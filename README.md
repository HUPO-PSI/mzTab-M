# mzTab-M

## *Reporting MS-based Quantitative and Qualitative Metabolomics Results*

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

### 🔧 Current Version 2.1.0 (in development, 2025):

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
    but version 4 is no longer maintained. Both versions 4 and 5 provide GUI and
    [console editions](https://systemsomicslab.github.io/compms/msdial/consoleapp.html),
    and the latest GUI editions of both versions support mzTab-M export.
    However, the console edition of version 4 does not support mzTab-M export,
    and the console edition of version 5 is still
    [incomplete](https://github.com/systemsomicslab/MsdialWorkbench/issues/658).
    ([Examples](../../wiki/Examples))
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
