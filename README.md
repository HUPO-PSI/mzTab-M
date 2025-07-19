# mzTab-M
Development of the mzTab-M standard data form

This repository contains GitHub Actions workflows to validate mzTab-M files using the official [jmzTab-m](https://github.com/lifs-tools/jmzTab-m) validator.

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
