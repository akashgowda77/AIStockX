import logging
import sys


def get_logger(name: str = "ai_stockx") -> logging.Logger:
    """Create and return a configured logger.

    Input:
        name: logger name
    Output:
        logging.Logger instance
    """

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

