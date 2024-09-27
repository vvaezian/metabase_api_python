import re


def email_type(value: str) -> bool:
    """Checks if a specific value is, actually, an email."""
    RE_EMAIL = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    r = RE_EMAIL.match(value)
    return r is not None
