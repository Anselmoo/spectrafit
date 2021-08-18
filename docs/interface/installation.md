`SpectraFit` can be currently only installed directly from the GitHub
repository. It is important that poetry is installed first, because the
`setup.py` is not explicitly defined, because it is indirectly available in the
`pyproject.toml` file.

```shell
poetry add git+https://github.com/Anselmoo/SpectraFit.git
```

## Coming soon:

### via PyPi:

```shell
pip install spectrafit
```

### via conda:

```shell
conda install spectrafit
```

### via Docker:

```docker
docker run --name=spectrafit -v /path/to/spectrafit/:/spectrafit -p 8888:8888 -d spectrafit/spectrafit
```
