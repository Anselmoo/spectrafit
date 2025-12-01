"""Future test configuration for pytest."""

from __future__ import annotations

import io
import re


def filter_moessbauer_stderr(stderr: str) -> str:
    """Filter out known warnings from stderr during tests.

    This function filters out:
    - Mössbauer experimental feature warnings
    - lmfit confidence interval warnings
    - pandas FutureWarnings
    - spectrafit report warnings about uncertainties
    - Other expected warnings from the fitting process

    Args:
        stderr: The stderr string to filter

    Returns:
        str: The filtered stderr with known warnings removed
    """
    # Remove lines containing known warnings
    lines = stderr.split("\n")
    filtered_lines = []

    for line in lines:
        # Skip if line contains any of the known warning patterns
        if any(
            [
                re.search(r"Mössbauer models are experimental", line),
                re.search(r"from spectrafit\.models\.moessbauer", line),
                re.search(r"lmfit/confidence\.py.*UserWarning", line),
                re.search(r"rel_change.*at iteration.*prob\(", line),
                re.search(r"warn\(errmsg\)", line),
                re.search(r"Bound reached with prob\(", line),
                re.search(r"spectrafit/report\.py.*FutureWarning", line),
                re.search(r"spectrafit/report\.py.*UserWarning", line),
                re.search(r"spectrafit/report/.*\.py.*UserWarning", line),  # Split report modules
                re.search(r"spectrafit/core/.*\.py.*UserWarning", line),  # Split core modules
                re.search(r"Downcasting object dtype arrays", line),
                re.search(r"return correl_matrix\.fillna", line),
                re.search(r"Error:.*No confidence interval could be calculated", line),
                re.search(r"self\.print_confidence_interval\(\)", line),
                re.search(
                    r"result, buffer, params = _extracted_gof_from_results\(", line
                ),
                re.search(r"## WARNING", line),
                re.search(r"##+$", line),  # Lines with only # characters
                re.search(r"Uncertainties could not be estimated", line),
                re.search(r"The parameter.*is at its (initial value|boundary)", line),
                re.search(r"uncertainties cannot be estimated!", line),
                re.search(r"spectrafit/models/regular\.py.*RuntimeWarning", line),
                re.search(r"invalid value encountered in", line),
                re.search(r"divide by zero encountered in", line),
                re.search(r"z = \(x - center", line),
                re.search(r"spectrafit/tools\.py.*UserWarning", line),
                re.search(r"Regression metric.*could not.*be calculated", line),
                re.search(r'self\.args\["regression_metrics"\]', line),
                re.search(r"Input contains NaN", line),
                re.search(r"return np\.array\(", line),
                line.strip() == "+",  # Filter out leading '+' markers
            ]
        ):
            continue

        filtered_lines.append(line)

    result = "\n".join(filtered_lines).strip()
    # Remove multiple consecutive newlines and return
    return re.sub(r"\n\s*\n", "\n", result)


def create_stdin(input_text: str) -> io.StringIO:
    """Create a StringIO object for stdin input in subprocess tests.

    Args:
        input_text: The text to provide as stdin input

    Returns:
        io.StringIO: A StringIO object containing the input text
    """
    return io.StringIO(input_text)
