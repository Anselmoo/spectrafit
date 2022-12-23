"""Abstract base class for the converter plugins."""
from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import Any
from typing import Dict


class Converter(ABC):
    """Abstract base class for the converter plugin.

    The abstract base class is used to define the interface for the converter plugins:

    - get_args: Get the arguments from the command line.
    - convert: Convert the input file to the output file.
    - __call__: Call the converter plugin.

    Currently used for:

    - Convertion of the input file.
    - Convertion of the output file.
    """

    @abstractmethod
    def get_args(self) -> Dict[str, Any]:
        """Get the arguments from the command line.

        Returns:
            Dict[str, Any]: Return the input file arguments as a dictionary without
                 additional information beyond the command line arguments.

        Raises:
            ValueError: If the output file format is not supported.
        """

    @abstractmethod
    def convert(self, infile: Path, file_format: str) -> None:
        """Convert the input file to the target file format.

        It is an abstract method and must be implemented in the derived class.

        Args:
            infile (Path): Input file as a path object.
            file_format (str): Target file format.
        """

    @abstractmethod
    def __call__(self) -> None:
        """Call the converter plugin."""
