import conllu
import argparse
import logging
import traceback
import sys

def validate_conllu_file(input_file, log_file=None):
    """
    Parse a CoNLL-U file and check for errors.
    
    Args:
        input_file (str): Path to the CoNLL-U file
        log_file (str, optional): Path to the log file. If None, logs to console.
        
    Returns:
        bool: True if parsing completed successfully, False otherwise
    """
    # Configure logging
    logger = logging.getLogger('validate_conllu')
    logger.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Use specified log file if provided, otherwise log to console
    if log_file:
        file_handler = logging.FileHandler(log_file, 'w', 'utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        log_destination = f"See '{log_file}' for details."
    else:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        log_destination = "See error output above."

    success = True
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            try:
                _ = conllu.parse(f.read())
                print("Parsing completed successfully. No errors found.")
            except Exception as e:
                tb = traceback.format_exc()
                logger.error(f"Error during parsing file '{input_file}':\n{tb}")
                print(f"Error during parsing. {log_destination}")
                success = False
    except FileNotFoundError:
        logger.error(f"File '{input_file}' not found.")
        print(f"Error: File '{input_file}' not found.")
        success = False
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Error opening file '{input_file}':\n{tb}")
        print(f"Error opening file. {log_destination}")
        success = False
    
    return success

def main():
    """
    Main function for command-line execution.
    Parses arguments and calls validate_conllu_file.
    
    Returns:
        bool: True if parsing completed successfully, False otherwise
    """
    parser = argparse.ArgumentParser(description="Parse a CoNLL-U file and check for errors.")
    parser.add_argument("-i", "--input_file", required=True, help="Path to the CoNLL-U file")
    parser.add_argument("-l", "--log_file", help="Path to the log file (optional)")
    args = parser.parse_args()
    
    return validate_conllu_file(args.input_file, args.log_file)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)