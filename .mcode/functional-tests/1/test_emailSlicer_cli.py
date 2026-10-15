"""
Functional tests for the emailSlicer.py CLI entry point.

Unlike tests/test_email_slicer.py (which imports and calls slice_email()
directly as a unit test), these tests invoke the real, unmodified CLI
entry point — `python emailSlicer.py` — as a subprocess, feeding it
stdin exactly as a human user would via `input()`. This is the behavior
that the milestone's refactor risk section calls out explicitly: moving
the input()/print() interaction into an `if __name__ == "__main__":`
block must not change the prompt text, output formatting (including the
original script's double-space quirk from
`print("Your username is: ", username)`), or which branch runs for edge
cases (empty string, multiple "@").

Run from anywhere; the script path is resolved relative to the repo root.
"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "emailSlicer.py"

PROMPT = "Please enter your Email Id:"
INVALID_MSG = "Please enter a valid Email Id."


def run_cli(stdin_text: str, args: list[str] | None = None) -> subprocess.CompletedProcess:
    """Invoke the real emailSlicer.py entry point non-interactively."""
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *(args or [])],
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(REPO_ROOT),
    )


@pytest.fixture(autouse=True, scope="module")
def ensure_script_exists():
    assert SCRIPT_PATH.is_file(), f"emailSlicer.py not found at {SCRIPT_PATH}"


class TestEmailSlicerCliHappyPath:
    """HAPPY_PATH / PIPE_INPUT: valid email piped via stdin."""

    def test_valid_email_matches_readme_example_exactly(self):
        # README.md's documented example: avimax37@gmail.com -> avimax37 / gmail.com
        # The original script prints with
        # `print("Your username is: ", username)` (a comma, not an f-string),
        # which inserts print()'s automatic space between the two positional
        # args, yielding a double space after the colon. That quirk must
        # survive the refactor byte-for-byte.
        result = run_cli("avimax37@gmail.com\n")

        expected_stdout = (
            f"{PROMPT}\n"
            "Your username is:  avimax37\n"
            "Your domain is:  gmail.com\n"
        )

        assert result.returncode == 0
        assert result.stdout == expected_stdout
        assert result.stderr == ""

    def test_valid_email_strips_surrounding_whitespace(self):
        # The CLI block calls .strip() on the raw input before slicing.
        result = run_cli("   avimax37@gmail.com   \n")

        assert result.returncode == 0
        assert "Your username is:  avimax37\n" in result.stdout
        assert "Your domain is:  gmail.com\n" in result.stdout


class TestEmailSlicerCliBoundary:
    """BOUNDARY: edge-case inputs exercised through the real CLI."""

    def test_multiple_at_characters_splits_on_first_at(self):
        # Documented behavior: str.index("@") / str.find("@") locate the
        # FIRST "@", so "a@b@c.com" -> username "a", domain "b@c.com".
        result = run_cli("a@b@c.com\n")

        expected_stdout = (
            f"{PROMPT}\n"
            "Your username is:  a\n"
            "Your domain is:  b@c.com\n"
        )

        assert result.returncode == 0
        assert result.stdout == expected_stdout

    def test_empty_string_input_is_treated_as_invalid(self):
        result = run_cli("\n")

        expected_stdout = f"{PROMPT}\n{INVALID_MSG}\n"

        assert result.returncode == 0
        assert result.stdout == expected_stdout

    def test_whitespace_only_input_is_treated_as_invalid(self):
        # "   ".strip() == "" -> no "@" -> ValueError -> invalid message.
        result = run_cli("   \n")

        expected_stdout = f"{PROMPT}\n{INVALID_MSG}\n"

        assert result.returncode == 0
        assert result.stdout == expected_stdout

    def test_at_symbol_only_input_is_valid_with_empty_parts(self):
        # "@" contains "@" at index 0, so it is "valid" per slice_email's
        # sole criterion (contains "@"); username and domain are both "".
        result = run_cli("@\n")

        expected_stdout = (
            f"{PROMPT}\n"
            "Your username is:  \n"
            "Your domain is:  \n"
        )

        assert result.returncode == 0
        assert result.stdout == expected_stdout


class TestEmailSlicerCliInvalidInput:
    """INVALID_INPUT: inputs with no "@" at all."""

    def test_no_at_symbol_prints_invalid_message(self):
        result = run_cli("not-an-email\n")

        expected_stdout = f"{PROMPT}\n{INVALID_MSG}\n"

        assert result.returncode == 0
        assert result.stdout == expected_stdout
        assert result.stderr == ""

    def test_no_at_symbol_exits_cleanly_without_traceback(self):
        # The ValueError raised by slice_email must be caught inside the
        # __main__ block, not propagate and crash the process.
        result = run_cli("plaintext\n")

        assert result.returncode == 0
        assert "Traceback" not in result.stderr
        assert result.stderr == ""


class TestEmailSlicerCliArgsIgnored:
    """INVALID_ARGS: the script takes no argv — extra args must be ignored, not crash it."""

    def test_extra_command_line_arguments_do_not_affect_behavior(self):
        result = run_cli("avimax37@gmail.com\n", args=["--bogus-flag", "ignored"])

        expected_stdout = (
            f"{PROMPT}\n"
            "Your username is:  avimax37\n"
            "Your domain is:  gmail.com\n"
        )

        assert result.returncode == 0
        assert result.stdout == expected_stdout
        assert result.stderr == ""
