With the command `spectrafit-data-converter` data files can be converted to
`CSV` or [pandas dataframes][1]. Currently, the following data formats are

- [x] The [`Athena`][2] data format
- [x] Text files with a header and a data seperator by space or tab
- [ ] More formats are coming soon

```shell
➜ spectrafit-data-converter -f ATHENA -h
  usage: spectrafit-data-converter [-h] [-f {ATHENA,TXT}] [-e {txt,csv,out,dat}] infile

  Converter for 'SpectraFit' from data files to CSV files.

  positional arguments:
    infile                Filename of the data file to convert.

  options:
    -h, --help            show this help message and exit
    -f {ATHENA,TXT}, --file-format {ATHENA,TXT}
                          File format for the conversion.
    -e {txt,csv,out,dat}, --export-format {txt,csv,out,dat}
                          File format for the export.
```

!!! example "From ATHENA to CSV"

    To convert a data file from the `Athena` format to `CSV` use:

    ```shell
    spectrafit-data-converter Examples/athena.nor -f ATHENA
    ```

    The original data file looks like this, but can contains more rows:

    ```txt
      # XDI/1.0 Demeter/0.9.26
      # Demeter.output_filetype: multicolumn normalized mu(E)
      # Element.symbol: V
      # Element.edge: K
      # Column.1: energy eV
      # Column.2: JZP-4-merged
      #------------------------
      #  energy  JZP-4-merged
        5263.8492       0.12737417
        5273.8501       0.10231758
        5283.8503       0.81114410E-01
        5293.8492       0.61588687E-01
        5303.8493       0.47158833E-01
        5313.8497       0.35236642E-01
        5323.8502       0.25314870E-01
        5333.8506       0.18438437E-01
        5343.8501       0.12077480E-01
    ```

    will be converted to:

    ```csv
      energy,JZP-4-merged
      5263.8492,0.12737417
      5273.8501,0.10231758
      5283.8503,0.08111441
      5293.8492,0.06158869
      5303.8493,0.04715883
      5313.8497,0.03523664
      5323.8502,0.02531487
      5333.8506,0.01843844
      5343.8501,0.01207748
    ```

[1]:
  https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html
[2]: https://bruceravel.github.io/demeter/documents/Athena/other/plugin.html
