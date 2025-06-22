# Spreadsheet to CoNLL-U Conversion Process

This document details the conversion process implemented in the `convert_from_gsheet_tsv.py` script, which transforms the annotation team's Google Sheets TSV exports into properly formatted CoNLL-U files for the Hebrew-PostRab Universal Dependencies treebank.

The conversion process bridges the gap between the collaborative annotation environment (Google Sheets) and the standardized Universal Dependencies format, ensuring consistent and valid CoNLL-U output while preserving all linguistic annotations.

# Conversion steps

## File conversion

- If there is a header line (which may automatically be generated if it is downloaded as a TSV from Google Sheets), delete it.
- Linebreaks should be converted to LF if needed.
- The extension should be changed to CoNNL-U

## Checks

These are cases where the script should log an error:

- If the ID field of any row doesn't satisfy the regex `^\d+(?:\+\d+)?(?:-\d+(?:\+\d+)?)?$`.
- If there is an empty field not in one of the cases indicated in the [normalization](#normalization) section below.

## Normalization - per-line changes

These are changes that the script should make automatically:

- In the FORM column, any string consisting only and exactly of a single `ה` and at least one underscore character (in any order - meaning, `_+ה|ה_+|_+ה_+` in regex, but there should be a simple non-regex way to implement it) should be replaced by `ה_` (he followed by a single underscore).
- Ensure that in any row in which the FORM column has either `_של_` or `ה_`, the MISC column has `PhantomToken=Yes`.
- Remove any lines beginning with `# Included`.
- Remove any Unicode RTL (Right-to-Left) and LTR (Left-to-Right) marks from all fields (characters U+200E, U+200F, and similar directional control characters).
- Lines that are entirely whitespace should be made blank lines (but do not erase the line itself!).
- There should never be more than one consecutive blank line.
- Lines that begin with `#` should never contain a tab character. If there is one, erase it and everything that comes after it.
- Other non-empty lines - there should be exactly 10 tab separated fields, where only the MISC field is allowed to have a space char. In other words, each line (if it isn't empty or beginning with `#`) should match the regex `^(\S+\t){9}[\S ]+$`. If there is a tenth tab char, it and anything after it should be erased.
  - Note that there should never be two consecutive tab characters either - empty fields should be indicated by underscore. The script should make this replacement (`\t\t` -> `\t_\t`) automatically in the following cases:
    - In a range line (the first column, ID, satisfies regex `\d+-\d+`), for all fields other than ID and FORM.
    - In any line in the DEPS and MISC fields.
    - In any line in which the UPOS is not NOUN, VERB, ADJ, or PRON, in the FEATS field.
- Change all `nsubj:nsent` in the DEPREL column to `nsubj:cop`.
- If anything else in the DEPREL column ends with `:nsent`, remove it, and instead add `NSent=Yes` to the MISC column.

## Scripts to call at the end

After the [checks](#checks) and [normalization](#normalization---per-line-changes) has been implemented, and any header line has been deleted, the resulting file should be processed through these components (in this order). The other file-conversion steps can wait till after.

- The [CoNNL-U fixer](CoNNLU-Fixing\conllu_fixer2.py) functionality to handle plus notation and token IDs. Processing continues only if this step completes without errors.
- The [run-through-CoNNL-U](run_through_conllu.py) validation to verify the file is properly formatted according to the CoNLL-U standard.

The conversion script directly imports and calls these components rather than executing them as separate processes, which improves efficiency and error handling.

# Reference - CoNLL-U format

For reference, these are the CoNLL-U fields, in order:

- ID: Word index, integer starting at 1 for each new sentence; may be a range for multiword tokens; may be a decimal number for empty nodes (decimal numbers can be lower than 1 but must be greater than 0).
- FORM: Word form or punctuation symbol.
- LEMMA: Lemma or stem of word form.
- UPOS: Universal part-of-speech tag.
- XPOS: Optional language-specific (or treebank-specific) part-of-speech / morphological tag; underscore if not available.
- FEATS: List of morphological features from the universal feature inventory or from a defined language-specific extension; underscore if not available.
- HEAD: Head of the current word, which is either a value of ID or zero (0).
- DEPREL: Universal dependency relation to the HEAD (root iff HEAD = 0) or a defined language-specific subtype of one.
- DEPS: Enhanced dependency graph in the form of a list of head-deprel pairs.
- MISC: Any other annotation.

## A note about the MISC column

As in the FEATS column, the MISC field should ideally be composed of strings of the form `<key>=<value>`, separated by pipe chars and in alphabetical order if there is more than one. Therefore, "adding something to the MISC field" usually means replacing the underscore character with something, but if it is not empty, it means inserting the new pair in the proper alphabetical place and adding the necessary pipe char.
