from datetime import datetime


def parse_datetime(date: str) -> datetime:
    """Parse GitHub date to object"""
    exp = "%Y-%m-%dT%H:%M:%SZ"
    return datetime.strptime(date, exp)
