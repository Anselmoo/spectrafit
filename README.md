# SpectraFit

poet:

- [Measurement of the Ligand Field Spectra of Ferrous and Ferric Iron Chlorides Using 2p3d RIXS](https://pubs.acs.org/doi/abs/10.1021/acs.inorgchem.7b00940)

Now, it is completely rewritten and is more flexible.

## Scope:

- Fitting of 2d data
- Using established and advanced solver methods
- Extensibility of the fitting function
- Guarantee traceability of the fitting results
- Saving all results for publications in a `CSV`-format
- Saving all results in a NoSQL-format (`JSON`) for project management
- Having an API interface for Graph-databases

## Installation:

via pip:

```shell
pip install spectrafit
```

## Usage:

`SpectraFit` needs as command line tool only two things:

1. The reference data, which should be fitted.
2. The input file, which contains the initial model.

As model files [json](https://en.wikipedia.org/wiki/JSON),
[toml](https://en.wikipedia.org/wiki/TOML), and
[yaml](https://en.wikipedia.org/wiki/YAML) are supported. By making use of the
python `**kwargs` feature, the input file can call most of the following
functions of [LMFIT](https://lmfit.github.io/lmfit-py/index.html). LMFIT is the
workhorse for the fit optimization, which is macro wrapper based on:

1. [NumPy](https://www.numpy.org/)
2. [SciPy](https://www.scipy.org/)
3. [uncertainties](https://pythonhosted.org/uncertainties/)

In case of `SpectraFit`, we have further extend the package by:

1. [Pandas](https://pandas.pydata.org/)
2. [Statsmodels](https://www.statsmodels.org/stable/index.html)
3. [numdifftools](https://github.com/pbrod/numdifftools)
4. [Matplotlib](https://matplotlib.org/) in combination with
   [Seaborn](https://seaborn.pydata.org/)

```shell
poetry run spectrafit data_file.txt input_file.json
```

```shell
poetry run spectrafit -h
Would you like to fit ...? Enter y/n: y
usage: spectrafit [-h] [-o OUTFILE] [-i INPUT] [-ov] [-disp] [-e0 ENERGY_START] [-e1 ENERGY_STOP] [-s SMOOTH] [-sh SHIFT] [-c COLUMN COLUMN] [-sep {    ,,,;,:,|, ,s+}] [-dec {.,,}] [-hd HEADER] [-np] [-v] [-vb] infile

Fast Fitting Program for ascii txt files.

positional arguments:
  infile                Filename of the specta data

optional arguments:
  -h, --help            show this help message and exit
  -o OUTFILE, --outfile OUTFILE
                        Filename for the export, default to set to input name.
  -i INPUT, --input INPUT
                        Filename for the input parameter, default to set to 'fitting_input.toml'.Supported fileformats are: '*.json', '*.yaml', and '*.toml'
  -ov, --oversampling   Oversampling the spectra by using factor of 5; default to False.
  -disp                 Hole or splitted Table on the Screen; default to 'hole'.
  -e0 ENERGY_START, --energy_start ENERGY_START
                        Starting energy in eV; default to start of energy.
  -e1 ENERGY_STOP, --energy_stop ENERGY_STOP
                        Ending energy in eV; default to end of energy.
  -s SMOOTH, --smooth SMOOTH
                        Number of smooth points for lmfit; default to 0.
  -sh SHIFT, --shift SHIFT
                        Constant applied energy shift; default to 0.0.
  -c COLUMN COLUMN, --column COLUMN COLUMN
                        Selected columns for the energy- and intensity-values; default to 0 for energy (x-axis) and 1 for intensity (y-axis).
  -sep {        ,,,;,:,|, ,s+}, --seperator {   ,,,;,:,|, ,s+}
                        Redefine the type of seperator; default to ' '.
  -dec {.,,}, --decimal {.,,}
                        Type of decimal seperator; default to '.'.
  -hd HEADER, --header HEADER
                        Selected the header for the dataframe; default to None.
  -np, --noplot         No plotting the spectra and the fit of `spectrafit`.
  -v, --version         Display the current version of `spectrafit`.
  -vb, --verbose        Display the initial configuration parameters as a dictionary.
```

## Documentation:

Please see the [extended documentation](https://anselmoo.github.io/spectrafit/)
for the full usage of `SpectraFit`.
