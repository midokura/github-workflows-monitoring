from datetime import datetime

def parse_datetime(date: str) -> datetime:
    """ Parse GitHub date to object """
    exp = "%Y-%m-%dT%H:%M:%SZ"
    return datetime.strptime(date, exp)


def get_message(*args) -> str:
    """ Return variables as string logfmt """
    msg = list()
    for variable in args:
        var_name = f"{variable=}".split("=")[0]
        msg.append(f'{var_name}="{variable}"')
    return " ".join(msg)
