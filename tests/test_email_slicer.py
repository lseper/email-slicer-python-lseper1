import sys
from pathlib import Path

import pytest

# The project has a flat layout (emailSlicer.py lives at the repo root) and
# tests/ has no __init__.py, so pytest's default "prepend" import mode adds
# only tests/ to sys.path, not the repo root. Add the repo root explicitly
# so `import emailSlicer` resolves regardless of the invocation directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from emailSlicer import slice_email


@pytest.mark.parametrize(
    "email, expected",
    [
        ("avimax37@gmail.com", ("avimax37", "gmail.com")),
        # Only the first "@" is used as the split point, matching the
        # behaviour of email.index("@") / email.find("@") in slice_email.
        ("a@b@c.com", ("a", "b@c.com")),
    ],
)
def test_slice_email_valid(email, expected):
    assert slice_email(email) == expected


@pytest.mark.parametrize(
    "email",
    [
        "no-at-symbol-here.com",
        "",
    ],
)
def test_slice_email_raises_without_at(email):
    with pytest.raises(ValueError):
        slice_email(email)
