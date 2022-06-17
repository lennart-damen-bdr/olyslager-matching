import logging
import sys

LOGGING_FORMAT = (
    "%(asctime)s | %(levelname)-8s | Process: %(process)d | %(name)s:%("
    "funcName)s:%(lineno)d - %(message)s"
)


def configure_logger(level: int) -> None:
    """
    Define logs level and formats.

    Args:
        verbose: logging level
    """
    logging.basicConfig(
        stream=sys.stdout,
        format=LOGGING_FORMAT,
        level=level,
    )
