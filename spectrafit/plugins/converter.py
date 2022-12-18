"""Abstract base class for the converter plugins."""
from abc import ABC
from abc import abstractmethod
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
        """
        pass

    @abstractmethod
    def convert(self, args: Dict[str, Any]) -> None:
        """Convert the input file to the output file.

        Args:
            args (Dict[str, Any]): The input file arguments as a dictionary with
                    additional information beyond the command line arguments.
        """
        pass

    @abstractmethod
    def __call__(self) -> None:
        """Call the converter plugin."""
        pass
