---
title: Using SpectraFit
description: Learn how to use SpectraFit effectively, from basic functionality to advanced features
tags:
  - usage
  - command-line
  - input-files
  - global-fitting
  - automatic-peak-detection
---

# Using SpectraFit

This guide covers both basic and advanced usage patterns for **SpectraFit**, including configuration options, input file formats, and special features.

## Standard Usage

!!! example "Basic Command"

    ```bash
      spectrafit data_file.txt input_file.json
    ```

    In case of the standard usage of **SpectraFit**, the following steps are necessary:

    1. Having a structured textfile available with or without header. Preferred fileformat can be `.csv` or `.txt`; however every file with a consistent separation is supported.

    ```text
    -1.600000000000000089e+00	0.000000000000000000e+00
    -1.583333333333333481e+00	3.891050583657595843e-03
    -1.566666666666666874e+00	3.973071404922200699e-03
    -1.550000000000000266e+00	4.057709648331829684e-03
    -1.533333333333333659e+00	4.145077720204749357e-03
    -1.516666666666667052e+00	4.235294117647067993e-03
    ```

    2. A wide range of pre-defined separators can be chosen: `,`, `;`, `:`, `|`, `\t`, `s+`, ` `

    3. Having an input file available as [JSON](https://en.wikipedia.org/wiki/JSON), [TOML](https://en.wikipedia.org/wiki/TOML), or [YAML](https://en.wikipedia.org/wiki/YAML). The input file must have at least the initial parameters for the peaks. More options are in the default settings not necessary, but can be activated by extending the objects in the input file.

    4. More command line arguments can be seen by activating the `-h` or `--help` flag.

    5. The attributes `minimizer` and `optimizer` must also be defined, because they control the optimization algorithm of lmfit. For information see [lmfit.mininizer](https://lmfit.github.io/lmfit-py/fitting.html?highlight=minimizer#module-lmfit.minimizer). The input file has to contain the following lines:

    ```json
    "parameters": {
        "minimizer": { "nan_policy": "propagate", "calc_covar": true },
        "optimizer": { "max_nfev": 1000, "method": "leastsq" }
    }
    ```

    6. Starting **SpectraFit** via:
    ```bash
    spectrafit data_file.txt input_file.json
    ```

!!! info "Peak definition in the input file"

    In the input file, the peaks must be defined as nested objects, as shown below:

    ```json
    "peaks": {
      "1": {
        "pseudovoigt": {
          "amplitude": {
            "max": 2,
            "min": 0,
            "vary": true,
            "value": 1
          },
          "center": {
            "max": 2,
            "min": -2,
            "vary": true,
            "value": 0
          },
          "fwhmg": {
            "max": 0.1,
            "min": 0.02,
            "vary": true,
            "value": 0.01
          },
          "fwhml": {
            "max": 0.1,
            "min": 0.01,
            "vary": true,
            "value": 0.01
          }
        }
      }
    }
    ```

    First, peaks have to be declared in the input file. Every peak contains a number as string; like "1" for peak #1. Next, the type of peak has to be defined in the input. The following peak types are available:

    - [x] [Gaussian](https://en.wikipedia.org/wiki/Gaussian_function)
    - [x] [Lorentzian](https://en.wikipedia.org/wiki/Cauchy_distribution) also known as Cauchy distribution
    - [x] [Voigt](https://en.wikipedia.org/wiki/Voigt_profile)
    - [x] [Pseudo Voigt](https://en.wikipedia.org/wiki/Voigt_profile#Pseudo-Voigt_approximation)
    - [x] Exponential
    - [x] [Powerlaw](https://en.wikipedia.org/wiki/Power_law) (also known as Log-parabola or just Power)
    - [x] Linear
    - [x] Constant
    - [x] [Error Function](https://en.wikipedia.org/wiki/Error_function)
    - [x] [Arcus Tangens](https://en.wikipedia.org/wiki/Inverse_trigonometric_functions)
    - [x] Logarithmic

    More information about the models, please see the [Models Documentation](../doc/models.md). For every model, the attributes have to be defined. The attributes are in case of the `pseudovoigt` model:

    1. **Amplitude**: The height or maximum value of the peak function
    2. **Center**: The position of the maximum along the x-axis
    3. **fwhmg**: The full width half maximum of the Gaussian distribution
    4. **fwhml**: The full width half maximum of the Lorentzian distribution

    Each attribute has sub-attributes, which are **always**:

    1. **max**: the maximum allowed value of the attribute
    2. **min**: the minimum allowed value of the attribute
    3. **vary**: if the attribute should be varied during the fit
    4. **value**: the initial value of the attribute

    At the moment, no default attributes are defined for the models, but this will come in a future release.

## Advanced Usage

In case of advanced usage of **SpectraFit**, the following features are available:

### Redefine the SpectraFit Settings

Define the settings in the input file as shown below:

```json
{
"settings": {
  "column": [0, 1],
  "decimal": ".",
  "energy_start": 0,
  "energy_stop": 8,
  "header": null,
  "infile": "spectrafit/test/rixs_fecl4.txt",
  "outfile": "fit_results",
  "oversampling": false,
  "separator": "\t",
  "shift": 0,
  "smooth": 0,
  "verbose": 1,
  "noplot": false
}
```

If the settings are pre-defined in the input file, the corresponding command line arguments will be automatically replaced with them.
If they are not defined, the command line arguments or their default values will be used. This allows for faster execution
of **SpectraFit** and also ensures consistency in the fitting procedure in case of larger studies. For the detailed
mechanism of overwriting the settings, please see the API documentation 
of [Command Line Module](../api/spectrafit_api.md#spectrafit.spectrafit.extracted_from_command_line_runner).

!!! warning "Datatype of columns for pandas.read_csv"

    According to the documentation of [`pandas.read_csv`][17], the datatype of
    can be both: `int` or `str`. The `in` is the default. In case of using
    the header the `str` is the mandatory.

### Define Project Details

Another advanced feature of **SpectraFit** is to define the fit as a project, which can become very useful for versioning the fitting project. For using **SpectraFit** as a project, the project details have to be defined as attributes. The attributes are `project_name`, `project_details`, and `keywords`, as shown in the snippet below:

```json
"fitting": {
    "description": {
      "project_name": "Template",
      "project_details": "Template for testing",
      "keywords": [
        "2D-Spectra",
        "fitting",
        "curve-fitting",
        "peak-fitting",
        "spectrum"
      ]
    }
```

All three attributes are strings, the `project_name` should ideally be a single name with no spaces. The `project_details` can be longer text, and the `keywords` should be a list of strings for tagging in a database.

### Tuning Minimizer and Optimizer and Activating Confidence Intervals

The input file can be extended with more parameters, which are optional in case of the confidence intervals. In general, the keywords of the lmfit `minimizer` function are supported. For more information please check the module [lmfit.mininizer](https://lmfit.github.io/lmfit-py/fitting.html?highlight=minimizer#module-lmfit.minimizer). The attributes have to be initialized with the keyword `parameters` as shown below:

```json
"parameters": {
  "minimizer": { "nan_policy": "propagate", "calc_covar": true },
  "optimizer": { "max_nfev": 1000, "method": "leastsq" },
  "report": { "min_correl": 0.0 },
  "conf_interval": {
    "p_names": null,
    "sigmas": null,
    "trace": true,
    "maxiter": 200,
    "verbose": 1,
    "prob_func": null
  }
}
```

!!! warning "About confidence interval calculations"

    The calculations of the confidence intervals depends on the number of
    features and `maxiter`. Consequently, the confidence interval calculations
    should be only used for the final fit to put the calculation time low.

### Using mathematical expressions

The input file can be further extended by `expressions`, which are evaluated during the fitting process. 
The `expressions` have to be defined as attributes of the `fitting` object in the input file. 
It can only contain mathematical constraints or dependencies between different `peaks`;
please compare the docs of [lmfit.eval](https://lmfit.github.io/lmfit-py/constraints.html) 
and [Expression Documentation](../doc/expression.md). The attributes are defined by the keyword 
`expr` followed by the string, which can contain any mathematical expression supported by Python.

!!! tip "About the importance of expressions"

    Using the `expr` attribute, the amplitude of the peak `2` can be defined as 1/3 of the amplitude of the peak `1`. In general, this expression mode is very useful in cases of fitting relative dependencies like the _L-edge X-ray Absorption Spectra_ (**L-XAS**), where relative dependencies between the _**L**<sub>3</sub>_ and _**L**<sub>2</sub>_ edge have to be defined.

    ```json
    "peaks": {
      "1": {
        "pseudovoigt": {
          "amplitude": {
            "max": 2,
            "min": 0,
            "vary": true,
            "value": 1
          },
          "center": {
            "max": 2,
            "min": -2,
            "vary": true,
            "value": 0
          },
          "fwhmg": {
            "max": 0.74,
            "min": 0.02,
            "vary": true,
            "value": 0.21
          },
          "fwhml": {
            "max": 0.74,
            "min": 0.01,
            "vary": true,
            "value": 0.21
          }
        }
      },
      "2": {
        "pseudovoigt": {
          "amplitude": {
            "expr": "pseudovoigt_amplitude_1 / 3"
          },
          "center": {
            "expr": "pseudovoigt_center_1 + 1.73"
          },
          "fwhmg": {
            "max": 0.5,
            "min": 0.02,
            "vary": true,
            "value": 0.01
          },
          "fwhml": {
            "max": 0.5,
            "min": 0.01,
            "vary": true,
            "value": 0.01
          }
        }
      },
      "3": {
        "constant": {
          "amplitude": {
            "max": 2,
            "min": 0.01,
            "vary": true,
            "value": 1
          }
        }
      },
      "4": {
        "gaussian": {
          "amplitude": {
            "max": 2,
            "min": 0,
            "vary": true,
            "value": 1
          },
          "center": {
            "expr": "pseudovoigt_center_2 + 0.35"
          },
          "fwhmg": {
            "max": 0.4,
            "min": 0.02,
            "vary": true,
            "value": 0.01
          }
        }
      }
    }
    ```

### Activating Global Fitting

The input file as well as the command line interface can be turned into the `global fitting` mode. The `global fitting` mode is useful when fitting several spectra with the same initial model. In case of using the `global fitting` **mode = 1**, the `fitting` object has to be defined in the same way like the local fitting model; via Input file

```json
{
  "settings": {
    "column": ["energy"],
    "decimal": ".",
    "header": 0,
    "infile": "data_global.csv",
    "outfile": "example_6",
    "oversampling": false,
    "separator": ",",
    "shift": 0.2,
    "smooth": false,
    "verbose": 1,
    "noplot": false,
    "global": 1,
    "autopeak": false
  }
}
```

or via Command Line.

```bash
spectrafit global_data.csv -i input.json -g 1
```

For more info please see the [Global Fitting Example](../examples/example6.md).

!!! danger "Correct Data Format for Global Fits"

    For the correct fitting the data file has to contain only spectra data;
    meaning `energy` and `intensity` columns. **No other columns are
    allowed!!**

### Activating Automatic Peak Detection for Fitting

The input file can be further extended by `autopeak`, which is used to automatically find the peaks in the data. The `autopeak` has to be defined as an attribute of the `setting` object in the input file or directly via command line:

```bash
spectrafit data.csv -i input.json -auto
```

The default peak model is `Gaussian`, but the `setting`-section in the input file allows switching to:

- [x] [gaussian](https://en.wikipedia.org/wiki/Normal_distribution)
- [x] [lorentzian](https://en.wikipedia.org/wiki/Cauchy_distribution)
- [x] [voigt](https://en.wikipedia.org/wiki/Voigt_profile)
- [x] [pseudovoigt](https://en.wikipedia.org/wiki/Voigt_profile#Pseudo-Voigt_approximation)

Furthermore, the _finding_ attributes of the `autopeak` are identical to the Scipy's [find_peaks](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html). The `autopeak` attributes have to be defined as follows:

```json
"autopeak": {
  "modeltype": "gaussian",
  "height": [0.0, 10],
  "threshold": [0.0, 10],
  "distance": 2,
  "prominence": [0.0, 1.0],
  "width": [0.0, 10],
  "wlen": 2,
  "rel_height": 1,
  "plateau_size": 0.5
}
```

## Configurations

In terms of the configuration of **SpectraFit**, configurations depend on the [lmfit package](https://lmfit.github.io/lmfit-py/fitting.html). Most of the provided features of `lmfit` can be used. The configurations can be called as attributes of `optimizer` and `minimizer` as shown in [Standard Usage](#standard-usage) step 5. For the individualization of the configuration, please use the keywords of `lmfit` [minimizer module](https://lmfit.github.io/lmfit-py/fitting.html?highlight=minimizer#module-lmfit.minimizer) and also check the **SpectraFit**'s [fitting routine](../api/spectrafit_api.md#spectrafit.spectrafit.fitting_routine).

## Input Files

<div class="grid cards" markdown>

- :material-code-json: **JSON**

  JavaScript Object Notation format, a lightweight data-interchange format

- :material-toml: **TOML**

  Tom's Obvious, Minimal Language format, a config file format for humans

- :material-language-yaml: **YAML**

  YAML Ain't Markup Language, a human-friendly data serialization standard

</div>

The input file of **SpectraFit** are dictionary-like objects. The input file can be one of these three types:

- [x] [JSON](https://en.wikipedia.org/wiki/JSON)
- [x] [TOML](https://en.wikipedia.org/wiki/TOML)
- [x] [YAML](https://en.wikipedia.org/wiki/YAML)

Especially, the `toml` and `yaml` files are very useful for the configuration of **SpectraFit** due to their structure and simplicity. [ConvertSimple](https://www.convertsimple.com) allows easily to convert between these three file types.

??? example "Reference Input in JSON"

    ```json
        {
          "settings": {
            "column": [0, 1],
            "decimal": ".",
            "energy_start": 0,
            "energy_stop": 8,
            "header": null,
            "infile": "spectrafit/test/rixs_fecl4.txt",
            "outfile": "fit_results",
            "oversampling": false,
            "noplot": false,
            "separator": "\t",
            "shift": 0,
            "smooth": 0,
            "verbose": 1
          },
          "fitting": {
            "description": {
              "project_name": "Template",
              "project_details": "Template for testing",
              "keywords": [
                "2D-Spectra",
                "fitting",
                "curve-fitting",
                "peak-fitting",
                "spectrum"
              ]
            },
            "parameters": {
              "minimizer": { "nan_policy": "propagate", "calc_covar": true },
              "optimizer": { "max_nfev": 1000, "method": "leastsq" },
              "report": { "min_correl": 0.0 },
              "conf_interval": {
                "p_names": null,
                "sigmas": null,
                "trace": true,
                "maxiter": 200,
                "verbose": 1,
                "prob_func": null
              }
            },
            "peaks": {
              "1": {
                "pseudovoigt": {
                  "amplitude": {
                    "max": 2,
                    "min": 0,
                    "vary": true,
                    "value": 1
                  },
                  "center": {
                    "max": 2,
                    "min": -2,
                    "vary": true,
                    "value": 0
                  },
                  "fwhmg": {
                    "max": 0.1,
                    "min": 0.02,
                    "vary": true,
                    "value": 0.01
                  },
                  "fwhml": {
                    "max": 0.1,
                    "min": 0.01,
                    "vary": true,
                    "value": 0.01
                  }
                }
              },
              "2": {
                "pseudovoigt": {
                  "amplitude": {
                    "max": 2,
                    "min": 0,
                    "vary": true,
                    "value": 1
                  },
                  "center": {
                    "max": 2,
                    "min": -2,
                    "vary": true,
                    "value": 0
                  },
                  "fwhmg": {
                    "max": 0.1,
                    "min": 0.02,
                    "vary": true,
                    "value": 0.01
                  },
                  "fwhml": {
                    "max": 0.1,
                    "min": 0.01,
                    "vary": true,
                    "value": 0.01
                  }
                }
              },
              "3": {
                "constant": {
                  "amplitude": {
                    "max": 2,
                    "min": 0.01,
                    "vary": true,
                    "value": 1
                  }
                }
              },
              "4": {
                "gaussian": {
                  "amplitude": {
                    "max": 2,
                    "min": 0,
                    "vary": true,
                    "value": 1
                  },
                  "center": {
                    "max": 2,
                    "min": -2,
                    "vary": true,
                    "value": 0
                  },
                  "fwhmg": {
                    "max": 0.1,
                    "min": 0.02,
                    "vary": true,
                    "value": 0.01
                  }
                }
              }
            }
          }
        }
    ```

## Jupyter Notebook Interface

The **SpectraFit** can be used in the [Jupyter Notebook](https://jupyter.org). First, the plugin has to be installed as described in [Installation](../interface/installation.md). To use the **SpectraFit** in the Jupyter Notebook, the **SpectraFit** has to be imported as follows:

```python
from spectrafit.plugins import notebook
```

Next, the **peak** definition has to be defined now as follows:

```python
initial_model = [
    {
        "pseudovoigt": {
            "amplitude": {"max": 2, "min": 0, "vary": True, "value": 1},
            "center": {"max": 2, "min": -2, "vary": True, "value": 0},
            "fwhmg": {"max": 0.1, "min": 0.02, "vary": True, "value": 0.01},
            "fwhml": {"max": 0.1, "min": 0.01, "vary": True, "value": 0.01},
        }
    },
    {
        "gaussian": {
            "amplitude": {"max": 2, "min": 0, "vary": True, "value": 1},
            "center": {"max": 2, "min": -2, "vary": True, "value": 0},
            "fwhmg": {"max": 0.1, "min": 0.02, "vary": True, "value": 0.01},
        }
    },
]
```

For generating the first fit via `spectrafit.plugins.notebook`, the following code has to be used:

```python
spf = SpectraFitNotebook(df=df, x_column="Energy", y_column="Noisy")
spf.solver_model(
    initial_model,
)
```

and to save the results as `toml` file, just save the `spf` object as follows:

```python
spf.generate_report
```

!!! info "About the Jupyter Interface"
The Jupyter interface is still under development and not yet fully functional. Furthermore, the peak definition changes a little bit - from a `dictionary` of `dictionary` to a `list` of `dictionaries`. As a consequence, the peak number is not needed anymore.

    Also the _global fitting routine_ is not yet implemented for the Jupyter interface.

More information about the Jupyter Notebook interface can be found in the [Jupyter Example](../examples/example9_1.ipynb) and the plugin documentation for [Jupyter-SpectraFit-Interface](../plugins/jupyter_interface.md) of **SpectraFit**.

The Jupyter Lab for the **SpectraFit** can be also started via the command line:

```bash
spectrafit-jupyter
```
