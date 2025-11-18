import argparse
import logging
import os
from typing import Optional

from rich.logging import RichHandler


def setup_logging(verbosity_level: int = 0):
    """Configures logging based on verbosity level.

    Args:
        verbosity_level: 0 = WARNING (quiet), 1 = INFO, 2+ = DEBUG
    """
    if verbosity_level >= 2:
        log_level = logging.DEBUG
    elif verbosity_level == 1:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    handler = RichHandler(rich_tracebacks=True, show_path=False, markup=True)
    formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Silence noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def init(verbosity: Optional[int] = None):
    """Initialize logging with smart defaults.

    Reads verbosity from (in order of priority):
    1. Explicit verbosity argument
    2. LOG_LEVEL environment variable (DEBUG, INFO, WARNING, ERROR)
    3. Default to WARNING (quiet)

    This is the simplest entry point - just call once at script start.
    """
    if verbosity is None:
        # Try to read from environment
        log_level_str = os.getenv("LOG_LEVEL", "WARNING").upper()
        level_map = {"DEBUG": 2, "INFO": 1, "WARNING": 0, "ERROR": 0}
        verbosity = level_map.get(log_level_str, 0)

    setup_logging(verbosity)


def create_parser(description: str, **kwargs) -> argparse.ArgumentParser:
    """Create an ArgumentParser with verbose flag pre-configured.

    Returns a parser with -v/--verbose already added.
    Call parser.parse_args() then pass args.verbose to setup_logging().
    """
    parser = argparse.ArgumentParser(description=description, **kwargs)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v for INFO, -vv for DEBUG)",
    )
    return parser


def add_verbose_argument(parser: argparse.ArgumentParser):
    """Adds verbose argument to existing parser (legacy API)."""
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v for INFO, -vv for DEBUG)",
    )
