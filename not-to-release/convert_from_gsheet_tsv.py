#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
import os
import logging
import sys
import tempfile
from pathlib import Path

# Import functions from other scripts
from run_through_conllu import validate_conllu_file
from CoNNLU_Fixing.conllu_fixer2 import process_conllu_file as fix_conllu_file

# Pre-compiled regex patterns for better performance
ID_PATTERN = re.compile(r'^\d+(?:\+\d+)?(?:-\d+(?:\+\d+)?)?$')
RANGE_PATTERN = re.compile(r'^\d+-\d+$')
HE_UNDERSCORE_PATTERN = re.compile(r'^[ה_]+$')

# Setup logging
logger = logging.getLogger(__name__)

def setup_logger(log_file=None):
    """Configure logging to file or console"""
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    if log_file:
        # Use 'w' mode and explicitly set encoding without BOM
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

def is_valid_id(id_str):
    """Check if ID field satisfies the required format"""
    return bool(ID_PATTERN.match(id_str))

def fix_phantom_tokens(form, misc):
    """Ensure phantom tokens have proper MISC field"""
    if form in ('_של_', 'ה_') and 'PhantomToken=Yes' not in misc:
        if misc == '_':
            return 'PhantomToken=Yes'
        else:
            # Add PhantomToken=Yes in alphabetical order
            features = misc.split('|')
            features.append('PhantomToken=Yes')
            features.sort()
            return '|'.join(features)
    return misc

def add_to_misc(misc, feature):
    """Add a feature to the MISC column in alphabetical order"""
    if misc == '_':
        return feature
    
    features = misc.split('|')
    features.append(feature)
    features.sort()
    return '|'.join(features)

def normalize_line(line):
    """Apply normalization rules to a single line"""
    if not line.strip():
        return '\n'  # Convert whitespace-only lines to blank lines
    
    if line.startswith('#'):
        if line.startswith('# Included'):
            return None  # Remove lines beginning with "# Included"
        
        return line.rstrip().split('\t')[0] + '\n'  # Strip trailing whitespace for comment lines, get rid of anything after first tab
    
    fields = line.strip().split('\t')
    
    # Ensure we have exactly 10 fields
    if len(fields) < 10:
        # Add missing fields as underscores
        fields.extend(['_'] * (10 - len(fields)))
    elif len(fields) > 10:
        # Truncate extra fields
        fields = fields[:10]
    
    # Check ID format
    if not is_valid_id(fields[0]):
        logger.error(f"Invalid ID format: {fields[0]} in line: {line.strip()}")
        return line  # Return original line for error reporting
    
    # Check that required fields are not empty
    required_fields = [0, 1]  # ID and FORM are always required
    for i in required_fields:
        if i < len(fields) and (not fields[i] or fields[i] == '_'):
            logger.error(f"Required field at position {i} is empty in line: {line.strip()}")
            if fields[i] == '':
                fields[i] = '_'  # Replace empty string with underscore for further processing
    
    # Check for other empty fields that should be underscores
    for i in range(2, len(fields)):
        if fields[i] == '':
            is_range = bool(RANGE_PATTERN.match(fields[0]))
            if (is_range) or \
               (i == 8 or i == 9) or \
               (i == 5 and fields[3] not in ('NOUN', 'VERB', 'ADJ', 'PRON')):
                fields[i] = '_'  # Valid cases for empty fields
            else:
                logger.error(f"Empty field at position {i} that should not be empty in line: {line.strip()}")
                fields[i] = '_'  # Replace with underscore but log the error
    
    # Fix he with underscores - look for any string with exactly one ה and at least one underscore
    if fields[1] and 'ה' in fields[1] and '_' in fields[1]:
        if HE_UNDERSCORE_PATTERN.match(fields[1]) and fields[1].count('ה') == 1:
            fields[1] = 'ה_'
    
    # Fix MISC field for phantom tokens
    fields[9] = fix_phantom_tokens(fields[1], fields[9])
    
    # Fix deprel fields
    if fields[7] == 'nsubj:nsent':
        fields[7] = 'nsubj:cop'
    elif fields[7].endswith(':nsent'):
        fields[7] = fields[7][:-6]  # Remove :nsent suffix
        fields[9] = add_to_misc(fields[9], 'NSent=Yes')
    
    return '\t'.join(fields) + '\n'

def normalize_file_content(content):
    """Apply all normalization rules to the file content"""
    content = content.replace("\u200f", "")  # Remove RTL marks
    content = content.replace("\u200e", "")  # Remove LTR marks
    lines = content.splitlines(True)  # Keep line endings
    
    # Remove header line if present
    if lines and not lines[0].startswith('#') and not is_valid_id(lines[0].split('\t')[0]):
        lines = lines[1:]
    
    normalized_lines = []
    prev_was_blank = False
    
    for line in lines:
        normalized = normalize_line(line)
        if normalized is None:  # Line was removed
            continue
            
        # Avoid consecutive blank lines
        is_blank = normalized == '\n'
        if is_blank and prev_was_blank:
            continue
            
        normalized_lines.append(normalized)
        prev_was_blank = is_blank
    
    return ''.join(normalized_lines)

def convert_file(input_file, output_file, log_file=None):
    """Convert Google Sheets TSV to CoNLL-U format"""
    try:
        # Read input file with explicit encoding
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Normalize content
        normalized_content = normalize_file_content(content)
        
        # Write to temporary file for processing
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.conllu', delete=False) as temp:
            temp_path = temp.name
            temp.write(normalized_content)
        
        try:
            # Run conllu_fixer directly
            temp_output_path = temp_path + ".fixed"
            try:
                fix_conllu_file(temp_path, temp_output_path, log_file)
                # Replace the temp file with the fixed version
                os.replace(temp_output_path, temp_path)
            except Exception as e:
                logger.error(f"Error during CoNLL-U fixing: {e}")
                return 1
            
            # Run validation directly
            try:
                validation_success = validate_conllu_file(temp_path, log_file)
                if not validation_success:
                    logger.error("CoNLL-U validation found errors. Stopping conversion process.")
                    return 1
            except Exception as e:
                logger.error(f"Error during CoNLL-U validation: {e}")
                return 1
            
            # Read the processed content back
            with open(temp_path, 'r', encoding='utf-8') as f:
                final_content = f.read()
            
            # Write final output
            with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
                f.write(final_content)
                
            logger.info(f"Conversion completed successfully: {input_file} -> {output_file}")
            return 0
            
        finally:
            # Clean up temp files
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                if os.path.exists(temp_output_path):
                    os.unlink(temp_output_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file(s): {e}")
    
    except Exception as e:
        logger.error(f"Error during conversion: {e}")
        return 1

def main():
    parser = argparse.ArgumentParser(description="Convert Google Sheets TSV to CoNLL-U format")
    parser.add_argument("-i", "--input", required=True, help="Input TSV file")
    parser.add_argument("-o", "--output", required=True, help="Output CoNLL-U file")
    parser.add_argument("-l", "--log", help="Log file (optional)")
    args = parser.parse_args()
    
    # Setup logging
    setup_logger(args.log)
    
    # Run conversion
    result = convert_file(args.input, args.output, args.log)
    
    # Return appropriate exit code
    return result

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
