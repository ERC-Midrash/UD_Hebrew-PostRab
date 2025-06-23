#!/usr/bin/env python3
import re
import sys
import logging
import argparse
from collections import defaultdict

import re
from collections import defaultdict

class PlusNotationError(Exception):
    """Exception raised for errors in the plus notation processing."""
    pass

def parse_id_with_plus(id_str):
    if '+' in id_str:
        try:
            base, increment = map(int, id_str.split('+'))
            return base, increment
        except ValueError:
            raise PlusNotationError(f"Invalid numeric values in plus notation: {id_str}")
    try:
        return int(id_str), 0
    except ValueError:
        return id_str, 0  # Non-numeric ID

def process_plus_notation_sentence(lines):
    """
    Process a CoNLL-U sentence with plus notation.
    
    Args:
        lines (list): List of lines in a CoNLL-U sentence
    
    Returns:
        list: Processed lines with plus notations resolved
    """

    increments = defaultdict(int)
    id_pattern = re.compile(r'^(\d+)(?:\+(\d+))?')
    range_pattern = re.compile(r'^(\d+)(?:\+(\d+))?-(\d+)(?:\+(\d+))?')
    
    # Set to track range endpoints that need validation
    range_endpoints = set()
    # Set to track all token IDs in the sentence
    token_ids = set()

    # Collect increments and track endpoints and tokens
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        fields = line.split('\t')
        
        range_match = range_pattern.match(fields[0])
        if range_match:
            # Collect range data
            start_base = int(range_match.group(1))
            start_inc = int(range_match.group(2) or 0)
            end_base = int(range_match.group(3))
            end_inc = int(range_match.group(4) or 0)
            
            # Add range endpoints to validation set
            range_endpoints.add(f"{start_base}+{start_inc}" if start_inc > 0 else f"{start_base}")
            range_endpoints.add(f"{end_base}+{end_inc}" if end_inc > 0 else f"{end_base}")
            
            # Process increments for this range
            for i in [1, 3]:
                base = int(range_match.group(i))
                inc = int(range_match.group(i + 1) or 0)
                increments[base] = max(increments[base], inc)
            continue
        
        # Add this token ID to the set of all token IDs
        token_ids.add(fields[0])
        
        if fields[0]:
            match = id_pattern.match(fields[0])
            if match:
                base, inc = int(match.group(1)), int(match.group(2) or 0)
                increments[base] = max(increments[base], inc)

        if len(fields) >= 7:
            match = id_pattern.match(fields[6])
            if match:
                base, inc = int(match.group(1)), int(match.group(2) or 0)
                increments[base] = max(increments[base], inc)
    
    # Validate that all range endpoints exist as token IDs
    missing_endpoints = range_endpoints - token_ids
    if missing_endpoints:
        raise PlusNotationError(f"Range endpoints not found as token IDs: {', '.join(missing_endpoints)}")

    # Check for missing intermediate IDs
    for base, max_inc in increments.items():
        for i in range(1, max_inc):
            target = f"{base}+{i}"
            if not any(target in (line.split('\t')[0], line.split('\t')[6] if len(line.split('\t')) >= 7 else '') for line in lines if not line.startswith('#')):
                raise PlusNotationError(f"Missing intermediate plus notation: {target}")

    cumulative_shifts = {}
    shift = 0
    for base in sorted(increments):
        cumulative_shifts[base] = shift
        shift += increments[base]

    output_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            output_lines.append(line.rstrip('\n'))
            continue

        fields = stripped.split('\t')

        range_match = range_pattern.match(fields[0])
        if range_match:
            start_base, start_inc = int(range_match.group(1)), int(range_match.group(2) or 0)
            end_base, end_inc = int(range_match.group(3)), int(range_match.group(4) or 0)
            new_start = start_base + start_inc + cumulative_shifts.get(start_base, 0)
            new_end = end_base + end_inc + cumulative_shifts.get(end_base, 0)
            fields[0] = f"{new_start}-{new_end}"
            output_lines.append('\t'.join(fields))
            continue

        if fields[0]:
            base, inc = parse_id_with_plus(fields[0])
            if isinstance(base, int):
                fields[0] = str(base + inc + cumulative_shifts.get(base, 0))

        if len(fields) >= 7 and ('+' in fields[6] or fields[6].isdigit()):
            base, inc = parse_id_with_plus(fields[6])
            if isinstance(base, int):
                fields[6] = str(base + inc + cumulative_shifts.get(base, 0))

        output_lines.append('\t'.join(fields))

    return output_lines

def process_skipped_ids_sentence(lines):
    token_ids, comments, range_lines = [], [], {}
    range_pattern = re.compile(r'^(\d+)-(\d+)')

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('#'):
            comments.append(line.rstrip('\n'))
            continue

        match = range_pattern.match(stripped)
        if match:
            start, end = map(int, match.groups())
            range_lines[start] = (end, line.rstrip('\n'))
            continue

        fields = stripped.split('\t')
        if fields[0].isdigit():
            token_ids.append(int(fields[0]))

    if not token_ids:
        return lines

    all_ids = set(range(min(token_ids), max(token_ids) + 1))
    missing = all_ids - set(token_ids)
    if not missing:
        return lines

    id_map, shift = {}, 0
    for i in range(min(token_ids), max(token_ids) + 1):
        if i in missing:
            shift += 1
        else:
            id_map[i] = i - shift

    processed_ranges = {}
    for start, (end, line) in sorted(range_lines.items()):
        new_start = id_map.get(start, start - shift)
        new_end = new_start + sum(start <= i <= end for i in token_ids) - 1
        fields = line.split('\t')
        fields[0] = f"{new_start}-{new_end}"
        processed_ranges[start] = '\t'.join(fields)

    output = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('#'):
            output.append(line.rstrip('\n'))
            continue
        match = range_pattern.match(stripped)
        if match:
            start = int(match.group(1))
            output.append(processed_ranges[start])
            continue

        fields = stripped.split('\t')
        if fields[0].isdigit():
            old_id = int(fields[0])
            fields[0] = str(id_map.get(old_id, old_id - shift))
            if len(fields) >= 7 and fields[6].isdigit() and int(fields[6]) > 0:
                fields[6] = str(id_map.get(int(fields[6]), int(fields[6]) - shift))
            output.append('\t'.join(fields))
        else:
            output.append(line.rstrip('\n'))

    return output

def fix_conllu_sentence(lines):
    return process_skipped_ids_sentence(process_plus_notation_sentence(lines))


class PlusNotationError_Legacy(Exception):
    """Exception raised for errors in the plus notation processing."""
    pass

def parse_id_with_plus_Legacy(id_str):
    """
    Parse an ID string that might contain plus notation.
    Returns (base_number, increment) tuple.
    
    Args:
        id_str (str): The ID string, like "10" or "10+2"
        
    Returns:
        tuple: (base_number, increment)
    """
    if '+' in id_str:
        parts = id_str.split('+')
        if len(parts) != 2:
            raise PlusNotationError(f"Invalid plus notation format: {id_str}. Expected format like '10+2'")
            
        try:
            base = int(parts[0])
            increment = int(parts[1])
            return base, increment
        except ValueError:
            raise PlusNotationError(f"Invalid numeric values in plus notation: {id_str}")
    else:
        try:
            return int(id_str), 0
        except ValueError:
            return id_str, 0  # Non-numeric ID, like '_'

def process_plus_notation_sentence_legacy(lines):
    """
    Process a CoNLL-U sentence with plus notation.
    
    Args:
        lines (list): List of lines in a CoNLL-U sentence
    
    Returns:
        list: Processed lines with plus notations resolved
    """
    # First, extract all the plus increments and find the max for each base number
    increments = {}
    
    # Regex patterns for ID fields and range notation
    id_pattern = re.compile(r'^(\d+)(?:\+(\d+))?')
    range_pattern = re.compile(r'^(\d+)(?:\+(\d+))?-(\d+)(?:\+(\d+))?')
    
    # First pass - collect all increments
    for line in lines:
        line = line.rstrip('\n').strip()
        if not line or line.startswith('#'):
            continue
            
        # Check for range notation first
        range_match = range_pattern.match(line)
        if range_match:
            start_base = int(range_match.group(1))
            start_inc = int(range_match.group(2) or 0)
            end_base = int(range_match.group(3))
            end_inc = int(range_match.group(4) or 0)
            
            # Update increments dictionary with max values
            increments[start_base] = max(increments.get(start_base, 0), start_inc)
            increments[end_base] = max(increments.get(end_base, 0), end_inc)
            continue
            
        # Regular ID field
        fields = line.split('\t')
        if not fields[0]:
            continue
            
        id_match = id_pattern.match(fields[0])
        if id_match and id_match.group(1):
            base = int(id_match.group(1))
            inc = int(id_match.group(2) or 0)
            increments[base] = max(increments.get(base, 0), inc)
            
        # Check head field too
        if len(fields) >= 7:  # Ensure we have enough fields
            head_field = fields[6]
            head_match = id_pattern.match(head_field)
            if head_match and head_match.group(1):
                head_base = int(head_match.group(1))
                head_inc = int(head_match.group(2) or 0)
                increments[head_base] = max(increments.get(head_base, 0), head_inc)
    
    # Validate that there are no missing intermediate plus indexes
    for base in increments:
        max_inc = increments[base]
        for i in range(1, max_inc):
            missing_key = f"{base}+{i}"
            found = False
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                fields = line.split('\t')
                if fields[0].startswith(f"{base}+{i}") or (len(fields) >= 7 and fields[6].startswith(f"{base}+{i}")):
                    found = True
                    break
            if not found:
                raise PlusNotationError(f"Missing intermediate plus notation: {missing_key}")
    
    # Calculate cumulative shifts for each base number
    # Start from the highest base number and work backwards
    bases = sorted(increments.keys())
    cumulative_shifts = {}
    current_shift = 0
    
    for base in bases:
        cumulative_shifts[base] = current_shift
        current_shift += increments[base]
    
    # Second pass - apply the shifts to generate the output lines
    output_lines = []
    
    for line in lines:
        stripped_line = line.rstrip('\n').strip()
        if not stripped_line or stripped_line.startswith('#'):
            output_lines.append(line.rstrip('\n'))
            continue
            
        # Process range lines
        range_match = range_pattern.match(stripped_line)
        if range_match:
            start_base = int(range_match.group(1))
            start_inc = int(range_match.group(2) or 0)
            end_base = int(range_match.group(3))
            end_inc = int(range_match.group(4) or 0)
            
            # Calculate new start and end
            new_start = start_base + start_inc + cumulative_shifts.get(start_base, 0)
            new_end = end_base + end_inc + cumulative_shifts.get(end_base, 0)
            
            # Format the new range line
            fields = stripped_line.split('\t')
            fields[0] = f"{new_start}-{new_end}"
            output_lines.append('\t'.join(fields))
            continue
            
        # Process regular token lines
        fields = stripped_line.split('\t')
        if not fields[0]:
            output_lines.append(line.rstrip('\n'))
            continue
            
        # Process ID field
        id_match = id_pattern.match(fields[0])
        if id_match and id_match.group(1):
            base, inc = parse_id_with_plus(fields[0])
            
            # Calculate new ID
            new_id = base + inc + cumulative_shifts.get(base, 0)
            
            fields[0] = str(new_id)
        
        # Process head field
        if len(fields) >= 7:
            head_field = fields[6]
            if head_field.isdigit() or '+' in head_field:
                head_base, head_inc = parse_id_with_plus(head_field)
                if isinstance(head_base, int):  # Skip non-numeric head fields
                    # Calculate new head
                    new_head = head_base + head_inc + cumulative_shifts.get(head_base, 0)
                    
                    fields[6] = str(new_head)
        
        output_lines.append('\t'.join(fields))
    
    return output_lines

def process_skipped_ids_sentence_legacy(lines):
    """
    Process a CoNLL-U sentence to handle skipped IDs (unification of tokens).
    Updates IDs and head references to be sequential after removing skips.
    
    Args:
        lines (list): List of lines in a CoNLL-U sentence
        
    Returns:
        list: Processed lines with sequential IDs
    """
    # Extract all actual IDs to find gaps
    token_ids = []
    range_lines = {}
    comments = []
    
    id_pattern = re.compile(r'^(\d+)')
    range_pattern = re.compile(r'^(\d+)-(\d+)')
    
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue
        
        if stripped_line.startswith('#'):
            comments.append(line.rstrip('\n'))
            continue
            
        range_match = range_pattern.match(stripped_line)
        if range_match:
            start_id = int(range_match.group(1))
            end_id = int(range_match.group(2))
            range_lines[start_id] = (end_id, line.rstrip('\n'))
            continue
            
        fields = stripped_line.split('\t')
        if fields[0].isdigit():
            token_ids.append(int(fields[0]))
    
    # If no tokens found, return the original lines
    if not token_ids:
        return lines
        
    # Find gaps in the sequence
    min_id = min(token_ids)
    max_id = max(token_ids)
    all_possible_ids = set(range(min_id, max_id + 1))
    missing_ids = all_possible_ids - set(token_ids)
    
    # If no gaps, return the original lines
    if not missing_ids:
        return lines
    
    # Create a mapping for ID adjustment
    id_map = {}
    shift = 0
    
    for i in range(min_id, max_id + 1):
        if i in missing_ids:
            shift += 1
        else:
            id_map[i] = i - shift
    
    # Process range lines but don't add them to output yet
    processed_range_lines = {}
    
    for start_id, (end_id, line) in sorted(range_lines.items()):
        # Calculate new start and end based on the mapping
        new_start = id_map.get(start_id, start_id - shift)
        
        # Need to count how many actual token lines exist in the range
        # to determine the new end ID
        tokens_in_range = [id for id in token_ids if start_id <= id <= end_id]
        new_end = new_start + len(tokens_in_range) - 1
        
        fields = line.split('\t')
        fields[0] = f"{new_start}-{new_end}"
        processed_range_lines[start_id] = '\t'.join(fields)
    
    # Process all lines in original order and apply the mapping
    output_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue
            
        if stripped_line.startswith('#'):
            output_lines.append(line.rstrip('\n'))
            continue
            
        range_match = range_pattern.match(stripped_line)
        if range_match:
            start_id = int(range_match.group(1))
            output_lines.append(processed_range_lines[start_id])
            continue
            
        fields = stripped_line.split('\t')
        if fields[0].isdigit():
            token_id = int(fields[0])
            new_id = id_map.get(token_id, token_id - shift)
            fields[0] = str(new_id)
            
            # Update head references
            if len(fields) >= 7 and fields[6].isdigit():
                head_id = int(fields[6])
                if head_id > 0:  # Skip root references (0)
                    new_head = id_map.get(head_id, head_id - shift)
                    fields[6] = str(new_head)
            
            output_lines.append('\t'.join(fields))
        else:
            output_lines.append(line.rstrip('\n'))  # Non-token line
    
    return output_lines

def fix_conllu_sentence_legacy(lines):
    """
    Process a CoNLL-U sentence applying both plus notation handling
    and skipped ID handling.
    
    Args:
        lines (list): List of lines in a CoNLL-U sentence
        
    Returns:
        list: Processed lines with plus notation resolved and IDs sequential
    """
    # First, process plus notation
    plus_processed_lines = process_plus_notation_sentence(lines)
    
    # Then, handle skipped IDs
    return process_skipped_ids_sentence(plus_processed_lines)

def process_conllu_file(input_path, output_path, log_file_path=None):
    """
    Processes a CoNLL-U file sentence by sentence using fix_conllu_sentence,
    logging errors to a specified file.

    Args:
        input_path (str): Path to the input CoNLL-U file.
        output_path (str): Path to write the processed CoNLL-U file.
        log_file_path (str, optional): Path to the log file. If None, errors
                                       are not logged to a file. Defaults to None.
    """
    logger = logging.getLogger(__name__ + '.process_conllu_file')
    logger.handlers.clear()  # Prevent duplicate handlers if called multiple times
    logger.setLevel(logging.INFO)
    
    if log_file_path:
        # Create file handler
        fh = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
        fh.setLevel(logging.ERROR)  # Log only errors and critical to file
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    else:
        # If no log file, add a NullHandler to prevent "No handler found" warnings
        logger.addHandler(logging.NullHandler())

    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        
        current_sentence_lines = []
        sentence_count = 0
        error_count = 0

        for line in infile:
            if not line.strip():  # Blank line indicates end of sentence
                if current_sentence_lines:
                    sentence_count += 1
                    try:
                        # Process the sentence
                        fixed_lines = fix_conllu_sentence(current_sentence_lines) 
                        for fixed_line in fixed_lines:
                            outfile.write(fixed_line + '\n')
                    except PlusNotationError as e:
                        error_count += 1
                        error_msg = f"Error processing plus notation in sentence {sentence_count}: {e}"
                        # TODO instead of using a sentence counter, use the sent_id in the file if available
                        logger.error(error_msg)
                        print(error_msg, file=sys.stderr)
                        # Write original lines on error
                        for original_line in current_sentence_lines:
                            outfile.write(original_line)
                    except Exception as e:
                        error_count += 1
                        error_msg = f"Unexpected error processing sentence {sentence_count}: {e}"
                        logger.error(error_msg, exc_info=True)
                        print(error_msg, file=sys.stderr)
                        # Write original lines on unexpected error
                        for original_line in current_sentence_lines:
                            outfile.write(original_line)
                    
                    outfile.write('\n')  # Write the blank line separator
                    current_sentence_lines = []
                else:
                    # Handle consecutive blank lines
                    outfile.write('\n') 
            else:
                current_sentence_lines.append(line)

        # Process the last sentence if the file doesn't end with a blank line
        if current_sentence_lines:
            sentence_count += 1
            try:
                fixed_lines = fix_conllu_sentence(current_sentence_lines)
                for fixed_line in fixed_lines:
                    outfile.write(fixed_line + '\n')
            except PlusNotationError as e:
                error_count += 1
                error_msg = f"Error processing plus notation in sentence {sentence_count}: {e}"
                logger.error(error_msg)
                print(error_msg, file=sys.stderr)
                for original_line in current_sentence_lines:
                    outfile.write(original_line)
            except Exception as e:
                error_count += 1
                error_msg = f"Unexpected error processing sentence {sentence_count}: {e}"
                logger.error(error_msg, exc_info=True)
                print(error_msg, file=sys.stderr)
                for original_line in current_sentence_lines:
                    outfile.write(original_line)
            outfile.write('\n')  # Ensure final newline
        
        summary_msg = f"Processed {sentence_count} sentences. Encountered {error_count} errors."
        logger.info(summary_msg)
        print(summary_msg)

# Test functions have been moved to tests/test_conllu_fixer2.py

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
    Processes a CoNLL-U file to fix token IDs and ranges based on plus notation.
    It handles:
    1. Plus notation for token splitting (e.g., 10+1, 10+2)
    2. Skipped IDs for token unification
    3. Range adjustments for multi-word tokens
    
    Errors during processing are logged and the original sentence is written to the output.
    """)
    parser.add_argument("-i", "--input", help="Path to the input CoNLL-U file.")
    parser.add_argument("-o", "--output", help="Path to write the processed CoNLL-U file.")
    parser.add_argument("-l", "--log", default="conllu_fixer2.log", help="Path to the log file (default: conllu_fixer2.log).")
    
    args = parser.parse_args()
    
    if args.input and args.output:
        process_conllu_file(args.input, args.output, args.log)
    else:
        parser.print_help()
