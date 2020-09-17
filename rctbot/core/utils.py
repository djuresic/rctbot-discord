"""
Core utility functions.
"""


def chunks(list_, n):
    # https://stackoverflow.com/a/312464/13185424
    """Yield successive n-sized chunks from list."""
    for i in range(0, len(list_), n):
        yield list_[i : i + n]


def ordinal(n: int) -> str:
    """Convert a cardinal to an ordinal number.

    Args:
        n (int): Number to convert.

    Returns:
        str: Cardinal number.
    """
    suffix = "th" if 4 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def dhms(seconds: int) -> str:
    """Convert seconds to dd:hh:mm:ss.

    Args:
        seconds (int): Input seconds.

    Returns:
        str: dd:hh:mm:ss, days and hours not included if those values are 0.
    """
    dhms = ""
    for scale in 86400, 3600, 60:
        result, seconds = divmod(seconds, scale)
        if dhms != "" or result > 0:
            dhms += "{0:02d}:".format(result)
    dhms += "{0:02d}".format(seconds)
    if dhms != "00":
        return dhms
    return "00:00"
