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

    For include the `jupyter` support, the following command can be used:

    ```terminal

    conda install -c conda-forge spectrafit-jupyter

    # To test
    python -c "from spectrafit.plugins.notebook import SpectraFitNotebook"
    ```

    Extended documentation about the installation of `SpectraFit` via conda can
    be found [here][7]. In general, the following command can be useful for
    working with conda:

    ```terminal
    conda config --add channels conda-forge
    conda config --set channel_priority strict
    ```

=== "Poetry"

    For installing `SpectraFit` via [Poetry][8], first `SpectraFit` has to be
    downloaded or cloned from the [GitHub repository][9]. Optionally, the
    `SpectraFit` repo has to be unpacked. Next, `poetry` has to be installed
    via `pip`:

    ```terminal
    pip install poetry
    ```

    or via `conda`:

    ```terminal
    conda install -c conda-forge poetry
    ```
    _Installation_:

    ```terminal
    poetry install -E jupyter
    ```
    _Usage_:

    ```terminal
    poetry run spectrafit --help
    ```

    or using the `poetry shell`:

    ```terminal
    poetry shell
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

### Plugins

The `SpectraFit` package is designed to be extended by plugins. Currently
available plugins are:

- [x] Input-File-Converter (_built-in_)
- [x] Jupyter-Notebook-Interface (`pip install spectrafit[jupyter]`)
- [ ] Elastic-Line-Alignment (_in progress_)

## via Docker

!!! info "About Docker-Image"

    Since version 0.12.0, the `SpectraFit` package is available as a
    [Docker-Image][4]. The Docker-Image is based on an modified
    [Jupyter-Scipy-Image][5] and contains the `SpectraFit` package and
    the [Jupyter-Notebook][6] interface.

    The Docker-Image can be installed and used via:

    ```terminal
    docker pull ghcr.io/anselmoo/spectrafit:latest
    docker run -it -p 8888:8888 spectrafit:latest
    ```

    or just via:

    ```terminal
    docker run -it -p 8888:8888 ghcr.io/anselmoo/spectrafit:latest
    ```


    ![Docker-Image](https://github.com/Anselmoo/spectrafit/blob/9094da4472db889d50652d4ded870d42dd0ed559/docs/images/docker.png?raw=true)

    To include the _home directory_ of the host system, the following command can
    be used:

    ```terminal
    docker run -it -p 8888:8888 -v $HOME:/home/user/work spectrafit:latest
    ```

    or via:

    ```terminal
    docker run -it -p 8888:8888 -v $HOME:/home/user/work ghcr.io/anselmoo/spectrafit:latest
    ```

[1]: https://github.com/pypa/pipx
[2]: https://conda.io/docs/
[3]: https://anaconda.org/conda-forge/spectrafit
[4]: https://github.com/Anselmoo/spectrafit/pkgs/container/spectrafit
[5]: https://github.com/jupyter/docker-stacks/blob/main/scipy-notebook/Dockerfile
[6]: ../../plugins/jupyter-spectrafit-interface
[7]: https://github.com/conda-forge/spectrafit-feedstock
[8]: https://python-poetry.org/docs/
[9]: https://github.com/Anselmoo/spectrafit/
