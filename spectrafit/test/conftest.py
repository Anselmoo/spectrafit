"""Future test configuration for pytest."""

from __future__ import annotations

import io
import re
import warnings
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def suppress_moessbauer_warnings() -> Any:
    """Suppress Mössbauer experimental feature warnings during tests.
    
    This fixture automatically suppresses the UserWarning about Mössbauer models
    being experimental features for all tests in this module.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Mössbauer models are experimental features.*",
            category=UserWarning,
        )
        yield


def filter_moessbauer_stderr(stderr: str) -> str:
    """Filter out known warnings from stderr during tests.
    
    This function filters out:
    - Mössbauer experimental feature warnings
    - lmfit confidence interval warnings
    - pandas FutureWarnings
    - Other expected warnings from the fitting process
    
    Args:
        stderr: The stderr string to filter
        
    Returns:
        str: The filtered stderr with known warnings removed
    """
    # Remove lines containing known warnings
    lines = stderr.split('\n')
    filtered_lines = []
    
    for line in lines:
        # Skip if line contains any of the known warning patterns
        if any([
            re.search(r'Mössbauer models are experimental', line),
            re.search(r'from spectrafit\.models\.moessbauer', line),
            re.search(r'lmfit/confidence\.py.*UserWarning', line),
            re.search(r'rel_change.*at iteration.*prob\(', line),
            re.search(r'warn\(errmsg\)', line),
            re.search(r'Bound reached with prob\(', line),
            re.search(r'spectrafit/report\.py.*FutureWarning', line),
            re.search(r'Downcasting object dtype arrays', line),
            re.search(r'return correl_matrix\.fillna', line),
            re.search(r'Error:.*No confidence interval could be calculated', line),
            re.search(r'self\.print_confidence_interval\(\)', line),
            line.strip() == '+',  # Filter out leading '+' markers
        ]):
            continue
        
        filtered_lines.append(line)
    
    result = '\n'.join(filtered_lines).strip()
    # Remove multiple consecutive newlines
    result = re.sub(r'\n\s*\n', '\n', result)
    return result


def create_stdin(input_text: str) -> io.StringIO:
    """Create a StringIO object for stdin input in subprocess tests.
    
    Args:
        input_text: The text to provide as stdin input
        
    Returns:
        io.StringIO: A StringIO object containing the input text
    """
    return io.StringIO(input_text)


@pytest.fixture
def assert_no_errors_in_stderr() -> Any:
    """Fixture that provides a helper function to check stderr excluding known warnings.
    
    Returns:
        Callable that checks if stderr contains only known warnings
    """
    def _check_stderr(stderr: str) -> bool:
        """Check if stderr contains only known warnings."""
        filtered = filter_moessbauer_stderr(stderr)
        return filtered == "" or filtered == "\n"
    
    return _check_stderr
