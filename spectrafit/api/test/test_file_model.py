"""Test the file model."""
import pytest

from spectrafit.api.file_model import DataFileAPI


def test_delimiter_space() -> None:
    """Test the delimiter validator."""
    data_file = DataFileAPI(
        skiprows=0,
        skipfooter=0,
        delimiter=" ",
        file_suffixes=[".txt"],
    )
    assert data_file.delimiter == " "


def test_delimiter_tab() -> None:
    """Test the delimiter validator for tab separation."""
    data_file = DataFileAPI(
        skiprows=0,
        skipfooter=0,
        delimiter="\t",
        file_suffixes=[".txt"],
    )
    assert data_file.delimiter == "\t"


def test_delimiter_comma() -> None:
    """Test the delimiter validator for comma separation."""
    data_file = DataFileAPI(
        skiprows=0,
        skipfooter=0,
        delimiter=",",
        file_suffixes=[".txt"],
    )
    assert data_file.delimiter == ","


def test_delimiter_semicolon() -> None:
    """Test the delimiter validator for semicolon separation."""
    data_file = DataFileAPI(
        skiprows=0,
        skipfooter=0,
        delimiter=";",
        file_suffixes=[".txt"],
    )
    assert data_file.delimiter == ";"


def test_delimiter_pipe() -> None:
    """Test the delimiter validator for pipe separation."""
    data_file = DataFileAPI(
        skiprows=0,
        skipfooter=0,
        delimiter="|",
        file_suffixes=[".txt"],
    )
    assert data_file.delimiter == "|"


def test_delimiter_regex() -> None:
    """Test the delimiter validator for regex separation."""
    data_file = DataFileAPI(
        skiprows=0,
        skipfooter=0,
        delimiter=r"\s+",
        file_suffixes=[".txt"],
    )
    assert data_file.delimiter == r"\s+"


def test_delimiter_regex_error() -> None:
    """Test the delimiter validator for regex error."""
    with pytest.raises(ValueError):
        DataFileAPI(
            skiprows=0,
            skipfooter=0,
            delimiter=r"\s",
            file_suffixes=[".txt"],
        )


def test_comment() -> None:
    """Test the comment marker validator."""
    data_file = DataFileAPI(
        skiprows=0,
        skipfooter=0,
        delimiter=" ",
        comment="#",
        file_suffixes=[".txt"],
    )
    assert data_file.comment == "#"

    data_file = DataFileAPI(
        skiprows=0,
        skipfooter=0,
        delimiter=" ",
        comment="%",
        file_suffixes=[".txt"],
    )
    assert data_file.comment == "%"

    data_file = DataFileAPI(
        skiprows=0,
        skipfooter=0,
        delimiter=" ",
        comment=None,
        file_suffixes=[".txt"],
    )
    assert data_file.comment is None


def test_comment_error() -> None:
    """Test the comment marker validator for error."""
    with pytest.raises(ValueError):
        DataFileAPI(
            skiprows=0,
            skipfooter=0,
            delimiter=" ",
            comment="x",
            file_suffixes=[".txt"],
        )
