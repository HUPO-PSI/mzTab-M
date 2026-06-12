# mzTab-M for Metabolomics

## *Reporting MS-based Quantitative and Qualitative Results for Small Molecules*

[![mzTab-M 2.0 Spec Build
Workflow](https://github.com/HUPO-PSI/mzTab-M/actions/workflows/ci.yml/badge.svg)](https://github.com/HUPO-PSI/mzTab-M/actions/workflows/ci.yml)
[![mzTab-M 2.0 Example File Validation
Workflow](https://github.com/HUPO-PSI/mzTab-M/actions/workflows/validate-mztab-stable.yml/badge.svg)](https://github.com/HUPO-PSI/mzTab-M/actions/workflows/validate-mztab-stable.yml)
[![mzTab-M 2.x Example File Validation
Workflow](https://github.com/HUPO-PSI/mzTab-M/actions/workflows/validate-mztab-snapshot.yml/badge.svg)](https://github.com/HUPO-PSI/mzTab-M/actions/workflows/validate-mztab-snapshot.yml)

--------------------------------------------------------------------------------

## General

**mzTab-M** is a lightweight, tab-delimited file format for reporting **mass
spectrometry-based metabolomics** results. Initially an extension of mzTab for
proteomics (version 1.0), mzTab-M has evolved significantly in version **2.0**
and beyond, supporting detailed **quantitative** and **qualitative** data
reporting for metabolomics workflows. With version 2.1, we intend to expand the
format, to modularize it and support **FAIR** data use cases and integrate
better with tools.

> The **mzTab-M 2.1+** development now takes place in this repository (split
> from the [original mzTab repository](https://github.com/HUPO-PSI/mzTab)).

--------------------------------------------------------------------------------

## Who Should Use mzTab-M?

mzTab-M is designed for a wide range of users, including **bioinformaticians**,
but also researchers outside of metabolomics, such as **systems biologists**.
Its goal is to provide a lightweight, easy-to-parse file format that presents
the **results** of mass spectrometry experiments in a **clear and accessible**
way.

A key design principle is usability: even a non-expert should be able to open an
mzTab-M file in Excel and intuitively understand the data. At the same time, the
format supports **machine-readability** and links to controlled vocabularies and
ontologies, making it highly suitable for AI/ML applications.

As MS-based methods and data volumes grow more complex, mzTab-M continues to
evolve to keep pace. In version **2.1.0**, the format is being extended to:

-   Support **intermediate analysis outputs**
-   Enable **submission-ready exports** to repositories like **MetaboLights**
    and **Metabolomics Workbench**
-   Integrate more effectively with a growing ecosystem of tools

--------------------------------------------------------------------------------

## Join the Community

📬 **Want to contribute or stay updated?**\
Join our working group via the [mzTab-M mailing
list](https://lists.cebitec.uni-bielefeld.de/mailman3/postorius/lists/mztabm.cebitec.uni-bielefeld.de/)

--------------------------------------------------------------------------------

## Specifications of mztab-M

### 🔧 Current Version 2.1.0 (in development, 2026):

-   **Specification**:\
    [AsciiDoc](https://github.com/HUPO-PSI/mzTab-M/blob/main/specification_documents/mzTab_format_specification_2_1-M.adoc)

-   **Example files**:\
    [GitHub Examples](https://github.com/HUPO-PSI/mzTab-M/tree/main/examples)

-   **Reference Implementation & Validator**:\
    [jmzTab-m (Java)](https://github.com/lifs-tools/jmzTab-m) to read, write and
    validate **mzTab-M 2.X.+**)\
    [jmzTab-m BioConda Package (and Docker container)](https://bioconda.github.io/recipes/jmztab-m/README.html)

-   **CI Validation Workflow**:\
    [GitHub Actions YAML](.github/workflows/validate-mztab.yml), using the
    aforementioned validator.

-   **R Ecosystem Validator**:\
    [reading-mzTab-into-R](https://github.com/michbur/reading-mzTab-into-R/)

-   **Online Validator App**:\
    [jmzTab-m Web Validator](https://github.com/lifs-tools/jmzTab-m-webapp)

-   **More Information on the object**: [jmzTab-m project
    README](https://github.com/lifs-tools/jmzTab-M) and the [Maven
    site](https://lifs-tools.github.io/jmzTab-m/) for an introduction to the
    object model, creation of custom mzTab-M files and mzTab-M validation.

**Version 2.0.0 for Metabolomics (March 2019):**

-   **Repository**: [Original repo](https://github.com/HUPO-PSI/mzTab)

-   **Specification Docs**:\
    [AsciiDoc](https://github.com/HUPO-PSI/mzTab/blob/master/specification_document-releases/2_0-Metabolomics-Release/mzTab_format_specification_2_0-M_release.adoc)
    \|\
    [PDF](http://hupo-psi.github.io/mzTab/2_0-metabolomics-release/mzTab_format_specification_2_0-M_release.pdf)
    \|\
    [HTML](http://hupo-psi.github.io/mzTab/2_0-metabolomics-release/mzTab_format_specification_2_0-M_release.html)

-   **Examples**: [Wiki](../../wiki/Examples) \| [GitHub
    Examples](https://github.com/HUPO-PSI/mzTab/tree/master/examples/2_0-Metabolomics_Release)

-   **Validator & Reference Tool**: [jmzTab-m
    (Java)](https://github.com/lifs-tools/jmzTab-m)

> If you want information regarding prior version of this format, please check
> [the mzTab 1.0 repository](https://github.com/HUPO-PSI/mzTab)

--------------------------------------------------------------------------------

## Current Activities and Software Support

### ✅ mzTab-M 2.0 Supported By

-   [Lipid Data Analyzer 2
    (LDA2)](http://genome.tugraz.at/lda2/lda_description.shtml) has support for
    mzTab-M as output ([Examples](../../wiki/Examples)).
-   [GNPS](https://gnps.ucsd.edu/ProteoSAFe/static/gnps-splash.jsp) can import
    mzTab-M since late 2019.
-   [MS-Dial](https://systemsomicslab.github.io/compms/msdial/main.html) has
    support for mzTab-M as output. MS-DIAL has two major versions, 4 and 5,
    but version 4 is no longer maintained. Anyone can easily produce mzTab-M using MS-DIAL5 console app by referring to the [MS-DIAL 5 console app tutorial](https://systemsomicslab.github.io/msdial5tutorial/consoleapp.html).
    The linked tutorial page describes how to automatically generate an mzTab-M file containing chemical name assignments in SML table from example mzML files, using only command-line operations.
-   [MetaboAnalyst](https://www.metaboanalyst.ca/MetaboAnalyst/docs/Format.xhtml)
    can import mzTab-M since April 2020.
-   [jmzTab-M](https://github.com/lifs-tools/jmzTab-m) provides the reference
    implementation to read, write and validate mzTab-M 2.0.
-   [MzMine 3](https://mzmine.github.io) provides feature input and output
    support via mzTab-M, implemented during [GSoC
    2020](https://summerofcode.withgoogle.com/organizations).
-   [LipidXplorer 2](https://github.com/lifs-tools/lipidxplorer) provides
    preliminary mzTab-M output of identified and quantified lipid features.
-   [xcms](https://github.com/sneumann/xcms) has a prototype mzTab-M export.
-   [rmztab-m](https://github.com/lifs-tools/rmztabm) provides support in R for
    reading, writing and validation of mzTab-M files.

### 🛠 Active Development (2.1.0+)

-   Convertor from mzTab-M to ISA-tab format for MetaboLights submission can be found [here](https://github.com/EBI-Metabolights/mztabm2mtbls)
-   Work with the [Lipidomics Standards
    Initiative](https://lipidomics-standards-initiative.org/) to map the
    reporting checklist to mzTab-M metadata.
-   Semantic validation using [Custom mapping file for
    lipidomics](https://github.com/lipidomics-standards-initiative/).
-   Contributing and building the spec: please check [the README.adoc](specification_documents/README.adoc)    
-   **Help wanted**
    -   Add export of mzTab-M from Skyline.
    -   Finalize the [Python mzTab-M
        library](https://github.com/lifs-tools/pymzTab-m).

--------------------------------------------------------------------------------

## Citation

If you use **mzTab-M 2.0**, please cite:

> **Hoffmann et al.**, Analytical Chemistry, 2019\
> [DOI](https://pubs.acs.org/doi/10.1021/acs.analchem.8b04310) \|
> [PubMed](http://www.ncbi.nlm.nih.gov/pubmed/30688441)

If you use **jmzTab-m**, please cite:

> **Hoffmann et al.**, Analytical Chemistry, 2019 (Sep)\
> [DOI](https://pubs.acs.org/doi/10.1021/acs.analchem.9b01987) \|
> [PubMed](http://www.ncbi.nlm.nih.gov/pubmed/31525911)

--------------------------------------------------------------------------------

## Repository details for contributors

### JSON Schema - OpenAPI definition

The main specification for mzTab-M is maintained in the form of an OpenAPI 3.1.1
compatible YAML file `schema/mzTab_m_openapi.yml` You can edit, view and
validate this file using either the swagger web editor at
<https://editor-next.swagger.io/> or using the docker container (instructions at
<https://swagger.io/docs/open-source-tools/swagger-editor-next/#docker>):

```         
docker pull swaggerapi/swagger-editor:next-v5
docker run -d -p 8080:80 docker.swagger.io/swaggerapi/swagger-editor:next-v5
```

### CV Term Mapping File

mzTab-M supports semantic validation based on an XML mapping file. An example is
available in the `schema/mzTab_2_1-M_mapping.xml`

### Specification Document

The `specification_document` folder contains the latest version of the AsciiDoc
source for the mzTab-M specification document. It is built automatically and is
deployed in different formats to the mzTab-M documentation website.

### Validation

The repository includes example mzTab-M files in the `examples/` directory that
are automatically validated using GitHub Actions on every push and pull request.

If you had a new mztab-M example please follow the following naming convention: 
*softwareName_0.1.2_databaseID_optionalComment.mzTab*

### Example Files

-   `examples/MTBLS263.mztab` - A metabolomics dataset example
-   `examples/minimal-m-2.0.mztab` - A minimal mzTab-M file (demonstrates
    validation errors)

### Validation Workflow

The validation workflow:

1. Downloads the latest stable jmzTab-m CLI validator 
2. Validates all `.mztab` files in the repository 
3. Reports validation results with Info-level logging

The workflow uses the command mentioned in issue #4:

``` bash
java -jar jmztabm-cli-<VERSION>.jar -c examples/MTBLS263.mztab -l Info
```

--------------------------------------------------------------------------------

## Documentation Workflow

The Antora documentation site (`docs/mztabm/`) contains two auto-generated
partials that **must be regenerated and committed** whenever their sources
change:

| Partial | Source |
|---|---|
| `docs/mztabm/modules/developers/partials/mzTab_m_schema.adoc` | `schema/mzTab_2_1-M.json` |
| `docs/mztabm/modules/developers/partials/mzTab_format_specification.adoc` | `specification_documents/mzTab_format_specification_2_1-M.adoc` |

The helper script `gen-docs.sh` (repository root) automates both steps.

### 1 — Sync the AsciiDoc schema documentation after JSON schema changes

After editing `schema/mzTab_2_1-M.json` run:

``` bash
./gen-docs.sh --schema
```

After editing
`specification_documents/mzTab_format_specification_2_1-M.adoc` run:

``` bash
./gen-docs.sh --spec
```

To regenerate both at once:

``` bash
./gen-docs.sh
```

Then stage and commit the updated partials:

``` bash
git add docs/mztabm/modules/developers/partials/mzTab_m_schema.adoc \
        docs/mztabm/modules/developers/partials/mzTab_format_specification.adoc
git commit -m "docs: regenerate Antora partials"
git push
```

> **Prerequisite:** Python 3.8+ must be on `PATH`; no third-party packages are
> needed for the schema generator.

### 2 — Build and preview the site locally

[Docker](https://docs.docker.com/get-docker/) is required.

``` bash
# Build only
./build-site.sh

# Build and start a local HTTP preview at http://localhost:8080
./build-site.sh --serve

# Force reinstall of Node/Antora dependencies before building
./build-site.sh --clean --serve
```

The generated site is written to `build/site/`.

### 3 — Create a pre-release (development snapshot)

While the specification is still in progress, `docs/mztabm/antora.yml`
carries `prerelease: -dev`. To publish a dated snapshot:

1.  Regenerate the partials if needed (`./gen-docs.sh`).
2.  Commit and push your changes to `main`.
3.  On GitHub, go to **Releases → Draft a new release**.
4.  Choose a pre-release tag (e.g. `v2.1.0-beta.1`), check **Set as a
    pre-release**, and publish.

The release workflow will build and deploy the Antora site to GitHub Pages
with the tag name injected as `document-version`.

> The `prerelease: -dev` marker in `antora.yml` is kept on `main` so the
> in-development version is visually distinct in the site version selector.

### 4 — Create a full release with GitHub

Antora uses per-version documentation branches (e.g. `v2.1`) so that older
versions remain browsable on the published site alongside `main`
(development). The release workflow handles branch creation automatically.

#### Pre-release checklist

-   [ ] All issues and PRs for the milestone are merged to `main`.
-   [ ] Regenerate and commit the documentation partials (`./gen-docs.sh`).
-   [ ] Update `docs/mztabm/antora.yml`: set the final `version:` value and
        remove or comment out the `prerelease:` line.
-   [ ] Commit: `git commit -am "release: bump antora version to 2.1.0"`.
-   [ ] Push `main` and verify the CI build passes.

#### Tagging and publishing on GitHub

``` bash
# Tag the release commit
git tag -a v2.1.0 -m "mzTab-M 2.1.0 release"
git push origin v2.1.0
```

Then on GitHub:

1.  Go to **Releases → Draft a new release**.
2.  Select the tag `v2.1.0` you just pushed.
3.  Fill in the release title and changelog notes.
4.  Ensure **Set as the latest release** is checked (not pre-release).
5.  Click **Publish release**.

#### What the release workflow does automatically

When the release is published, `.github/workflows/release.yml`:

1.  Runs the CI build and example validation.
2.  Creates a documentation branch `v2.1` from the tagged commit, removes
    the `prerelease:` line from `docs/mztabm/antora.yml` on that branch,
    and pushes it to the repository.
3.  Builds the Antora site — the `v*` glob in `antora-playbook.yml`
    automatically includes `v2.1` alongside `main`, so both the new stable
    version and the ongoing development version appear in the version
    selector.
4.  Deploys the site to GitHub Pages.

#### After the release — start the next development cycle

Bump `main` to the next development version:

``` bash
# Edit docs/mztabm/antora.yml:
#   version: '2.1'   →  '2.2'
#   prerelease: -dev     (restore if it was removed before tagging)
git add docs/mztabm/antora.yml
git commit -m "chore: start 2.2 development cycle"
git push
```

> **GitHub Pages setup (one-time):** In the repository **Settings → Pages**,
> set the source to **GitHub Actions** (not the legacy branch-based deploy).
> This is required for the `deploy-pages` action in the release workflow.
