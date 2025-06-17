import re
import sys

def replace_unicode(match):
    # Extract the hexadecimal part from the match
    hex_value = match.group(1)
    # Convert the hexadecimal value to an integer, then to the corresponding Unicode character
    return chr(int(hex_value, 16))

def process_text(text):
    # This regex finds patterns like "\uXXXX" where X is a hex digit
    return re.sub(r'\\u([0-9a-fA-F]{4})', replace_unicode, text)

def main():
    if len(sys.argv) != 3:
        print("Usage: python convert_unicode.py input_file output_file")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = f.read()

    # Process the text to convert Unicode escapes to actual characters
    processed_data = process_text(data)

    # Write the processed text to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(processed_data)

if __name__ == "__main__":
    main()
