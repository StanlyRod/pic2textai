import logging
from rich import print
from rich.logging import RichHandler

# # Configure logging 
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S",handlers=[RichHandler()] ) 

# Create logger
rich_logging = logging.getLogger("rich_logger")

# Set the logging level to INFO
def log_info(message: str):
    rich_logging.info(message)

# Set the logging level to ERROR
def log_error(message: str):
    rich_logging.error(message)