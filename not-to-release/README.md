# ERC-MiDRASH UD Hebrew-PostRab Utilities

This folder contains utility scripts for processing and managing CoNLL-U formatted files for the Hebrew-PostRab Universal Dependencies treebank. These scripts are used internally by the annotation team but are not part of the final release.

## Scripts Overview

### `convert_from_gsheet_tsv.py` (not yet implemented)

Script for converting TSV files generated from the tagging staff's internal spreadsheet into proper CoNLL-U format. This utility streamlines the workflow from Google Sheets-based annotation to the standard CoNLL-U format required for the Universal Dependencies corpus. It integrates functionality from both the CoNLL-U fixer and validation scripts for a seamless conversion process.

Usage:

```
python convert_from_gsheet_tsv.py -i input_file -o output_file [-l log_file]
```

### `replace_literal_unicode.py`

Converts the output of the UD validation script (see [below](#helpful-links)) from literal Unicode escape sequences (like `\u05D0`) into readable Hebrew characters. This is useful when debugging output that contains Unicode escape sequences instead of actual Hebrew characters.

Usage:

```
python replace_literal_unicode.py input_file output_file
```

### `run_through_conllu.py`

Performs a basic first-pass validation of CoNLL-U files using the Python CoNLL-U parsing library. This script checks for syntax errors and other issues in the CoNLL-U format, logging any errors it encounters. It returns an exit code of 0 if processing completed without errors, and a non-zero exit code if any errors were encountered, making it suitable for integration into automated pipelines.

Usage:

```
python run_through_conllu.py -i input_file
```

### CoNNLU-Fixing Directory

Contains scripts and tests for converting the annotation staff's internal token-ID labeling system into proper CoNLL-U format. This is particularly important when correcting segmentation issues.

#### `conllu_fixer2.py`

This script processes CoNLL-U files to fix token IDs and ranges based on plus notation. It handles:

1. Plus notation for token splitting (e.g., 10+1, 10+2)
2. Skipped IDs for token unification
3. Range adjustments for multi-word tokens

The script returns an exit code of 0 if processing completed without errors, and a non-zero exit code if any errors were encountered, making it suitable for integration into automated pipelines.

Usage:

```
python conllu_fixer2.py -i input_file -o output_file [-l log_file]
```

## Development Notes

These scripts are part of the ERC-MiDRASH project's internal workflow for creating and maintaining the UD Hebrew-PostRab treebank. They are not intended for release as part of the final treebank but are maintained here for documentation and development purposes.

## Helpful Links

- [Link-tree for contributing to UD resources](https://universaldependencies.org/contributing/index.html), most notably including:
  - UD corpus [release checklist and guidelines](https://universaldependencies.org/contributing/repository_files.html).
  - [Validation guidelines](https://universaldependencies.org/contributing/validation.html) and [validation script repo](https://github.com/UniversalDependencies/tools).
