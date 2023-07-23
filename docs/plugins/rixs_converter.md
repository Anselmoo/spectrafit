!!! abstract "About RIXS Converter"

    The `spectrafit-rixs-converter` allows to convert `SpectraFit` pkl files to a
    `json`, `toml`, `npy`, or `npz` file. The `npy` or `npz` files are the prefered
    format, since they are the most compact and fast to load. The `json` and `toml`
    files are also supported, but they are not as compact as the `npy` or `npz`
    files. The `json` and `toml` files are also slower to load, since they are not
    binary files.

The `spectrafit-rixs-converter` command line tool can be used like this:

```shell
➜ spectrafit-rixs-converter -h
usage: spectrafit-rixs-converter [-h] [-f {latin1,utf-8,utf-32,utf-16}] [-e {toml,npy,lock,json,npz}] [-ie INCIDENT_ENERGY] [-ee EMISSION_ENERGY] [-rm RIXS_MAP] [-m {sum,mean}]
                                 infile

Converter for 'SpectraFit' from pkl files to a JSON, TOML, or numpy file for RIXS-Visualizer.

positional arguments:
  infile                Filename of the pkl file to convert to JSON, TOML, or numpy.

options:
  -h, --help            show this help message and exit
  -f {latin1,utf-8,utf-32,utf-16}, --file-format {latin1,utf-8,utf-32,utf-16}
                        File format for the optional encoding of the pickle file. Default is 'latin1'.
  -e {toml,npy,lock,json,npz}, --export-format {toml,npy,lock,json,npz}
                        File extension for the export.
  -ie INCIDENT_ENERGY, --incident_energy INCIDENT_ENERGY
                        Name of the incident energy
  -ee EMISSION_ENERGY, --emission_energy EMISSION_ENERGY
                        Name of the emitted energy
  -rm RIXS_MAP, --rixs_map RIXS_MAP
                        Name of the RIXS map
  -m {sum,mean}, --mode {sum,mean}
                        Mode of the RIXS map post-processing, e.g. 'sum' or 'max'.Default is 'sum'.
```

Furthermore, the `spectrafit-rixs-converter` allows to sum or average the
`RIXS-Map`. For the conversion, the `spectrafit-rixs-converter` requires the
**three** keys for the `RIXS-Map`:

- `incident_energy` &rarr; the dictionary-key, which should to load the
  `incident_energy` from the pkl file.
- `emission_energy`&rarr; the dictionary-key, which should to load the
  `emission_energy` from the pkl file.
- `rixs_map`&rarr; the dictionary-key, which should to load the `rixs_map` from
  the pkl file.

The name of three options are also used as keys in the output file and cannot be
changed because it allows to load the data in the `RIXS-Visualizer` without
specifying the keys.

```python
from spectrafit.plugins.pkl_converter import PklConverter
from spectrafit.plugins.rixs_converter import RIXSConverter
from spectrafit.plugins.rixs_visualizer import RIXSApp

pkl_data = PklConverter.convert(
    infile="test.pkl",
)
rixs_data = RIXSConverter.convert(
    infile="test.pkl",
)
RIXSApp(**rixs_data).app_run()
```
