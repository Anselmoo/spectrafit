"""Future test configuration for pytest."""

from __future__ import annotations

import io


def create_stdin(input_text: str) -> io.StringIO:
    """Create a StringIO object for stdin input in subprocess tests.

    Args:
        input_text: The text to provide as stdin input

    Returns:
        io.StringIO: A StringIO object containing the input text
    """
    return io.StringIO(input_text)
