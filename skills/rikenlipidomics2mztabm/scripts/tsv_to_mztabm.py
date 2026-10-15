"""Convert RIKEN_LIPIDOMICS-format MSDIAL alignment TSVs to mzTab-M.

The script consumes the two-file split used in
https://github.com/kozo2/hupopsi-pymztabm-handson/tree/main/RIKEN_LIPIDOMICS:

* `*_forMTD.tsv` — a 9-row "metadata" table whose columns are the per-sample
  attributes that mzTab-M's metadata section needs (sample name in row 1,
  Public/Private flag, Category, Tissue/Species, Genotype/Background,
  Perturbation, Diet/Culture, Biological replicate, Technical replicate, Unit).
* `*_forSMLSMF.tsv` — the MSDIAL alignment export. The first column is a row
  number; columns 2..31 carry identification fields ("Alignment ID",
  "Average Rt(min)", "Adduct type", ...) and the trailing block (one column
  per sample, matching the names in the MTD TSV) carries peak heights.

The converter:
1. Parses both TSVs into row lists.
2. Builds an in-memory `MzTabM` object (Metadata + SML + SMF + SME) using the
   `pymztab-m` model classes — every required-field rule is encoded in the
   pydantic schema, so building through the model is much safer than
   hand-authoring TSV.
3. Runs `MzTabM.validate(...)` and aborts (exit 1) on any ERROR-level message.
4. Writes the result (TSV by default; JSON or YAML on request).

Usage:
    python tsv_to_mztabm.py MTD.tsv SMLSMF.tsv OUT.mztab \\
        [--metadata META.json] [--format tsv|json|yaml] [--include-blank]

The optional META.json overrides the default study-level metadata
(mzTab-ID, title, contacts, instrument CV terms, ms_run file locations,
publication, software version, scan polarity, ...). See
``scripts/example_metadata.json`` for the schema.

Exit code 0 means the file was written and validation reported zero ERROR
messages. WARNINGs (e.g. unreferenced study_variable, recommended-but-missing
``best_id_confidence_value``) are tolerated.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import mztab_m_io as mztabm
from mztab_m_io.model.common import (
    CV,
    Assay,
    Contact,
    Database,
    Instrument,
    MsRun,
    Parameter,
    Publication,
    PublicationItem,
    Sample,
    Software,
    SpectraRef,
    StudyVariable,
)
from mztab_m_io.model.mztabm import MzTabM
from mztab_m_io.model.section.mtd import Metadata
from mztab_m_io.model.section.sme import SmallMoleculeEvidence
from mztab_m_io.model.section.smf import SmallMoleculeFeature
from mztab_m_io.model.section.sml import SmallMoleculeSummary
from mztab_m_io.model.validation import MessageType, ValidationContext


# -----------------------------------------------------------------------------
# TSV reading
# -----------------------------------------------------------------------------


def _read_tsv(path: Path) -> List[List[str]]:
    with path.open(newline="") as f:
        # quoting=QUOTE_NONE because MSDIAL exports raw text (with embedded ",").
        return [row for row in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)]


# -----------------------------------------------------------------------------
# MTD TSV layout
# -----------------------------------------------------------------------------
#
# The MTD TSV has 9 rows. Column 0 carries the attribute label (blank in row 0
# because it is the header row); columns 1.. carry one value per sample.
#
#   row 0 (cells 1..N)   sample names (one per ms_run)
#   row 1                Public/Private
#   row 2                Category (Mouse/Human/Blank/...)
#   row 3                Tissue/Species
#   row 4                Genotype/Background
#   row 5                Perturbation
#   row 6                Diet/Culture
#   row 7                Biological replicate
#   row 8                Technical replicate
#   row 9                Unit
#
# Sample columns in the SML/SMF TSV are matched by the sample names from row 0.

MTD_LABELS = {
    "public_private": "Public/Private",
    "category": "Category",
    "tissue": "Tissue/Species",
    "genotype": "Genotype/Background",
    "perturbation": "Perturbation",
    "diet": "Diet/Culture",
    "bio_replicate": "Biological replicate",
    "tech_replicate": "Technical replicate",
    "unit": "Unit",
}


def _label_row_index(rows: List[List[str]], label: str) -> int:
    """Find the row whose cell[0] equals `label` (case-insensitive)."""
    target = label.strip().lower()
    for i, row in enumerate(rows):
        if row and row[0].strip().lower() == target:
            return i
    raise KeyError(f"label '{label}' not found in MTD TSV")


def parse_mtd_tsv(rows: List[List[str]]) -> List[Dict[str, str]]:
    """Return one dict per sample column with all per-sample attributes."""
    if not rows:
        raise ValueError("MTD TSV is empty")
    # Sample names live in row 0, columns 1..N (cell[0] of row 0 is empty).
    name_row = rows[0]
    sample_cols = list(range(1, len(name_row)))
    samples: List[Dict[str, str]] = []
    label_index = {key: _label_row_index(rows, lbl) for key, lbl in MTD_LABELS.items()}
    for col in sample_cols:
        name = name_row[col].strip() if col < len(name_row) else ""
        if not name:
            continue
        info: Dict[str, Any] = {"name": name, "col": col}
        for key, idx in label_index.items():
            info[key] = rows[idx][col].strip() if col < len(rows[idx]) else ""
        samples.append(info)
    return samples


# -----------------------------------------------------------------------------
# Adduct normalisation
# -----------------------------------------------------------------------------

_ADDUCT_RE = re.compile(r"^\[(\d*)M((?:[+-][\w\d]+)*)\](\d*)([+-])$")


def normalise_adduct(s: Optional[str]) -> Optional[str]:
    """MSDIAL writes ``[M-H]-``; mzTab-M wants the explicit charge digit."""
    if not s:
        return None
    s = s.strip()
    m = _ADDUCT_RE.match(s)
    if not m:
        return None
    pre, body, charge, sign = m.groups()
    if not charge:
        charge = "1"
    return f"[{pre}M{body}]{charge}{sign}"


# -----------------------------------------------------------------------------
# Default metadata
# -----------------------------------------------------------------------------

DEFAULT_METADATA: Dict[str, Any] = {
    "mztab_id": "RIKEN-LIPIDOMICS-001",
    "title": "RIKEN lipidomics dataset",
    "description": "Lipidomics MSDIAL alignment results converted to mzTab-M.",
    "quantification_method": {
        "cv_label": "MS",
        "cv_accession": "MS:1001834",
        "name": "LC-MS label-free quantitation analysis",
    },
    "small_molecule_quantification_unit": {
        "cv_label": "MS",
        "cv_accession": "MS:1002857",
        "name": "isotopologue peak intensity",
    },
    "small_molecule_feature_quantification_unit": {
        "cv_label": "MS",
        "cv_accession": "MS:1002857",
        "name": "isotopologue peak intensity",
    },
    "small_molecule_identification_reliability": {
        "cv_label": "MS",
        "cv_accession": "MS:1002896",
        "name": "compound identification confidence level",
    },
    "id_confidence_measure": [
        {"cv_label": "MS", "cv_accession": "MS:1002890", "name": "fragmentation score"},
    ],
    "software": [
        {
            "cv_label": "MS",
            "cv_accession": "MS:1003082",
            "name": "MS-DIAL",
            "value": "4",
        }
    ],
    "instrument": [
        {
            "name": {
                "cv_label": "MS",
                "cv_accession": "MS:1000483",
                "name": "Thermo Fisher Scientific instrument model",
            },
            "source": {
                "cv_label": "MS",
                "cv_accession": "MS:1000073",
                "name": "electrospray ionization",
            },
            "analyzer": [
                {"cv_label": "MS", "cv_accession": "MS:1000484", "name": "orbitrap"}
            ],
            "detector": {
                "cv_label": "MS",
                "cv_accession": "MS:1000624",
                "name": "inductive detector",
            },
        }
    ],
    "database": [
        {
            "param": {
                "cv_label": "MS",
                "cv_accession": "MS:1002012",
                "name": "LIPID MAPS",
            },
            "prefix": "LM",
            "version": "Unknown",
            "uri": "https://www.lipidmaps.org/",
        }
    ],
    "cv": [
        {
            "label": "MS",
            "full_name": "PSI-MS controlled vocabulary",
            "version": "4.1.138",
            "uri": "https://raw.githubusercontent.com/HUPO-PSI/psi-ms-CV/master/psi-ms.obo",
        }
    ],
    "ms_run_format": {
        "cv_label": "MS",
        "cv_accession": "MS:1000584",
        "name": "mzML file",
    },
    "ms_run_id_format": {
        "cv_label": "MS",
        "cv_accession": "MS:1001530",
        "name": "mzML unique identifier",
    },
    "ms_run_scan_polarity": [
        {"cv_label": "MS", "cv_accession": "MS:1000130", "name": "positive scan"}
    ],
    "ms_run_location_template": "file:///data/{name}.mzML",
}


def _merge(base: Dict[str, Any], override: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not override:
        return base
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _param(d: Optional[Dict[str, Any]], pid: Optional[int] = None) -> Optional[Parameter]:
    if not d:
        return None
    return Parameter(
        id=pid,
        cv_label=d.get("cv_label", ""),
        cv_accession=d.get("cv_accession", ""),
        name=d.get("name", ""),
        value=d.get("value", ""),
    )


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _f(v: Any) -> Optional[float]:
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower() == "null":
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    if math.isnan(f):
        return None
    return f


def _str(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower() == "null":
        return None
    return s


# -----------------------------------------------------------------------------
# Main builder
# -----------------------------------------------------------------------------


def build_mztabm(
    mtd_rows: List[List[str]],
    smlsmf_rows: List[List[str]],
    meta_override: Optional[Dict[str, Any]] = None,
    include_blank: bool = False,
) -> MzTabM:
    meta = _merge(DEFAULT_METADATA, meta_override)
    samples_info = parse_mtd_tsv(mtd_rows)
    if not include_blank:
        samples_info = [
            s for s in samples_info if s.get("category", "").lower() != "blank"
        ]
    if not samples_info:
        raise ValueError("No sample columns found in MTD TSV.")

    # ------------------------------------------------------------------ MTD
    instruments: List[Instrument] = []
    for i, ib in enumerate(meta.get("instrument") or [], start=1):
        analyzers = [
            _param(p, pid=ai + 1) for ai, p in enumerate(ib.get("analyzer") or [])
        ]
        instruments.append(
            Instrument(
                id=i,
                name=_param(ib.get("name")),
                source=_param(ib.get("source")),
                analyzer=[a for a in analyzers if a is not None] or None,
                detector=_param(ib.get("detector")),
            )
        )
    instrument_ref = 1 if instruments else None

    fmt_param = _param(meta.get("ms_run_format"))
    idfmt_param = _param(meta.get("ms_run_id_format"))
    polarity_params = [
        _param(p, pid=i + 1)
        for i, p in enumerate(meta.get("ms_run_scan_polarity") or [])
    ]
    location_template = meta.get(
        "ms_run_location_template", "file:///data/{name}.mzML"
    )

    samples: List[Sample] = []
    ms_runs: List[MsRun] = []
    assays: List[Assay] = []
    sv_to_assays: Dict[str, List[int]] = {}
    name_to_assay: Dict[str, int] = {}

    for assay_id, info in enumerate(samples_info, start=1):
        run_name = info["name"]
        category = info.get("category") or "unknown"
        tissue_label = info.get("tissue") or "unknown"
        genotype = info.get("genotype") or "unknown"
        biorep = info.get("bio_replicate") or ""

        samples.append(
            Sample(
                id=assay_id,
                name=run_name,
                description=(
                    f"{category} {tissue_label} {genotype} "
                    f"biorep {biorep}".strip()
                ),
            )
        )
        ms_runs.append(
            MsRun(
                id=assay_id,
                name=run_name,
                location=location_template.format(name=run_name),
                format=fmt_param,
                id_format=idfmt_param,
                scan_polarity=[p for p in polarity_params if p is not None] or None,
                instrument_ref=instrument_ref,
            )
        )
        assays.append(
            Assay(
                id=assay_id,
                name=run_name,
                sample_ref=assay_id,
                ms_run_ref=[assay_id],
            )
        )
        name_to_assay[run_name] = assay_id
        # Group assays into study variables by Genotype/Background, then
        # falling back to Category. This means biological replicates that
        # share a genotype end up in the same study variable.
        sv_key = genotype if genotype != "unknown" else category
        sv_to_assays.setdefault(sv_key, []).append(assay_id)

    study_variables: List[StudyVariable] = []
    for sv_id, (sv_name, assay_ids) in enumerate(sv_to_assays.items(), start=1):
        study_variables.append(
            StudyVariable(
                id=sv_id,
                name=sv_name,
                description=f"Group: {sv_name}",
                assay_refs=sorted(assay_ids),
                # Provide one factor — the validator does not require it but it
                # makes the file self-describing.
                factors=[
                    Parameter(
                        id=1,
                        cv_label="EFO",
                        cv_accession="EFO:0001461",
                        name="genotype",
                        value=sv_name,
                    )
                ],
            )
        )

    contacts: Optional[List[Contact]] = None
    if meta.get("contact"):
        contacts = [
            Contact(
                id=i + 1,
                name=c.get("name"),
                affiliation=c.get("affiliation"),
                email=c.get("email"),
                orcid=c.get("orcid"),
            )
            for i, c in enumerate(meta["contact"])
        ]

    publications: Optional[List[Publication]] = None
    if meta.get("publication"):
        publications = []
        for i, entry in enumerate(meta["publication"]):
            items: List[PublicationItem] = []
            iterable = entry if isinstance(entry, list) else [entry]
            for item in iterable:
                if isinstance(item, str) and ":" in item:
                    typ, acc = item.split(":", 1)
                    items.append(
                        PublicationItem(type=typ.strip(), accession=acc.strip())
                    )
                elif isinstance(item, dict):
                    items.append(PublicationItem(**item))
            if items:
                publications.append(Publication(id=i + 1, publication_items=items))

    cvs = [
        CV(
            id=i + 1,
            label=c["label"],
            full_name=c.get("full_name", c["label"]),
            version=c.get("version", "Unknown"),
            uri=c.get("uri", ""),
        )
        for i, c in enumerate(meta["cv"])
    ]
    databases = [
        Database(
            id=i + 1,
            param=_param(d["param"]),
            prefix=d.get("prefix", ""),
            version=d.get("version", "Unknown"),
            uri=d.get("uri", ""),
        )
        for i, d in enumerate(meta["database"])
    ]
    softwares = [
        Software(id=i + 1, parameter=_param(s)) for i, s in enumerate(meta["software"])
    ]
    id_confidence_measures = [
        _param(p, pid=i + 1) for i, p in enumerate(meta["id_confidence_measure"])
    ]

    mtd = Metadata(
        mztab_version="2.0.0-M",
        mztab_id=meta["mztab_id"],
        title=meta.get("title"),
        description=meta.get("description"),
        contact=contacts,
        publication=publications,
        instrument=instruments or None,
        software=softwares,
        ms_run=ms_runs,
        sample=samples,
        assay=assays,
        study_variable=study_variables,
        cv=cvs,
        database=databases,
        quantification_method=_param(meta["quantification_method"]),
        small_molecule_quantification_unit=_param(
            meta["small_molecule_quantification_unit"]
        ),
        small_molecule_feature_quantification_unit=_param(
            meta["small_molecule_feature_quantification_unit"]
        ),
        small_molecule_identification_reliability=_param(
            meta["small_molecule_identification_reliability"]
        ),
        id_confidence_measure=id_confidence_measures,
    )

    # ----------------------------------------------------------- SML/SMF/SME
    if not smlsmf_rows:
        raise ValueError("SMLSMF TSV is empty")

    header = smlsmf_rows[0]
    # Build a {column-name → header-index} map. The SMLSMF TSV has
    # 'Alignment ID' as its very first column, then the rest of the MSDIAL
    # alignment fields, then one column per sample matching the names in the
    # MTD TSV.
    col_idx: Dict[str, int] = {}
    for i, h in enumerate(header):
        if h is None:
            continue
        col_idx[str(h).strip()] = i

    def col(row: List[str], name: str) -> Optional[str]:
        i = col_idx.get(name)
        if i is None or i >= len(row):
            return None
        return row[i]

    # Sample (abundance) column indexes — those whose header matches a sample
    # name in the MTD TSV. They appear in the order the user listed samples.
    sample_col_indexes: List[int] = []
    for s in samples_info:
        i = col_idx.get(s["name"])
        if i is None:
            raise ValueError(
                f"Sample '{s['name']}' from MTD TSV is missing from SMLSMF header"
            )
        sample_col_indexes.append(i)

    db_prefix = databases[0].prefix if databases else "null"

    sml_list: List[SmallMoleculeSummary] = []
    smf_list: List[SmallMoleculeFeature] = []
    sme_list: List[SmallMoleculeEvidence] = []

    # For each SML row we report `abundance_study_variable` as the mean across
    # the assays in that study variable. The cross-check validator considers a
    # study_variable "referenced" iff this list is at least as long as the SV
    # index — emitting it (even as a list of None) silences the
    # `study_variable[i] is not referenced` warning.
    sv_assay_indexes: List[List[int]] = []
    for sv in study_variables:
        # SV.assay_refs are 1-based assay ids; sample_col_indexes is 0-based by
        # assay order, so subtract 1 to align them.
        sv_assay_indexes.append(
            [aid - 1 for aid in (sv.assay_refs or []) if 1 <= aid <= len(sample_col_indexes)]
        )

    def _study_variable_means(values: List[Optional[float]]) -> List[Optional[float]]:
        out: List[Optional[float]] = []
        for assay_idxs in sv_assay_indexes:
            vals = [values[i] for i in assay_idxs if values[i] is not None]
            out.append(sum(vals) / len(vals) if vals else None)
        return out

    next_id = 1
    for r in smlsmf_rows[1:]:
        # Skip empty rows
        if not r or all((c is None or str(c).strip() == "") for c in r):
            continue
        if not _str(col(r, "Alignment ID")) and not _str(col(r, "Metabolite name")):
            continue

        name = _str(col(r, "Metabolite name"))
        formula = _str(col(r, "Formula"))
        smiles = _str(col(r, "SMILES"))
        ontology = _str(col(r, "Ontology"))
        adduct = normalise_adduct(_str(col(r, "Adduct type")))
        rt_min = _f(col(r, "Average Rt(min)"))
        rt_sec = rt_min * 60.0 if rt_min is not None else None
        mz = _f(col(r, "Average Mz"))
        score = _f(col(r, "Total score"))
        ref_mz = _f(col(r, "Reference m/z"))
        spec_file = _str(col(r, "Spectrum reference file name"))
        align_id = _str(col(r, "Alignment ID"))

        # SMF requires exp_mass_to_charge and charge — skip features without
        # an m/z (otherwise the validator emits ERROR).
        if mz is None:
            continue

        abundances: List[Optional[float]] = []
        for ci in sample_col_indexes:
            abundances.append(_f(r[ci]) if ci < len(r) else None)

        sml = SmallMoleculeSummary(
            sml_id=next_id,
            smf_id_refs=[next_id],
            chemical_name=[name] if name else None,
            chemical_formula=[formula] if formula else None,
            smiles=[smiles] if smiles else None,
            adduct_ions=[adduct] if adduct else None,
            database_identifier=[f"{db_prefix}:null"] if db_prefix else ["null"],
            best_id_confidence_measure=id_confidence_measures[0]
            if id_confidence_measures
            else None,
            best_id_confidence_value=score if score is not None else 0.0,
            reliability="3",
            abundance_assay=abundances,
            abundance_study_variable=_study_variable_means(abundances),
            # Provide a parallel list (one entry per SV) so the table writer
            # emits a matching header column for the variation column group.
            abundance_variation_study_variable=[None] * len(study_variables),
        )
        sml_list.append(sml)

        smf = SmallMoleculeFeature(
            smf_id=next_id,
            sme_id_refs=[next_id],
            adduct_ion=adduct,
            exp_mass_to_charge=mz,
            charge=1,
            retention_time_in_seconds=rt_sec,
            abundance_assay=abundances,
        )
        smf_list.append(smf)

        # spectra_ref must point to a real ms_run id. If MSDIAL named
        # the spectrum-reference file, try to match it to one of the ms_run
        # names; otherwise default to ms_run[1].
        sref_run_id = 1
        sref_text = "index=null"
        if spec_file:
            for run_name, run_id in name_to_assay.items():
                if run_name in spec_file:
                    sref_run_id = run_id
                    break
            sref_text = f"file={spec_file}"
        spectra_ref = SpectraRef(ms_run=sref_run_id, reference=sref_text)

        # database_identifier on SME is a single string, not a list.
        sme = SmallMoleculeEvidence(
            sme_id=next_id,
            evidence_input_id=align_id or str(next_id),
            database_identifier=f"{db_prefix}:null" if db_prefix else "null",
            chemical_formula=formula,
            smiles=smiles,
            chemical_name=name,
            adduct_ion=adduct,
            exp_mass_to_charge=mz,
            charge=1,
            theoretical_mass_to_charge=ref_mz if ref_mz is not None else mz,
            spectra_ref=[spectra_ref],
            identification_method=Parameter(
                cv_label="MS",
                cv_accession="MS:1001582",
                name="accurate mass",
            ),
            ms_level=Parameter(
                cv_label="MS",
                cv_accession="MS:1000511",
                name="ms level",
                value="2",
            ),
            id_confidence_measure=[score] if score is not None else None,
            rank=1,
        )
        sme_list.append(sme)

        next_id += 1

    if not sml_list:
        raise ValueError("No usable feature rows found in SMLSMF TSV.")

    return MzTabM(
        metadata=mtd,
        small_molecule_summary=sml_list,
        small_molecule_feature=smf_list,
        small_molecule_evidence=sme_list,
    )


# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------


def validate_inmemory(m: MzTabM) -> Tuple[List[Any], List[Any]]:
    """Run the in-memory validator and partition messages by severity."""
    ctx = ValidationContext(messages=[], source_format="json")
    m.validate(ctx)
    errs = [x for x in ctx.messages if x.message_type == MessageType.ERROR]
    warns = [x for x in ctx.messages if x.message_type == MessageType.WARNING]
    return errs, warns


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mtd", help="*_forMTD.tsv (per-sample metadata)")
    p.add_argument("smlsmf", help="*_forSMLSMF.tsv (MSDIAL alignment export)")
    p.add_argument("output", help="Output mzTab-M file path")
    p.add_argument("--metadata", help="Optional JSON metadata override file")
    p.add_argument("--format", choices=["tsv", "json", "yaml"], default="tsv")
    p.add_argument(
        "--include-blank",
        action="store_true",
        help="Keep columns whose Category == 'Blank' as samples",
    )
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    mtd_rows = _read_tsv(Path(args.mtd))
    smlsmf_rows = _read_tsv(Path(args.smlsmf))

    meta_override: Optional[Dict[str, Any]] = None
    if args.metadata:
        meta_override = json.loads(Path(args.metadata).read_text())

    m = build_mztabm(
        mtd_rows,
        smlsmf_rows,
        meta_override=meta_override,
        include_blank=args.include_blank,
    )
    errs, warns = validate_inmemory(m)
    mztabm.write(m, args.output, format=args.format)

    if not args.quiet:
        print(
            f"Wrote {args.output} (validation: {len(errs)} errors, "
            f"{len(warns)} warnings)"
        )
        for e in errs:
            print("  ERROR:", e.message)
        for w in warns[:10]:
            print("  WARN: ", w.message)
        if len(warns) > 10:
            print(f"  (...{len(warns) - 10} more warnings)")
    return 0 if not errs else 1


if __name__ == "__main__":
    sys.exit(main())
