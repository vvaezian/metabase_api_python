from metabase_api.utility.util import email_type
from hypothesis import strategies as st, given, assume


def test_empty_string_not_an_email() -> None:
    assert not email_type("")


@given(an_email=st.emails())
def test_myemail_an_email(an_email: str) -> None:
    """Checks for a subset of the RFC email standard."""
    prefix: str = an_email.split("@")[0]
    assume(all(c.isalnum() for c in prefix))
    assert email_type(an_email)
