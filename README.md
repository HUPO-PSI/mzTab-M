# mzTab-M
## _Reporting MS-based Quantitative and Qualitative Metabolomics Results_

[![mzTab-M 2.0 Spec Build Workflow](https://github.com/HUPO-PSI/mzTab-M/actions/workflows/ci.yml/badge.svg)](https://github.com/HUPO-PSI/mzTab-M/actions/workflows/ci.yml)
[![mzTab-M 2.0 Example File Validation Workflow](https://github.com/HUPO-PSI/mzTab-M/actions/workflows/validate-mztab.yml/badge.svg)](https://github.com/HUPO-PSI/mzTab-M/actions/workflows/validate-mztab.yml)

## General
mzTab has been designed to act as a lightweight, tab-delimited file format for mass spec-derived omics data. It was originally designed for proteomics with limited support for metabolomics (version 1.0). The metabolomics aspects have been further refined and extended in the mzTab-M 2.0 release. With version 2.1, we intend to expand the format, to modularize it and support FAIR data use cases and integrate better with tools.

**From mzTab-M 2.1 onwards, we have split the development from the [original GitHub repository](https://github.com/HUPO-PSI/mzTab), where both mzTab and mzTab-M were maintained together. The current repository is being used for mzTab-M 2.1.X and future versions.**

One of the main target audiences for this format are bioinformaticians, but also researchers outside of metabolomics, such as systems biologists. It should be easy to parse and only contain the minimal information required to evaluate the results of an experiment. One of the goals of this file format is that it, for example, should be possible for a biologist to open such a file in Excel and still be able to "see" the data. However, the volume and complexity of mass spectrometry data are increasing with new methods and technologies.

The aim of the format is to present the results of an experiment in a computationally accessible overview. The aim is to provide detailed evidence for these results, but necessarily the complete process leading to those results. Both of these functions are established through links to more detailed representations in other formats. For version 2.1.0, we intend to expand the format so that it can capture the necessary information to create submissions to repositories like MetaboLights or Metabolomics Workbench. 

**If you are interested in joining our working group, [please sign up for our mailing list](https://lists.cebitec.uni-bielefeld.de/mailman3/postorius/lists/mztabm.cebitec.uni-bielefeld.de/)**

When you use the mzTab-M format version 2.0, please cite the following publication:

  * **[N. Hoffmann et al., Analytical Chemistry 2019.](https://pubs.acs.org/doi/10.1021/acs.analchem.8b04310) [PubMed record](http://www.ncbi.nlm.nih.gov/pubmed/30688441).**

Please check the mzTab 1.0 repository for more information about prior versions: https://github.com/HUPO-PSI/mzTab

## Specifications

**Version 2.1.0 for Metabolomics (in development, 2025):**

  > Specification document ([adoc](https://github.com/HUPO-PSI/mzTab-M/blob/main/specification_documents/mzTab_format_specification_2_1-M.adoc))
  
  > Example Files ([Git](https://github.com/HUPO-PSI/mzTab-M/tree/main/examples))

  > Reference implementation and validator ([jmzTab-m](https://github.com/lifs-tools/jmzTab-m) to read, write and validate **mzTab-M 2.X.+**)

  > [GitHub Actions workflow](https://github.com/HUPO-PSI/mzTab-M/blob/main/.github/workflows/validate-mztab.yml) to validate mzTab-M files using the official [jmzTab-m](https://github.com/lifs-tools/jmzTab-m) validator.
  
  > Validator web application ([jmzTab-m web validator](https://github.com/lifs-tools/jmzTab-m-webapp) for **mzTab-M 2.X** and mzTab 1.0 (see below))
  
Please see the [jmzTab-m project README](https://github.com/lifs-tools/jmzTab-M) and the [Maven site](https://lifs-tools.github.io/jmzTab-m/) for an introduction to the object model, creation of custom mzTab-M files and mzTab-M validation. 

**Version 2.0.0 for Metabolomics (March 2019):**

Please note that development for mzTab-M 2.0.0 was performed in a different repository: https://github.com/HUPO-PSI/mzTab

  > Specification document ([adoc](https://github.com/HUPO-PSI/mzTab/blob/master/specification_document-releases/2_0-Metabolomics-Release/mzTab_format_specification_2_0-M_release.adoc), [html](http://hupo-psi.github.io/mzTab/2_0-metabolomics-release/mzTab_format_specification_2_0-M_release.html), [docx](http://hupo-psi.github.io/mzTab/2_0-metabolomics-release/mzTab_format_specification_2_0-M_release.docx), [PDF](http://hupo-psi.github.io/mzTab/2_0-metabolomics-release/mzTab_format_specification_2_0-M_release.pdf))
  
  > Example Files ([Wiki](../../wiki/Examples), [Git](https://github.com/HUPO-PSI/mzTab/tree/master/examples/2_0-Metabolomics_Release))

  > Reference implementation ([jmzTab-m](https://github.com/lifs-tools/jmzTab-m) to read, write and validate **mzTab-M 2.0.+**)
  
  > Validator web application ([jmzTab-m web validator](https://github.com/lifs-tools/jmzTab-m-webapp) for **mzTab-M 2.0** and mzTab 1.0 (see below))
  
Please see the [jmzTab-m project README](https://github.com/lifs-tools/jmzTab-M) and the [Maven site](https://lifs-tools.github.io/jmzTab-m/) for an introduction to the object model, creation of custom mzTab-M files and mzTab-M validation. 
  
When you use the jmzTab-m library, please cite the following publication:

* **[Nils Hoffmann et al., Analytical Chemistry 2019; Sep;](https://pubs.acs.org/doi/10.1021/acs.analchem.9b01987). [PDF File](). [PubMed record](http://www.ncbi.nlm.nih.gov/pubmed/31525911).**

---

## Current Activities and Software Support

**Version 2.1.0 for Metabolomics**

 * Work with the [Lipidomics Standards Initiative](https://lipidomics-standards-initiative.org/) to map the reporting checklist to mzTab-M metadata.
 * [Custom mapping file for semantic validation of mzTab-M for Lipidomics](https://github.com/lipidomics-standards-initiative/).

**Help wanted**

* Add export of mzTab-M from Skyline.
* Finalize the [Python mzTab-M library](https://github.com/lifs-tools/pymzTab-m).

**Software with support for mzTab-M 2.0**
 
 * [Lipid Data Analyzer 2 (LDA2)](http://genome.tugraz.at/lda2/lda_description.shtml) has support for mzTab-M as output ([Examples](../../wiki/Examples)).
 * [GNPS](https://gnps.ucsd.edu/ProteoSAFe/static/gnps-splash.jsp) can import mzTab-M since late 2019.
 * [MS-Dial](http://prime.psc.riken.jp/Metabolomics_Software/MS-DIAL/) has support for mzTab-M as output ([Examples](../../wiki/Examples)).
 * [MetaboAnalyst](https://www.metaboanalyst.ca/MetaboAnalyst/docs/Format.xhtml) can import mzTab-M since April 2020.
 * [jmzTab-M](https://github.com/lifs-tools/jmzTab-m) provides the reference implementation to read, write and validate mzTab-M 2.0.
 * [MzMine 3](https://mzmine.github.io) provides feature input and output support via mzTab-M, implemented during [GSoC 2020](https://summerofcode.withgoogle.com/organizations).
 * [LipidXplorer 2](https://github.com/lifs-tools/lipidxplorer) provides preliminary mzTab-M output of identified and quantified lipid features.
 * [XCMS](https://github.com/sneumann/xcms) has a prototype mzTab-M export.
 * [rmztab-m](https://github.com/lifs-tools/rmztabm) provides support in R for reading, writing and validation of mzTab-M files.

## Specification

### JSON Schema - OpenAPI definition

The main specification for mzTab-M is maintained in the form of an OpenAPI 3.1.1 compatible YAML file `schema/mzTab_m_openapi.yml`
You can edit, view and validate this file using either the swagger web editor at https://editor-next.swagger.io/ or using the docker container (instructions at https://swagger.io/docs/open-source-tools/swagger-editor-next/#docker):

```
docker pull swaggerapi/swagger-editor:next-v5
docker run -d -p 8080:80 docker.swagger.io/swaggerapi/swagger-editor:next-v5
```

### CV Term Mapping File

mzTab-M supports semantic validation based on an XML mapping file. An example is available in the `schema/mzTab_2_1-M_mapping.xml`

### Specification Document

The `specification_document` folder contains the latest version of the AsciiDoc source for the mzTab-M specification document. It is built automatically and is deployed in different formats to the mzTab-M documentation website.

## Validation

The repository includes example mzTab-M files in the `examples/` directory that are automatically validated using GitHub Actions on every push and pull request.

### Example Files

- `examples/MTBLS263.mztab` - A metabolomics dataset example
- `examples/minimal-m-2.0.mztab` - A minimal mzTab-M file (demonstrates validation errors)

### Validation Workflow

The validation workflow:
1. Downloads the latest stable jmzTab-m CLI validator
2. Validates all `.mztab` files in the repository 
3. Reports validation results with Info-level logging

The workflow uses the command mentioned in issue #4:
```bash
java -jar jmztabm-cli-<VERSION>.jar -c examples/MTBLS263.mztab -l Info
```
