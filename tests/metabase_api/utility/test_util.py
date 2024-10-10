import string

from metabase_api.utility.util import email_type, case_expand
from hypothesis import strategies as st, given, assume


def test_empty_string_not_an_email() -> None:
    assert not email_type("")


@given(an_email=st.emails())
def test_myemail_an_email(an_email: str) -> None:
    """Checks for a subset of the RFC email standard."""
    prefix: str = an_email.split("@")[0]
    assume(all(c.isalnum() for c in prefix))
    assert email_type(an_email)


def test_case_expand_empty() -> None:
    assert case_expand("") == {""}


@given(
    sentence=st.lists(
        elements=st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
        min_size=1,
        max_size=10,
    ).map(lambda l: " ".join(l))
)
def test_case_expand_includes_same_sentence(sentence: str) -> None:
    assert sentence in case_expand(sentence)


@given(
    sentence=st.lists(
        elements=st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
        min_size=1,
        max_size=10,
    ).map(lambda l: " ".join(l))
)
def test_case_expand_has_at_most_3_expansions(sentence: str) -> None:
    s = case_expand(sentence)
    assert len(s) <= 3
