import re


def email_type(value: str) -> bool:
    """Checks if a specific value is, actually, an email."""
    RE_EMAIL = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    r = RE_EMAIL.match(value)
    return r is not None


def case_expand(sentence: str) -> set[str]:
    """
    Does all SENSIBLE case expansions for a sentence.
    Basically 3 cases:
    (1) the sentence as presented
    (2) the sentence with all words in lowercase
    (3) the sentence with all words in uppercase
    Args:
        sentence: a sentence

    Returns: all possible sensible case expansions, as a set.

    """
    all_lowercase = " ".join([w.casefold() for w in sentence.split()])
    all_uppercase = " ".join([w.capitalize() for w in sentence.split()])
    return {sentence, all_lowercase, all_uppercase}
