# mzTab-M
Development of the mzTab-M standard data form

This repository contains GitHub Actions workflows to validate mzTab-M files using the official [jmzTab-m](https://github.com/lifs-tools/jmzTab-m) validator.

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
