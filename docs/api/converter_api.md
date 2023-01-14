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

### Pkl Converter for pickle files

::: spectrafit.plugins.pkl_converter

!!! info "About [pickle file][6] and the PklVisualizer"

    In addition to exploring the nested structure of the Python's
    [pickle file][6], the `PklVisualizer` provides two methods to visualize
    the data:

    1. As graph via [`networkx`][7] and [`matplotlib`][8]
    2. As json file with  used types

::: spectrafit.plugins.pkl_visualizer

[1]: https://docs.python.org/3/tutorial/datastructures.html#dictionaries
[2]: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html
[3]: https://docs.python.org/3/library/abc.html#abc.ABC
[4]: https://docs.python.org/3/library/abc.html#abc.abstractmethod
[5]: https://pydantic-docs.helpmanual.io/
[6]: https://docs.python.org/3/library/pickle.html
[7]: https://networkx.org
[8]: https://matplotlib.org
