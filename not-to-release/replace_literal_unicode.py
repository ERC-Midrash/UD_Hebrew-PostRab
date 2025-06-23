import re
import sys
import argparse

def replace_unicode(match):
    # Extract the hexadecimal part from the match
    hex_value = match.group(1)
    # Convert the hexadecimal value to an integer, then to the corresponding Unicode character
    return chr(int(hex_value, 16))

def process_text(text):
    # This regex finds patterns like "\uXXXX" where X is a hex digit
    return re.sub(r'\\u([0-9a-fA-F]{4})', replace_unicode, text)

def main():
    parser = argparse.ArgumentParser(description="Convert Unicode escape sequences (\\uXXXX) to actual characters in a text file.")
    parser.add_argument("--input_file", "-i", required=True, help="Path to the input file")
    parser.add_argument("--output_file", "-o", required=True, help="Path to the output file")
    args = parser.parse_args()

    # Read the input file
    with open(args.input_file, 'r', encoding='utf-8') as f:
        data = f.read()

    # Process the text to convert Unicode escapes to actual characters
    processed_data = process_text(data)

    # Write the processed text to the output file
    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write(processed_data)

if __name__ == "__main__":
    main()
