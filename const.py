# StrEnum only in Python 3.11
from enum import Enum


class GithubHeaders(str, Enum):
    # NOTE: Flask manipulates as Capital-Word-Per-Section
    EVENT = "X-Github-Event"
    HOOK_ID = "X-Github-Hook-Id"
    DELIVERY = "X-Github-Delivery"
