import argparse
import logging

from rich.logging import RichHandler

# Define a custom log level for user-facing messages
NOTICE_LEVEL_NUM = 25
logging.addLevelName(NOTICE_LEVEL_NUM, "NOTICE")


def notice(self, message, *args, **kws):
    if self.isEnabledFor(NOTICE_LEVEL_NUM):
        self._log(NOTICE_LEVEL_NUM, message, args, **kws)


logging.Logger.notice = notice


def add_verbose_argument(parser: argparse.ArgumentParser):
    """Adds a verbose argument to the argument parser."""
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity level (-v for INFO, -vv for DEBUG).",
    )


def setup_logging(verbosity_level: int):
    """Configures logging based on the verbosity level using RichHandler."""
    if verbosity_level == 1:
        log_level = logging.INFO
    elif verbosity_level >= 2:
        log_level = logging.DEBUG
    else:
        log_level = NOTICE_LEVEL_NUM

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # If handlers already exist, clear them to avoid duplication
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Add a RichHandler with a simple format
    handler = RichHandler(rich_tracebacks=True, show_path=False)
    formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Silence noisy loggers from other libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.info("Logging configured with level: %s", logging.getLevelName(log_level))
