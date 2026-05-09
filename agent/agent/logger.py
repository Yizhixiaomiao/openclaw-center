import logging
import os
from logging.handlers import RotatingFileHandler

DEFAULT_LOG_DIR = r"C:\ProgramData\OpenClawCenterAgent\logs"


def setup_logger(name="openclaw-agent", log_dir=None, max_bytes=10*1024*1024, backup_count=5):
    log_dir = log_dir or DEFAULT_LOG_DIR
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        fh = RotatingFileHandler(
            os.path.join(log_dir, "agent.log"),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(ch)

    return logger
