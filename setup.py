"""Setup SpectraFit."""
from setuptools import setup

packages = ["spectrafit", "spectrafit.test"]

package_data = {"": ["*"], "spectrafit.test": ["export/*", "import/*", "scripts/*"]}

install_requires = [
    "PyYAML>=6.0.0,<7.0.0",
    "corner>=2.2.1,<3.0.0",
    "dill>=0.3.4,<0.4.0",
    "emcee>=3.1.1,<4.0.0",
    "lmfit>=1.0.2,<2.0.0",
    "matplotlib>=3.4.2,<4.0.0",
    "numdifftools>=0.9.40,<0.10.0",
    "numpy>=1.21.1,<2.0.0",
    "openpyxl>=3.0.7,<4.0.0",
    "pandas>=1.3.0,<2.0.0",
    "scipy>=1.7.0,<2.0.0",
    "seaborn>=0.11.1,<0.12.0",
    "statsmodels>=0.13.1,<0.14.0",
    "tabulate>=0.8.9,<0.9.0",
    "toml>=0.10.2,<0.11.0",
    "tqdm>=4.62.3,<5.0.0",
]

entry_points = {
    "console_scripts": ["spectrafit = spectrafit.spectrafit:command_line_runner"]
}

with open("README.md", "r") as fh:
    long_description = fh.read()
setup_kwargs = {
    "name": "spectrafit",
    "version": "0.7.0",
    "description": "Fast fitting of 2D-Spectra with established routines",
    "long_description": long_description,
    "author": "Anselm Hahn",
    "author_email": "Anselm.Hahn@gmail.com",
    "maintainer": "Anselm Hahn",
    "maintainer_email": "Anselm.Hahn@gmail.com",
    "url": "https://pypi.org/project/spectrafit/",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "entry_points": entry_points,
    "python_requires": ">=3.7.1,<3.10",
}


setup(**setup_kwargs)
