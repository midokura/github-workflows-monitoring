from datetime import datetime


def parse_datetime(date: str) -> datetime:
    """Parse GitHub date to object"""
    exp = "%Y-%m-%dT%H:%M:%SZ"
    return datetime.strptime(date, exp)


def dict_to_logfmt(data: dict) -> str:
    """Convert a dict to logfmt string"""
    outstr = list()
    for k, v in data.items():
        if v is None:
            outstr.append(f"{k}=")
            continue
        if isinstance(v, bool):
            v = "true" if v else "false"
        elif isinstance(v, (dict, object, int)):
            v = str(v)

        if " " in v:
            v = '"%s"' % v.replace('"', '\\"')
        outstr.append(f"{k}={v}")
    return " ".join(outstr)
