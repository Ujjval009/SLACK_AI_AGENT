import logging
import sys
import os


def setup_logger(name: str = "slack_ai_agent") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if os.getenv("NODE_ENV") == "development" else logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "[%(levelname)s] %(message)s"
    ))
    logger.addHandler(handler)

    return logger


log = setup_logger()
