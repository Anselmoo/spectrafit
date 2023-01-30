"""Transform the raw pkl data into a CSV files."""

import argparse
import gzip
import pickle

from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import numpy as np

from spectrafit.plugins.converter import Converter
from spectrafit.tools import pkl2any
from spectrafit.tools import pure_fname


pkl_gz = "pkl.gz"
choices_fformat = {"latin1", "utf-8", "utf-16", "utf-32"}
choices_export = {"npy", "npz", "pkl", pkl_gz}


class ExportData:
    """Export the data to a file.

    !!! info "General information"

        The data is exported to a file. The file format is determined by the file
        extension of the output file. The supported file formats are:

        -[x] npy
        -[x] npz
        -[x] pkl
        -[x] pkl.gz

        Classical file formats like `CSV`, `JSON`, `TOML`, etc. are not supported.
        In case of `CSV`, the conversion from unstructured data to a structured
        format is not trivial. In case of `JSON` and `TOML`, the data is not
        the conversion from numpy arrays to lists is very costly. Therefore, the
        data is exported to a pickly file as the preferred format.

    !!! warning "About NumPy"

        The data is exported to a NumPy file can cause some challenge for the
        loading of the data. The data is exported as a dictionary with numpy
        as numpy arrays. The data can be loaded with the following code:

        ```python
        import numpy as np

        data = np.load("data.npy", allow_pickle=True).item()
        ```
    """

    def __init__(self, data: Dict[str, Any], fname: Path, export_format: str) -> None:
        """Export the data to a file.

        Args:
            data (Dict[str, Any]): The data to export.
            fname (Path): The filename of the output file.
            export_format (str): The file format of the output file.
        """
        self.data = data
        self.fname = fname.with_suffix(f".{export_format}")
        self.export_format = export_format

    def __call__(self) -> None:
        """Export the data to a file."""
        if self.export_format in {"npy", "npz"}:
            self.to_numpy()
        elif self.export_format in {"pkl", pkl_gz}:
            self.to_pickle()

    def to_numpy(self) -> None:
        """Export the data to a numpy file."""
        _data: Any = self.data
        if self.export_format.lower() == "npy":
            np.save(self.fname, _data)
        elif self.export_format.lower() == "npz":
            np.savez(self.fname, data=_data)

    def to_pickle(self) -> None:
        """Export the data to a pickle file."""
        if self.export_format.lower() == "pkl":
            with open(self.fname, "wb") as f:
                pickle.dump(self.data, f)
        elif self.export_format.lower() == pkl_gz:
            with gzip.open(self.fname, "wb") as f:
                pickle.dump(self.data, f)

    @staticmethod
    def numpy2list(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert the arrays of list dictionaries to a list of dictionaries with list.

        Args:
            data (List[Dict[str, Any]]): The data to convert.

        Returns:
            List[Dict[str, Any]]: The converted data.
        """
        return [
            {k: v.tolist() for k, v in d.items() if isinstance(v, np.ndarray)}
            for d in data
        ]


class PklConverter(Converter):
    """Convert pkl data to a CSV files.

    !!! info "General information"

        The pkl data is converted to a CSV file. The CSV file is saved in the same
        directory as the input file. The name of the CSV file is the same as the
        input file with the suffix `.csv` and prefixed with the name of the
        'major' keys in the pkl file. Furthermore, a graph of the data is optionally
        saved as a PDF file to have a visual representation of the data structure.

    !!! info "Supported file formats"

        Currently supported file formats:

        -[x] pkl
        -[x] pkl.gz
        -[x] ...

    """

    def get_args(self) -> Dict[str, Any]:
        """Get the arguments from the command line.

        Returns:
            Dict[str, Any]: Return the input file arguments as a dictionary without
                additional information beyond the command line arguments.
        """
        parser = argparse.ArgumentParser(
            description="Converter for 'SpectraFit' from pkl files to CSV files."
        )
        parser.add_argument(
            "infile",
            type=Path,
            help="Filename of the pkl file to convert.",
        )
        parser.add_argument(
            "-f",
            "--file-format",
            help="File format for the optional encoding of the pickle file."
            " Default is 'latin1'.",
            type=str,
            default="latin1",
            choices=choices_fformat,
        )
        parser.add_argument(
            "-e",
            "--export-format",
            help="File format for export of the output file. Default is 'pkl'.",
            type=str,
            default="pkl",
            choices=choices_export,
        )
        return vars(parser.parse_args())

    @staticmethod
    def convert(infile: Path, file_format: str) -> Dict[str, Any]:
        """Convert the input file to the output file.

        Args:
            infile (Path): The input file of the as a path object.
            file_format (str): The output file format.

        Returns:
            Dict[str, Any]: The data as a dictionary, which can be a nested dictionary
        """

        def _convert(
            data_values: Dict[str, Any], _key: Optional[List[str]] = None
        ) -> List[Dict[str, Any]]:
            """Convert the data to a list of dictionaries.

            The new key is the old key plus all the subkeys. The new value is the
            value of the subkey if the value is an instance of an array.

            For avoiding `pylint` errors, the `_key` argument is set to `None` by
            default and is set to an empty list if it is `None`. This is done to
            avoid the `pylint` error `dangerous-default-value`. The `_key` argument
            is used to keep track of the keys of the nested dictionary. Furthermore,
            the `_key` argument is used to create the new key for the new dictionary.

            Finally, the new dictionary is appended to the list of dictionaries.

            Args:
                data_values (Dict[str, Any]): The data as a dictionary.

            Returns:
                List[Dict[str, Any]]: The data as a list of dictionaries.
            """
            data_list = []
            if _key is None:
                _key = []
            for key, value in data_values.items():
                if isinstance(value, dict):
                    _key.append(str(key))
                    data_list.extend(_convert(value, _key))
                    _key.pop()
                elif isinstance(value, np.ndarray):
                    data_list.append({"_".join(_key + [key]): value})
            return data_list

        data_dict = {}
        for key, value in pkl2any(infile, file_format).items():
            if isinstance(value, dict):
                data_dict[key] = _convert(value)
        return data_dict

    def save(self, data: Any, fname: Path, export_format: str) -> None:
        """Save the converted pickle data to a file.

        Args:
            data (Any): The converted nested dictionary of the pkl data.
            fname (Path): The filename of the output file.
            export_format (str): The file format of the output file.

        Raises:
            ValueError: If the export format is not supported.
        """
        if export_format.lower() not in choices_export:
            raise ValueError(f"Unsupported file format '{export_format}'.")

        fname = pure_fname(fname)

        for key, value in data.items():
            _fname = Path(f"{fname}_{key}").with_suffix(f".{export_format}")
            ExportData(data=value, fname=_fname, export_format=export_format)()

    def __call__(self) -> None:
        """Run the converter."""
        args = self.get_args()
        data = self.convert(args["infile"], args["file_format"])
        self.save(data, args["infile"], args["export_format"])


def command_line_runner() -> None:
    """Run the command line script."""
    PklConverter()()
