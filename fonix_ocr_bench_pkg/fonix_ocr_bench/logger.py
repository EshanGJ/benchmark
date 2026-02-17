import logging
import sys

# ANSI escape codes for colors
class Colors:
    RESET = "\033[0m"
    DEBUG = "\033[36m"  # Cyan
    INFO = "\033[32m"   # Green
    WARNING = "\033[33m" # Yellow
    ERROR = "\033[31m"  # Red
    BOLD = "\033[1m"

class ColoredFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: f"{Colors.DEBUG}[DEBUG]{Colors.RESET} %(message)s",
        logging.INFO: f"{Colors.INFO}[INFO]{Colors.RESET} %(message)s",
        logging.WARNING: f"{Colors.WARNING}[WARNING]{Colors.RESET} %(message)s",
        logging.ERROR: f"{Colors.ERROR}[ERROR]{Colors.RESET} %(message)s",
        logging.CRITICAL: f"{Colors.ERROR}{Colors.BOLD}[CRITICAL]{Colors.RESET} %(message)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logger(name="fonix_ocr_bench", level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Check if handlers already exist to avoid duplicate logs
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(ColoredFormatter())
        logger.addHandler(handler)
    
    return logger

# Create a default logger instance
logger = setup_logger()
