import conllu
import argparse
import logging
import traceback
import sys

def main():
    parser = argparse.ArgumentParser(description="Parse a CoNLL-U file and check for errors.")
    parser.add_argument("-i", "--input_file", help="Path to the CoNLL-U file")
    parser.add_argument("-l", "--log_file", help="Path to the log file (optional)")
    args = parser.parse_args()

    # Configure logging
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # Use specified log file if provided, otherwise log to console
    if args.log_file:
        file_handler = logging.FileHandler(args.log_file, 'w', 'utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        log_destination = f"See '{args.log_file}' for details."
    else:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        log_destination = "See error output above."

    success = True
    with open(args.input_file, "r", encoding="utf-8") as f:
        try:
            _ = conllu.parse(f.read())
            print("Parsing completed successfully. No errors found.")
        except Exception as e:
            tb = traceback.format_exc()
            logging.error(f"Error during parsing file '{args.input_file}':\n{tb}")
            print(f"Error during parsing. {log_destination}")
            success = False
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)