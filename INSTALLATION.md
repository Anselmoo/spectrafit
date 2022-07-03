`SpectraFit` can be currently only installed directly from the GitHub
repository. It is important that poetry is installed first, because the
`setup.py` is not explicitly defined, because it is indirectly available in the
`pyproject.toml` file.

## via GitHub

```terminal
pip install git+https://github.com/Anselmoo/SpectraFit.git
```

## via PyPi

```terminal
pip install spectrafit
```

## via Environment

To keep the system environment clean, the installation is done via the:

=== "PIPX"

    [PIPX][1] allows to install and run packages in a _isolated_ environment.

    _Installation_:

    ```terminal
    # install pipx for macOS
    brew install pipx
    # install pipx for Linux or Windows
    pip install pipx
    pipx install --upgrade pipx
    # install spectrafit for python 3.7
    pipx install spectrafit --python python3.7
    # install spectrafit for python 3.8
    pipx install spectrafit --python python3.8
    # install spectrafit for python 3.9
    pipx install spectrafit --python python3.9

    spectrafit --help
    ```

=== "Conda"

    [Conda][2] is a package manager for Python. It is a tool for installing and
    managing packages, environments, and virtualenvs. `SpectraFit` is available as [conda-forge][3].

    _Example_:

    ```terminal
    conda install -c conda-forge spectrafit

    spectrafit --help
    ```

_Result_:

```terminal

    usage: spectrafit [-h] [-o OUTFILE] [-i INPUT] [-ov] [-e0 ENERGY_START]
                    [-e1 ENERGY_STOP] [-s SMOOTH] [-sh SHIFT] [-c COLUMN COLUMN]
                    [-sep {	,,,;,:,|, ,s+}] [-dec {.,,}] [-hd HEADER]
                    [-g {0,1,2}] [-auto] [-np] [-v] [-vb {0,1,2}]
                    infile

    Fast Fitting Program for ascii txt files.

    ...
```

## via Docker

```docker
docker pull ghcr.io/anselmoo/spectrafit:latest
```

!!! caution "About Docker-Image"

    The docker-image of `SpectraFit` is still under development!

[1]: https://github.com/pypa/pipx
[2]: https://conda.io/docs/
[3]: https://anaconda.org/conda-forge/spectrafit
