# StrEnum only in Python 3.11
from enum import Enum


class GithubHeaders(str, Enum):
    # NOTE: Flask manipulates as Capital-Word-Per-Section
    EVENT = "X-Github-Event"
    HOOK_ID = "X-Github-Hook-Id"
    DELIVERY = "X-Github-Delivery"


LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "[%(asctime)s]: %(levelname)s | %(message)s",
        }
    },
    "handlers": {
        "wsgi": {
            "class": "logging.StreamHandler",
            "stream": "ext://flask.logging.wsgi_errors_stream",
            "formatter": "default",
        }
    },
    "root": {"level": "INFO", "handlers": ["wsgi"]},
}
