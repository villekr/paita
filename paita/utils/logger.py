from loguru import logger as log
from textual.logging import TextualHandler

log.configure(
    handlers=[{"sink": TextualHandler(), "format": "{message}"}],
)
# log.level("INFO")
