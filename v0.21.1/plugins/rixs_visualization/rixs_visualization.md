The `spectrafit-rixs-visualizer` allows to visualize RIXS data in a 2D plane.
The initial data can be a `json`, `toml`, `npy`, or `npz` file. The `npy` or
`npz` files are the prefered format, since they are the most compact and
fast to load. The `json` and `toml` files are also supported, but they are
not as compact as the `npy` or `npz` files. The `json` and `toml` files
are also slower to load, since they are not binary files.

```shell
    ➜ spectrafit-rixs-visualizer -h
    usage: spectrafit-rixs-visualizer [-h] infile

    `RIXS-Visualizer` is a simple RIXS plane viewer, which allows to visualize RIXS data in a 2D plane.

    positional arguments:
    infile      The input file. This can be a json, toml, npy, or npz file.

    options:
    -h, --help  show this help message and exit
```

The `spectrafit-rixs-visualizer` based in
