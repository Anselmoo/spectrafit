!!! info "About the Converter API"

    The **Converter API** is a new feature in the v0.12.x release of
    `SpectraFit` with major focus on:

    1. Data Validation
    2. Settings Management

    In general, input and data files are converted to the internal data format,
    which are [dictionaries][1] for the input data and [pandas dataframes][2]
    for the data files. The Converter API is realized by using the
    [`ABC`-class][3] and the [`@abstractmethod`][4] decorator, while
    the File API is using the [pydantic][5] library.

### Meta Data Converter Class

::: spectrafit.plugins.converter

### Input and Output File Converter for object-oriented formats

::: spectrafit.plugins.file_converter

### Data Converter for rational data formats like CSV, Excel, etc.

::: spectrafit.plugins.data_converter

[1]: https://docs.python.org/3/tutorial/datastructures.html#dictionaries
[2]: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html
[3]: https://docs.python.org/3/library/abc.html#abc.ABC
[4]: https://docs.python.org/3/library/abc.html#abc.abstractmethod
[5]: https://pydantic-docs.helpmanual.io/
