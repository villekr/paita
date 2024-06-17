from loguru import logger as log
from textual.logging import TextualHandler

# log.add(
#     format="{time} {level} {file}:{line} - {message}",
# )

log.configure(
    handlers=[{"sink": TextualHandler(), "format": "{level} {file}:{line} - {message}"}],
)
# log.level("INFO")
