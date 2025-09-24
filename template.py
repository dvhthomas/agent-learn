# Starting point for most scripts with logging, CLI arg setup, and environment.
# Create a .env file in the same directory as the script
import argparse
import logging

from common import add_verbose_argument, setup_logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Brief description of the script's purpose"
    )
    add_verbose_argument(parser)
    args = parser.parse_args()
    setup_logging(args.verbose)

    logging.info("Starting scripts...")
