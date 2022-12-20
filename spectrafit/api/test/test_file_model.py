"""Test the file model."""
import pytest

from spectrafit.api.file_model import DataFileAPI


def test_delimiter() -> None:
    """Test the delimiter validator."""
    data_file = DataFileAPI(
        skip_header=0,
        skip_footer=0,
        delimiter=" ",
    )
    assert data_file.delimiter == " "

    data_file = DataFileAPI(
        skip_header=0,
        skip_footer=0,
        delimiter="\t",
    )
    assert data_file.delimiter == "\t"

    data_file = DataFileAPI(
        skip_header=0,
        skip_footer=0,
        delimiter=",",
    )
    assert data_file.delimiter == ","

    data_file = DataFileAPI(
        skip_header=0,
        skip_footer=0,
        delimiter=";",
    )
    assert data_file.delimiter == ";"

    data_file = DataFileAPI(
        skip_header=0,
        skip_footer=0,
        delimiter="|",
    )
    assert data_file.delimiter == "|"

    data_file = DataFileAPI(
        skip_header=0,
        skip_footer=0,
        delimiter="s+",
    )
    assert data_file.delimiter == "s+"


def test_delimiter_error() -> None:
    """Test the delimiter validator."""
    with pytest.raises(ValueError) as excinfo:
        DataFileAPI(
            skip_header=0,
            skip_footer=0,
            delimiter="x",
        )

    assert "Delimiter not supported." in str(excinfo.value)


def test_comment_marker() -> None:
    """Test the comment marker validator."""
    data_file = DataFileAPI(
        skip_header=0,
        skip_footer=0,
        delimiter=" ",
        comment_marker="#",
    )
    assert data_file.comment_marker == "#"

    data_file = DataFileAPI(
        skip_header=0,
        skip_footer=0,
        delimiter=" ",
        comment_marker="%",
    )
    assert data_file.comment_marker == "%"

    data_file = DataFileAPI(
        skip_header=0,
        skip_footer=0,
        delimiter=" ",
        comment_marker=None,
    )
    assert data_file.comment_marker is None


def test_comment_marker_error() -> None:
    """Test the comment marker validator."""
    with pytest.raises(ValueError) as excinfo:
        DataFileAPI(
            skip_header=0,
            skip_footer=0,
            delimiter=" ",
            comment_marker="x",
        )

    assert "Comment marker not supported." in str(excinfo.value)
