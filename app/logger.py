import logging
import os

logger = logging.getLogger("uvicorn")
logger.setLevel(os.environ.get("LOG_LEVEL", logging.INFO))
