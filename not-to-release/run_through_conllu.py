import conllu
import argparse
import logging
import traceback

def main():
    parser = argparse.ArgumentParser(description="Parse a CoNLL-U file and check for errors.")
    parser.add_argument("-i", "--input_file", help="Path to the CoNLL-U file")
    args = parser.parse_args()

    # Set up logging to a file
    logging.basicConfig(filename='conllu_parse_errors.log', level=logging.ERROR,
                        format='%(asctime)s %(levelname)s: %(message)s')

    with open(args.input_file, "r", encoding="utf-8") as f:
        try:
            _ = conllu.parse(f.read())
            print("Parsing completed successfully. No errors found.")
        except Exception as e:
            tb = traceback.format_exc()
            logging.error(f"Error during parsing file '{args.input_file}':\n{tb}")
            print(f"Error during parsing. See 'conllu_parse_errors.log' for details.")

if __name__ == "__main__":
    main()