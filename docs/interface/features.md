## Statistic

### Pre-Analysis

!!! info "Initial Data Analysis"

    As part of the fitting procedure in **SpectraFit**, the initial data will be first
    analyzed based on standard statistics to provide baseline insights.

    As part of the fitting procedure in **SpectraFit**, the initial data will be first
    analyzed based on standard statistics. The standard statistics includes:

    - [x] Number of points in the data array
    - [x] The mean value of the data array
    - [x] The standard deviation of the data array
    - [x] The minimum value of the data array
    - [x] The maximum value of the data array
    - [x] The percentage based contribution of the data array

    The evaluation of the standard statistics is performed via [pandas-describe][1];
    see also the [Command Line Interface][2] for more information in the
    API-section.

??? example "Pre-Analysis Example"

    |       |      0 |      1 |
    | :---- | -----: | -----: |
    | count | 611.00 | 611.00 |
    | mean  |   3.48 |   0.06 |
    | std   |   2.94 |   0.12 |
    | min   |  -1.60 |   0.00 |
    | 10%   |  -0.58 |   0.00 |
    | 20%   |   0.43 |   0.00 |
    | 30%   |   1.45 |   0.00 |
    | 40%   |   2.47 |   0.01 |
    | 50%   |   3.48 |   0.02 |
    | 60%   |   4.50 |   0.03 |
    | 70%   |   5.52 |   0.06 |
    | 80%   |   6.53 |   0.10 |
    | 90%   |   7.55 |   0.14 |
    | max   |   8.57 |   1.00 |

### Fit Statistic

!!! tip "Statistical Insights"
    The fit statistics provide crucial information about the quality of your model fit.
    Pay special attention to reduced chi-square values and information criteria when
    comparing different models. See the [Statistics Documentation](../doc/statistics.md#standard-statistics) for more details.

The fit statistic provides standard statistics of the data based on the [fit
report module][3] of lmfit. So following standard insights are provided by
lmfit:

- used fitting method
- number of evaluated function
- number of data points
- number of variables
- chi-square
- reduced chi-square
- [Akaike info criteria][4] is an estimator of prediction error
- [Bayesian info criteria][5] is an estimator of model validity

This information will be also saved and extended in the `json`-output. For a comprehensive overview of all statistical measures, including regression metrics, please refer to the [Statistics Documentation](../doc/statistics.md).

### Variable Analysis

In addition to [Fit Statistic][6], the variable analysis of `lmfit` provides a
more detail look on the fitting result of each peak's attribute. In case of a
[pseudovoigt distribution][7], the attributes consists of:

1. Amplitude
2. Center
3. Full Width at Half Maximum of the gaussian distribution
4. Full Width at Half Maximum of the lorentzian distribution

And every of these attributes has to be analyzed according to the:

1. Best Value
2. Initial Value
3. Absolute Error
4. Relative Error

??? example "Variable Analysis Example"

    [Download the full variable analysis table](../assets/data/variable_analysis_example.csv)

    | variable name           |       value | absolute error | relative error | init value |  model value |
    | :---------------------- | ----------: | -------------: | -------------: | ---------: | -----------: |
    | pseudovoigt_amplitude_1 |  0.16403603 | +/- 0.28617283 |        174.46% |          1 |     0.164036 |
    | pseudovoigt_center_1    |  0.03500058 | +/- 0.07534815 |        215.28% |          0 |   0.03500058 |
    | pseudovoigt_fwhmg_1     |  0.06876795 | +/- 0.04790400 |         69.66% |       0.02 |   0.06876795 |
    | pseudovoigt_fwhml_1     |  0.09252389 | +/- 0.03757126 |         40.61% |       0.01 |   0.09252389 |
    | ...                     |         ... |            ... |            ... |        ... |          ... |

### Correlation Analysis

The [Variable Analysis][8] will be completed by the two kinds of correlation
analysis. In the first case, the correlation analysis of `lmfit` is used to
analyze every peak's attributes against each other. In contrast to the default
values of `lmfit`, the threshold of the correlation analysis is set to 0.0;
please check also the [Performing Fits and Analyzing Outputs in `lmfit`][9]

In the second case, the linear correlation analysis of
[`pandas-module corr`][10] is used to generally analyze the fit results in the
concept of the dataframes. In more detail, a linear pearson correlation will be
performed between each components in the dataframe, which normally consists of:

1. Energy (1D-array)
2. Intensity (1D-array)
3. Residual (1D-array)
4. Fit (1D-array)
5. Single components of the fit as multiple variables (1D-array)

This analysis should give insights, if the fit model can be further simplified
as a result of a superposition of the components, see also the Wikipedia article
about [Correlation][17].

??? example "Overall Correlation Analysis"

    |               | energy | intensity | residual |   fit | pseudovoigt_1 | pseudovoigt_2 | constant_3 | gaussian_4 |
    | :------------ | -----: | --------: | -------: | ----: | ------------: | ------------: | ---------: | ---------: |
    | energy        |   1.00 |     -0.31 |     0.12 | -0.23 |         -0.21 |         -0.25 |        nan |      -0.10 |
    | intensity     |  -0.31 |      1.00 |     0.05 |  0.90 |          0.88 |          0.85 |        nan |       0.61 |
    | residual      |   0.12 |      0.05 |     1.00 |  0.47 |          0.47 |          0.39 |        nan |       0.39 |
    | fit           |  -0.23 |      0.90 |     0.47 |  1.00 |          0.98 |          0.92 |        nan |       0.71 |
    | pseudovoigt_1 |  -0.21 |      0.88 |     0.47 |  0.98 |          1.00 |          0.85 |        nan |       0.65 |
    | pseudovoigt_2 |  -0.25 |      0.85 |     0.39 |  0.92 |          0.85 |          1.00 |        nan |       0.56 |
    | constant_3    |    nan |       nan |      nan |   nan |           nan |           nan |        nan |        nan |
    | gaussian_4    |  -0.10 |      0.61 |     0.39 |  0.71 |          0.65 |          0.56 |        nan |       1.00 |

### Confidence Intervals

`SpectraFinder` provides the possibility to calculate the [confidence
intervals][11]. This is an optional feature in `SpectraFinder` provided by the
[`lmfit`][12] package to further investigated the statistical legality of the
fit.

??? example "Confidence Intervals"

    |                         | 99.73% | 95.45% | 68.27% |   _BEST_ | 68.27% | 95.45% | 99.73% |
    | :---------------------- | -----: | -----: | -----: | -------: | -----: | -----: | -----: |
    | pseudovoigt_amplitude_1 |   -inf |   -inf |   -inf |  0.16404 |   +inf |   +inf |   +inf |
    | pseudovoigt_center_1    |   -inf |   -inf |   -inf |  0.03500 |   +inf |   +inf |   +inf |
    | pseudovoigt_fwhmg_1     |   -inf |   -inf |   -inf |  0.06877 |   +inf |   +inf |   +inf |
    | pseudovoigt_fwhml_1     |   -inf |   -inf |   -inf |  0.09252 |   +inf |   +inf |   +inf |
    | pseudovoigt_amplitude_2 |   -inf |   -inf |   -inf |  0.09740 |   +inf |   +inf |   +inf |
    | pseudovoigt_center_2    |   -inf |   -inf |   -inf | -0.01805 |   +inf |   +inf |   +inf |
    | pseudovoigt_fwhmg_2     |   -inf |   -inf |   -inf |  0.04334 |   +inf |   +inf |   +inf |
    | pseudovoigt_fwhml_2     |   -inf |   -inf |   -inf |  0.09990 |   +inf |   +inf |   +inf |
    | constant_amplitude_3    |   -inf |   -inf |   -inf |  0.03677 |   +inf |   +inf |   +inf |
    | gaussian_amplitude_4    |   -inf |   -inf |   -inf |  0.01411 |   +inf |   +inf |   +inf |
    | gaussian_center_4       |   -inf |   -inf |   -inf |  0.00079 |   +inf |   +inf |   +inf |
    | gaussian_fwhmg_4        |   -inf |   -inf |   -inf |  0.04893 |   +inf |   +inf |   +inf |

!!! Danger "About the trace in confidence intervals"

    The trace in the confidence intervals is the sum of the weights of the
    diagonal elements of the confidence matrix. lmfit allows calculating the
    trace of the confidence matrix. The export is a nested dictionary in a
    `dictionary`, where the arrays are saved as `array objects` and not as a
    `list`. The problem is that these `arrays` are not pickable,
    so they cannot be saved in a `json`-file. So please never use **trace!=True**
    in the input file.

## Plotting

For the plotting of the results, the `SpectraFinder` provides the possibility to
plot both the fit results and the residuals. A detail description of the
plotting options is available in the [API-section][13].

## Saving the Results as CSV- and JSON-files

`SpectraFinder` automatically saves the **fit results and the statistics** in
file format. By default, the results starts with `fit_results_*.*`, but can be
individually labeled via `-o` command or in the input file. Furthermore, four
different types of output files will be generated

1.  Fit results as `*_fit.csv` file, which combines the original data with the
    fit, residuals, and the single contribution.
2.  Fit errors as `*_errors.csv` file, which contains the value and fit errors
    for each parameter. The saved report is identically to printed report of
    [Variable Analysis][8].
3.  Fit correlation as `*_correlation.csv` file, which contains the correlation
    analysis of the dataframe. The saved report is identically to printed report
    of [Correlation Analysis][14].
4.  Fit summary as `*_summary.json` file, which contains all results of the fit
    _project_ including the meta-data. The overall goal is to save the results
    in a NoSQL-format, so that every fit becomes an unique fitting-project.

    !!! info "A closer look on the output file format"

        The fitting-project consists of the following parts:

         1. The input parameter including the file-name of the original data.
             ```json
             "infile": "reference_data.txt",
             "outfile": "fit_results",
             "input": "spectrafit/test/test_input_2.json",
             "oversampling": false,
             "energy_start": 0,
             "energy_stop": 8,
             "smooth": 0,
             "shift": 0,
             "column": [
                 0,
                 1
             ],
             "separator": "\t",
             "decimal": ".",
             "header": null,
             "noplot": true,

             "verbose": 1,
             ```
         2. The project-specific meta-data.
              ```json
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
             ```
             The meta-data will be automatically extended by **timestamp**, name
             of the user (**username**), name of system of the user
             (**system**), and unique ID. For getting the username and the name
             of the used system, the built-in function [`getpass.getuser()`][19]
             and [`socket.gethostname()`][18] are used.
             ```json
             {
             "timestamp": "2021-08-22 12:33:26",
             "ID": "89b1a4ef-320a-4ac0-80da-e8d946b00e13",
             "host_info": "e74490816920d147adc2315b45c4c6ce05e99ae9e09e34d2a263e2e9da861ffd",
             "used_version": "0.3.0",
             }
             ```
         3. The `lmfit`-settings.
             ```json
               "minimizer": {
                     "nan_policy": "propagate",
                     "calc_covar": true
                 },
               "optimizer": {
                     "max_nfev": 1,
                     "method": "leastsq"
                 },
               "report": {
                     "min_correl": 0.0
                 },
             ```
         4. The initial peak definitions.
         5. The results are saved as dictionary-list and can be imported by
         [pandas.DataFrame.from_dict][15]. For example:
        ```json
            "data_statistic": {
            "0": {
                "count": 611.0,
                "mean": 3.483333333333315,
                "std": 2.942079763251376,
                "min": -1.6,
                "10%": -0.5833333333333369,
                "20%": 0.433333333333326,
                "30%": 1.4499999999999895,
                "40%": 2.466666666666652,
                "50%": 3.483333333333315,
                "60%": 4.499999999999979,
                "70%": 5.516666666666641,
                "80%": 6.533333333333305,
                "90%": 7.549999999999968,
                "max": 8.566666666666633
            },
            "1": {
                "count": 611.0,
                "mean": 0.0603440425183391,
                "std": 0.12314108298811662,
                "min": 0.0,
                "10%": 0.00015819900201364986,
                "20%": 0.0015617780277680387,
                "30%": 0.0045243182103807894,
                "40%": 0.010958904109588984,
                "50%": 0.016245522651620947,
                "60%": 0.02770646393851211,
                "70%": 0.059617904082309055,
                "80%": 0.10112180177353332,
                "90%": 0.13932494130255624,
                "max": 1.0
            }
        },
        ```
        becomes again the result of [pre-analysis][16]:

        |       |      0 |      1 |
        | :---- | -----: | -----: |
        | count | 611.00 | 611.00 |
        | mean  |   3.48 |   0.06 |
        | std   |   2.94 |   0.12 |
        | min   |  -1.60 |   0.00 |
        | 10%   |  -0.58 |   0.00 |
        | 20%   |   0.43 |   0.00 |
        | 30%   |   1.45 |   0.00 |
        | 40%   |   2.47 |   0.01 |
        | 50%   |   3.48 |   0.02 |
        | 60%   |   4.50 |   0.03 |
        | 70%   |   5.52 |   0.06 |
        | 80%   |   6.53 |   0.10 |
        | 90%   |   7.55 |   0.14 |
        | max   |   8.57 |   1.00 |

        This is the one of the universal concepts of `SpectraFit` to to keep the
        results of the fit in a universal format, so that it can be switch
        between dictionary representation and dataframe representation.

??? example "Fit summary in JSON format"

    This is an extended example of the fit summary in JSON format to highlight
    the complexity of the fitting procedure.
    ```json
    {
      "infile": "spectrafit/test/rixs_fecl4.txt",
      "outfile": "fit_results",
      "input": "spectrafit/test/fitting_input.json",
      "oversampling": false,
      "energy_start": 0,
      "energy_stop": 8,
      "smooth": 0,
      "shift": 0,
      "column": [0, 1],
      "separator": "\t",
      "decimal": ".",
      "header": null,
      "noplot": true,

      "verbose": 1,
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
      "minimizer": {
        "nan_policy": "propagate",
        "calc_covar": true
      },
      "optimizer": {
        "max_nfev": 1000,
        "method": "leastsq"
      },
      "report": {
        "min_correl": 0.0
      },
      "conf_interval": {
        "p_names": null,
        "sigmas": null,
        "trace": false,
        "maxiter": 200,
        "verbose": 1,
        "prob_func": null
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
      },
      "timestamp": "2021-08-19 21:08:57",
      "ID": "ce43d306-43e4-4350-9f09-fd1b13064f39",
      "host_info": "username",
      "host_info": "e74490816920d147adc2315b45c4c6ce05e99ae9e09e34d2a263e2e9da861ffd",
      "used_version": "0.2.0",
      "data_statistic": {
        "0": {
          "count": 611.0,
          "mean": 3.483333333333315,
          "std": 2.942079763251376,
          "min": -1.6,
          "10%": -0.5833333333333369,
          "20%": 0.433333333333326,
          "30%": 1.4499999999999895,
          "40%": 2.466666666666652,
          "50%": 3.483333333333315,
          "60%": 4.499999999999979,
          "70%": 5.516666666666641,
          "80%": 6.533333333333305,
          "90%": 7.549999999999968,
          "max": 8.566666666666633
        },
        "1": {
          "count": 611.0,
          "mean": 0.0603440425183391,
          "std": 0.12314108298811662,
          "min": 0.0,
          "10%": 0.00015819900201364986,
          "20%": 0.0015617780277680387,
          "30%": 0.0045243182103807894,
          "40%": 0.010958904109588984,
          "50%": 0.016245522651620947,
          "60%": 0.02770646393851211,
          "70%": 0.059617904082309055,
          "80%": 0.10112180177353332,
          "90%": 0.13932494130255624,
          "max": 1.0
        }
      },
      "fit_insights": {
        "configurations": {
          "fitting_method": "leastsq",
          "function_evals": 92,
          "data_points": 577,
          "variable_names": [
            "pseudovoigt_amplitude_1",
            "pseudovoigt_center_1",
            "pseudovoigt_fwhmg_1",
            "pseudovoigt_fwhml_1",
            "pseudovoigt_amplitude_2",
            "pseudovoigt_center_2",
            "pseudovoigt_fwhmg_2",
            "pseudovoigt_fwhml_2",
            "constant_amplitude_3",
            "gaussian_amplitude_4",
            "gaussian_center_4",
            "gaussian_fwhmg_4"
          ],
          "variable_numbers": 12,
          "degree_of_freedom": 565
        },
        "statistics": {
          "chi_square": 2.149830777028136,
          "reduced_chi_square": 0.0038050102248285596,
          "akaike_information": -3202.8454593711404,
          "bayesian_information": -3150.551352173043
        },
        "variables": {
          "pseudovoigt_amplitude_1": {
            "init_value": 1,
            "model_value": 0.16403602584115073,
            "best_value": 0.16403602584115073,
            "error_relative": 0.28617283308359887,
            "error_absolute": 174.45730693373602
          },
          "pseudovoigt_center_1": {
            "init_value": 0,
            "model_value": 0.03500058482452051,
            "best_value": 0.03500058482452051,
            "error_relative": 0.07534814694716585,
            "error_absolute": 215.27682273005587
          },
          "pseudovoigt_fwhmg_1": {
            "init_value": 0.02,
            "model_value": 0.0687679507938458,
            "best_value": 0.0687679507938458,
            "error_relative": 0.04790400069682786,
            "error_absolute": 69.66035797756372
          },
          "pseudovoigt_fwhml_1": {
            "init_value": 0.01,
            "model_value": 0.09252389394106236,
            "best_value": 0.09252389394106236,
            "error_relative": 0.037571255043319145,
            "error_absolute": 40.607083687217056
          },
          "pseudovoigt_amplitude_2": {
            "init_value": 1,
            "model_value": 0.09740402120893221,
            "best_value": 0.09740402120893221,
            "error_relative": 0.12049275689025189,
            "error_absolute": 123.7040887991618
          },
          "pseudovoigt_center_2": {
            "init_value": 0,
            "model_value": -0.018052359245206206,
            "best_value": -0.018052359245206206,
            "error_relative": 0.02098357900187265,
            "error_absolute": 116.23732231810547
          },
          "pseudovoigt_fwhmg_2": {
            "init_value": 0.02,
            "model_value": 0.043344705776687614,
            "best_value": 0.043344705776687614,
            "error_relative": 0.030179868797834665,
            "error_absolute": 69.62757794071015
          },
          "pseudovoigt_fwhml_2": {
            "init_value": 0.01,
            "model_value": 0.09989511131863486,
            "best_value": 0.09989511131863486,
            "error_relative": 0.0766935496518902,
            "error_absolute": 76.77407696885308
          },
          "constant_amplitude_3": {
            "init_value": 1,
            "model_value": 0.03676872733249155,
            "best_value": 0.03676872733249155,
            "error_relative": 0.0027777331216664375,
            "error_absolute": 7.554607741921567
          },
          "gaussian_amplitude_4": {
            "init_value": 1,
            "model_value": 0.014112879601465012,
            "best_value": 0.014112879601465012,
            "error_relative": 0.18946469610443273,
            "error_absolute": 1342.494951099597
          },
          "gaussian_center_4": {
            "init_value": 0,
            "model_value": 0.000785067433615172,
            "best_value": 0.000785067433615172,
            "error_relative": 0.0723964536938497,
            "error_absolute": 9221.686009884514
          },
          "gaussian_fwhmg_4": {
            "init_value": 0.02,
            "model_value": 0.0489339673857355,
            "best_value": 0.0489339673857355,
            "error_relative": 0.27055202071590273,
            "error_absolute": 552.8920608116684
          }
        },
        "errorbars": {},
        "correlations": {
          "pseudovoigt_amplitude_1": {
            "pseudovoigt_center_1": -0.9862283106649913,
            "pseudovoigt_fwhmg_1": 0.08087768591070482,
            "pseudovoigt_fwhml_1": 0.026422859895268734,
            "pseudovoigt_amplitude_2": -0.8508056947473775,
            "pseudovoigt_center_2": 0.443720894718587,
            "pseudovoigt_fwhmg_2": 0.46503877490597423,
            "pseudovoigt_fwhml_2": -0.7971320712781913,
            "constant_amplitude_3": -0.19256163835611795,
            "gaussian_amplitude_4": -0.9391516417433717,
            "gaussian_center_4": 0.4275708026546227
          },
          "pseudovoigt_center_1": {
            "pseudovoigt_fwhmg_1": 0.016337719047078703,
            "pseudovoigt_fwhml_1": 0.09199213704177446,
            "pseudovoigt_amplitude_2": 0.7845675730452338,
            "pseudovoigt_center_2": -0.5671057830051938,
            "pseudovoigt_fwhmg_2": -0.543356574051609,
            "pseudovoigt_fwhml_2": 0.7838468315613173,
            "constant_amplitude_3": 0.1908234141503389,
            "gaussian_amplitude_4": 0.9606615151849531,
            "gaussian_center_4": -0.45981680639412886
          },
          "pseudovoigt_fwhmg_1": {
            "pseudovoigt_fwhml_1": 0.9707589530283234,
            "pseudovoigt_amplitude_2": -0.12947342434289133,
            "pseudovoigt_center_2": -0.22593963910738113,
            "pseudovoigt_fwhmg_2": -0.041441070112167695,
            "pseudovoigt_fwhml_2": -0.22029948420194614,
            "constant_amplitude_3": -0.08828608501696038,
            "gaussian_amplitude_4": -0.02662835781007091,
            "gaussian_center_4": 0.11186439414852514
          },
          "pseudovoigt_fwhml_1": {
            "pseudovoigt_amplitude_2": -0.13806698462988234,
            "pseudovoigt_center_2": -0.3754173331238591,
            "pseudovoigt_fwhmg_2": -0.14152665304317025,
            "pseudovoigt_fwhml_2": -0.16783283765319543,
            "constant_amplitude_3": -0.07658241281626063,
            "gaussian_amplitude_4": 0.05913347928634629,
            "gaussian_center_4": 0.06599377246402101
          },
          "pseudovoigt_amplitude_2": {
            "pseudovoigt_center_2": 0.01906524917689979,
            "pseudovoigt_fwhmg_2": 0.06033478892009533,
            "pseudovoigt_fwhml_2": 0.44749434233368474,
            "constant_amplitude_3": 0.18484185277297382,
            "gaussian_amplitude_4": 0.6203122316031827,
            "gaussian_center_4": 0.0556317158685396
          },
          "pseudovoigt_center_2": {
            "pseudovoigt_fwhmg_2": 0.8392271456101567,
            "pseudovoigt_fwhml_2": -0.5198485790152048,
            "constant_amplitude_3": -0.09631860290887163,
            "gaussian_amplitude_4": -0.6669343985978409,
            "gaussian_center_4": 0.6369311212860583
          },
          "pseudovoigt_fwhmg_2": {
            "pseudovoigt_fwhml_2": -0.7677038773609103,
            "constant_amplitude_3": -0.04615140867123564,
            "gaussian_amplitude_4": -0.7331418848699987,
            "gaussian_center_4": 0.9347248046811267
          },
          "pseudovoigt_fwhml_2": {
            "constant_amplitude_3": 0.07011958877932851,
            "gaussian_amplitude_4": 0.9079454516212739,
            "gaussian_center_4": -0.8457904795491098
          },
          "constant_amplitude_3": {
            "gaussian_amplitude_4": 0.15153400546405374,
            "gaussian_center_4": 0.000926625676270801
          },
          "gaussian_amplitude_4": {
            "gaussian_center_4": -0.680824994264301
          },
          "gaussian_center_4": {},
          "gaussian_fwhmg_4": {}
        },
        "covariance_matrix": {
          "pseudovoigt_amplitude_1": {
            "pseudovoigt_amplitude_1": 0.08189489039509333,
            "pseudovoigt_center_1": -0.021265639351830783,
            "pseudovoigt_fwhmg_1": 0.001108737928958058,
            "pseudovoigt_fwhml_1": 0.0002840952206331345,
            "pseudovoigt_amplitude_2": -0.029337272332296393,
            "pseudovoigt_center_2": 0.0026645130237849127,
            "pseudovoigt_fwhmg_2": 0.004016381114148398,
            "pseudovoigt_fwhml_2": -0.017495144124302444,
            "constant_amplitude_3": -0.00015306951027211485,
            "gaussian_amplitude_4": -0.05092047223554052,
            "gaussian_center_4": 0.008858368387821043,
            "gaussian_fwhmg_4": -0.06714216825754851
          },
          "pseudovoigt_center_1": {
            "pseudovoigt_amplitude_1": -0.02126563935183133,
            "pseudovoigt_center_1": 0.005677343248371699,
            "pseudovoigt_fwhmg_1": 5.897063230563316e-5,
            "pseudovoigt_fwhml_1": 0.00026042278959073953,
            "pseudovoigt_amplitude_2": 0.007123015208851593,
            "pseudovoigt_center_2": -0.0008966360919980639,
            "pseudovoigt_fwhmg_2": -0.0012355913220318477,
            "pseudovoigt_fwhml_2": 0.004529628892633818,
            "constant_amplitude_3": 3.993877639913862e-5,
            "gaussian_amplitude_4": 0.013714224880423878,
            "gaussian_center_4": -0.0025082724605561347,
            "gaussian_fwhmg_4": 0.018719658813627908
          },
          "pseudovoigt_fwhmg_1": {
            "pseudovoigt_amplitude_1": 0.0011087379289576504,
            "pseudovoigt_center_1": 5.8970632305741064e-5,
            "pseudovoigt_fwhmg_1": 0.0022947932827616846,
            "pseudovoigt_fwhml_1": 0.0017471849987940095,
            "pseudovoigt_amplitude_2": -0.0007473316247946308,
            "pseudovoigt_center_2": -0.00022711393397554513,
            "pseudovoigt_fwhmg_2": -5.991286583356574e-5,
            "pseudovoigt_fwhml_2": -0.0008093644116645487,
            "constant_amplitude_3": -1.174774635498921e-5,
            "gaussian_amplitude_4": -0.000241682089250215,
            "gaussian_center_4": 0.0003879546421282315,
            "gaussian_fwhmg_4": 0.0006338841801499864
          },
          "pseudovoigt_fwhml_1": {
            "pseudovoigt_amplitude_1": 0.00028409522063252706,
            "pseudovoigt_center_1": 0.00026042278959089474,
            "pseudovoigt_fwhmg_1": 0.001747184998794004,
            "pseudovoigt_fwhml_1": 0.001411599205530134,
            "pseudovoigt_amplitude_2": -0.0006250380895126818,
            "pseudovoigt_center_2": -0.0002959712912374934,
            "pseudovoigt_fwhmg_2": -0.0001604764417774813,
            "pseudovoigt_fwhml_2": -0.0004836057758023863,
            "constant_amplitude_3": -7.99236418817879e-6,
            "gaussian_amplitude_4": 0.0004209373212019539,
            "gaussian_center_4": 0.00017950475225613966,
            "gaussian_fwhmg_4": 0.0016290684573037366
          },
          "pseudovoigt_amplitude_2": {
            "pseudovoigt_amplitude_1": -0.029337272332291955,
            "pseudovoigt_center_1": 0.007123015208850233,
            "pseudovoigt_fwhmg_1": -0.0007473316247947598,
            "pseudovoigt_fwhml_1": -0.0006250380895129165,
            "pseudovoigt_amplitude_2": 0.014518504463013346,
            "pseudovoigt_center_2": 4.8203990398478634e-5,
            "pseudovoigt_fwhmg_2": 0.00021940478068353377,
            "pseudovoigt_fwhml_2": 0.004135302929289992,
            "constant_amplitude_3": 6.186596216252945e-5,
            "gaussian_amplitude_4": 0.014161184585388637,
            "gaussian_center_4": 0.0004852892705786586,
            "gaussian_fwhmg_4": 0.01580657485574901
          },
          "pseudovoigt_center_2": {
            "pseudovoigt_amplitude_1": 0.0026645130237860095,
            "pseudovoigt_center_1": -0.000896636091998334,
            "pseudovoigt_fwhmg_1": -0.00022711393397552792,
            "pseudovoigt_fwhml_1": -0.0002959712912374785,
            "pseudovoigt_amplitude_2": 4.820399039793754e-5,
            "pseudovoigt_center_2": 0.00044031058772783083,
            "pseudovoigt_fwhmg_2": 0.0005314671608839781,
            "pseudovoigt_fwhml_2": -0.0008365949996164612,
            "constant_amplitude_3": -5.614101449265054e-6,
            "gaussian_amplitude_4": -0.002651496020276534,
            "gaussian_center_4": 0.0009675854452465984,
            "gaussian_fwhmg_4": -0.004552935512084298
          },
          "pseudovoigt_fwhmg_2": {
            "pseudovoigt_amplitude_1": 0.004016381114150193,
            "pseudovoigt_center_1": -0.0012355913220322883,
            "pseudovoigt_fwhmg_1": -5.991286583353875e-5,
            "pseudovoigt_fwhml_1": -0.00016047644177745796,
            "pseudovoigt_amplitude_2": 0.00021940478068266733,
            "pseudovoigt_center_2": 0.0005314671608839815,
            "pseudovoigt_fwhmg_2": 0.0009108244806545143,
            "pseudovoigt_fwhml_2": -0.0017769283665557472,
            "constant_amplitude_3": -3.868947408063938e-6,
            "gaussian_amplitude_4": -0.004192119718773303,
            "gaussian_center_4": 0.002042294689594265,
            "gaussian_fwhmg_4": -0.006643131556043086
          },
          "pseudovoigt_fwhml_2": {
            "pseudovoigt_amplitude_1": -0.017495144124304918,
            "pseudovoigt_center_1": 0.004529628892634345,
            "pseudovoigt_fwhmg_1": -0.0008093644116646446,
            "pseudovoigt_fwhml_1": -0.0004836057758025077,
            "pseudovoigt_amplitude_2": 0.004135302929291826,
            "pseudovoigt_center_2": -0.0008365949996163061,
            "pseudovoigt_fwhmg_2": -0.0017769283665554888,
            "pseudovoigt_fwhml_2": 0.005881900558206947,
            "constant_amplitude_3": 1.4937871417533935e-5,
            "gaussian_amplitude_4": 0.013193101203570787,
            "gaussian_center_4": -0.0046961171705344,
            "gaussian_fwhmg_4": 0.017977662918727797
          },
          "constant_amplitude_3": {
            "pseudovoigt_amplitude_1": -0.00015306951027210417,
            "pseudovoigt_center_1": 3.993877639913526e-5,
            "pseudovoigt_fwhmg_1": -1.1747746354989603e-5,
            "pseudovoigt_fwhml_1": -7.992364188179718e-6,
            "pseudovoigt_amplitude_2": 6.186596216253293e-5,
            "pseudovoigt_center_2": -5.61410144926284e-6,
            "pseudovoigt_fwhmg_2": -3.868947408060254e-6,
            "pseudovoigt_fwhml_2": 1.4937871417527104e-5,
            "constant_amplitude_3": 7.71580129520277e-6,
            "gaussian_amplitude_4": 7.974967428193074e-5,
            "gaussian_center_4": 1.8634259555896554e-7,
            "gaussian_fwhmg_4": 0.00010750148023268642
          },
          "gaussian_amplitude_4": {
            "pseudovoigt_amplitude_1": -0.050920472235545126,
            "pseudovoigt_center_1": 0.013714224880424732,
            "pseudovoigt_fwhmg_1": -0.00024168208925048727,
            "pseudovoigt_fwhml_1": 0.0004209373212015925,
            "pseudovoigt_amplitude_2": 0.01416118458539306,
            "pseudovoigt_center_2": -0.0026514960202759937,
            "pseudovoigt_fwhmg_2": -0.004192119718772415,
            "pseudovoigt_fwhml_2": 0.013193101203570229,
            "constant_amplitude_3": 7.974967428194676e-5,
            "gaussian_amplitude_4": 0.03589687106994505,
            "gaussian_center_4": -0.00933858512004467,
            "gaussian_fwhmg_4": 0.05016978516684734
          },
          "gaussian_center_4": {
            "pseudovoigt_amplitude_1": 0.008858368387825048,
            "pseudovoigt_center_1": -0.002508272460557119,
            "pseudovoigt_fwhmg_1": 0.0003879546421282912,
            "pseudovoigt_fwhml_1": 0.00017950475225619249,
            "pseudovoigt_amplitude_2": 0.0004852892705767287,
            "pseudovoigt_center_2": 0.0009675854452466064,
            "pseudovoigt_fwhmg_2": 0.002042294689594267,
            "pseudovoigt_fwhml_2": -0.004696117170534979,
            "constant_amplitude_3": 1.863425955505357e-7,
            "gaussian_amplitude_4": -0.009338585120046658,
            "gaussian_center_4": 0.005241246507445724,
            "gaussian_fwhmg_4": -0.014022897607884997
          },
          "gaussian_fwhmg_4": {
            "pseudovoigt_amplitude_1": -0.06714216825755784,
            "pseudovoigt_center_1": 0.01871965881362988,
            "pseudovoigt_fwhmg_1": 0.0006338841801496148,
            "pseudovoigt_fwhml_1": 0.001629068457303274,
            "pseudovoigt_amplitude_2": 0.015806574855756025,
            "pseudovoigt_center_2": -0.004552935512083683,
            "pseudovoigt_fwhmg_2": -0.006643131556042074,
            "pseudovoigt_fwhml_2": 0.01797766291872774,
            "constant_amplitude_3": 0.00010750148023271109,
            "gaussian_amplitude_4": 0.05016978516684935,
            "gaussian_center_4": -0.014022897607882723,
            "gaussian_fwhmg_4": 0.07319839591345827
          }
        }
      },
      "confidence_interval": {
        "pseudovoigt_amplitude_1": [
          [0.9973002039367398, -Infinity],
          [0.9544997361036416, -Infinity],
          [0.6826894921370859, -Infinity],
          [0.0, 0.16403602584115073],
          [0.6826894921370859, Infinity],
          [0.9544997361036416, Infinity],
          [0.9973002039367398, Infinity]
        ],
        "pseudovoigt_center_1": [
          [0.9973002039367398, -Infinity],
          [0.9544997361036416, -Infinity],
          [0.6826894921370859, -Infinity],
          [0.0, 0.03500058482452051],
          [0.6826894921370859, Infinity],
          [0.9544997361036416, Infinity],
          [0.9973002039367398, Infinity]
        ],
        "pseudovoigt_fwhmg_1": [
          [0.9973002039367398, -Infinity],
          [0.9544997361036416, -Infinity],
          [0.6826894921370859, -Infinity],
          [0.0, 0.0687679507938458],
          [0.6826894921370859, Infinity],
          [0.9544997361036416, Infinity],
          [0.9973002039367398, Infinity]
        ],
        "pseudovoigt_fwhml_1": [
          [0.9973002039367398, -Infinity],
          [0.9544997361036416, -Infinity],
          [0.6826894921370859, -Infinity],
          [0.0, 0.09252389394106236],
          [0.6826894921370859, Infinity],
          [0.9544997361036416, Infinity],
          [0.9973002039367398, Infinity]
        ],
        "pseudovoigt_amplitude_2": [
          [0.9973002039367398, -Infinity],
          [0.9544997361036416, -Infinity],
          [0.6826894921370859, -Infinity],
          [0.0, 0.09740402120893221],
          [0.6826894921370859, Infinity],
          [0.9544997361036416, Infinity],
          [0.9973002039367398, Infinity]
        ],
        "pseudovoigt_center_2": [
          [0.9973002039367398, -Infinity],
          [0.9544997361036416, -Infinity],
          [0.6826894921370859, -Infinity],
          [0.0, -0.018052359245206206],
          [0.6826894921370859, Infinity],
          [0.9544997361036416, Infinity],
          [0.9973002039367398, Infinity]
        ],
        "pseudovoigt_fwhmg_2": [
          [0.9973002039367398, -Infinity],
          [0.9544997361036416, -Infinity],
          [0.6826894921370859, -Infinity],
          [0.0, 0.043344705776687614],
          [0.6826894921370859, Infinity],
          [0.9544997361036416, Infinity],
          [0.9973002039367398, Infinity]
        ],
        "pseudovoigt_fwhml_2": [
          [0.9973002039367398, -Infinity],
          [0.9544997361036416, -Infinity],
          [0.6826894921370859, -Infinity],
          [0.0, 0.09989511131863486],
          [0.6826894921370859, Infinity],
          [0.9544997361036416, Infinity],
          [0.9973002039367398, Infinity]
        ],
        "constant_amplitude_3": [
          [0.9973002039367398, -Infinity],
          [0.9544997361036416, -Infinity],
          [0.6826894921370859, -Infinity],
          [0.0, 0.03676872733249155],
          [0.6826894921370859, Infinity],
          [0.9544997361036416, Infinity],
          [0.9973002039367398, Infinity]
        ],
        "gaussian_amplitude_4": [
          [0.9973002039367398, -Infinity],
          [0.9544997361036416, -Infinity],
          [0.6826894921370859, -Infinity],
          [0.0, 0.014112879601465012],
          [0.6826894921370859, Infinity],
          [0.9544997361036416, Infinity],
          [0.9973002039367398, Infinity]
        ],
        "gaussian_center_4": [
          [0.9973002039367398, -Infinity],
          [0.9544997361036416, -Infinity],
          [0.6826894921370859, -Infinity],
          [0.0, 0.000785067433615172],
          [0.6826894921370859, Infinity],
          [0.9544997361036416, Infinity],
          [0.9973002039367398, Infinity]
        ],
        "gaussian_fwhmg_4": [
          [0.9973002039367398, -Infinity],
          [0.9544997361036416, -Infinity],
          [0.6826894921370859, -Infinity],
          [0.0, 0.0489339673857355],
          [0.6826894921370859, Infinity],
          [0.9544997361036416, Infinity],
          [0.9973002039367398, Infinity]
        ]
      },
      "linear_correlation": {
        "energy": {
          "energy": 1.0,
          "intensity": -0.3129468170823972,
          "residual": 0.11751656931991195,
          "fit": -0.2259994866489651,
          "pseudovoigt_1": -0.21288051248995526,
          "pseudovoigt_2": -0.246613792947609,
          "constant_3": NaN,
          "gaussian_4": -0.10125030598524841
        },
        "intensity": {
          "energy": -0.3129468170823972,
          "intensity": 1.0,
          "residual": 0.04780312901812482,
          "fit": 0.9036600060804049,
          "pseudovoigt_1": 0.8801769832650946,
          "pseudovoigt_2": 0.854987122158034,
          "constant_3": NaN,
          "gaussian_4": 0.6134257926400243
        },
        "residual": {
          "energy": 0.11751656931991195,
          "intensity": 0.04780312901812482,
          "residual": 1.0,
          "fit": 0.4709588097391075,
          "pseudovoigt_1": 0.47380507798980864,
          "pseudovoigt_2": 0.39048994293738104,
          "constant_3": NaN,
          "gaussian_4": 0.39179078414068746
        },
        "fit": {
          "energy": -0.2259994866489651,
          "intensity": 0.9036600060804049,
          "residual": 0.4709588097391075,
          "fit": 1.0,
          "pseudovoigt_1": 0.9804809307693575,
          "pseudovoigt_2": 0.9225135358767362,
          "constant_3": NaN,
          "gaussian_4": 0.709732782751552
        },
        "pseudovoigt_1": {
          "energy": -0.21288051248995526,
          "intensity": 0.8801769832650946,
          "residual": 0.47380507798980864,
          "fit": 0.9804809307693575,
          "pseudovoigt_1": 1.0,
          "pseudovoigt_2": 0.8453034770676977,
          "constant_3": NaN,
          "gaussian_4": 0.6530789084228865
        },
        "pseudovoigt_2": {
          "energy": -0.246613792947609,
          "intensity": 0.854987122158034,
          "residual": 0.39048994293738104,
          "fit": 0.9225135358767362,
          "pseudovoigt_1": 0.8453034770676977,
          "pseudovoigt_2": 1.0,
          "constant_3": NaN,
          "gaussian_4": 0.558516514398519
        },
        "constant_3": {
          "energy": NaN,
          "intensity": NaN,
          "residual": NaN,
          "fit": NaN,
          "pseudovoigt_1": NaN,
          "pseudovoigt_2": NaN,
          "constant_3": NaN,
          "gaussian_4": NaN
        },
        "gaussian_4": {
          "energy": -0.10125030598524841,
          "intensity": 0.6134257926400243,
          "residual": 0.39179078414068746,
          "fit": 0.709732782751552,
          "pseudovoigt_1": 0.6530789084228865,
          "pseudovoigt_2": 0.558516514398519,
          "constant_3": NaN,
          "gaussian_4": 1.0
        }
      },
      "fit_result": {
        "energy": [
          -1.6, -1.5833333333333335, -1.5666666666666669, -1.5500000000000003,
          -1.5333333333333337, -1.516666666666667, -1.5000000000000004,
          -1.4833333333333338, -1.4666666666666672, -1.4500000000000006,
          -1.433333333333334, -1.4166666666666674, -1.4000000000000008,
          -1.383333333333334, -1.3666666666666676, -1.3500000000000008,
          -1.3333333333333344, -1.3166666666666675, -1.3000000000000012,
          -1.2833333333333343, -1.266666666666668, -1.250000000000001,
          -1.2333333333333347, -1.216666666666668, -1.2000000000000015,
          -1.183333333333335, -1.1666666666666683, -1.1500000000000017,
          -1.133333333333335, -1.1166666666666685, -1.1000000000000019,
          -1.0833333333333353, -1.0666666666666687, -1.050000000000002,
          -1.0333333333333354, -1.0166666666666688, -1.0000000000000022,
          -0.9833333333333357, -0.966666666666669, -0.9500000000000025,
          -0.9333333333333358, -0.9166666666666691, -0.9000000000000026,
          -0.8833333333333359, -0.8666666666666692, -0.8500000000000028,
          -0.8333333333333361, -0.8166666666666694, -0.8000000000000029,
          -0.7833333333333363, -0.7666666666666697, -0.750000000000003,
          -0.7333333333333365, -0.7166666666666699, -0.7000000000000033,
          -0.6833333333333367, -0.6666666666666701, -0.6500000000000035,
          -0.6333333333333369, -0.6166666666666702, -0.6000000000000036,
          -0.5833333333333369, -0.5666666666666704, -0.5500000000000038,
          -0.5333333333333372, -0.5166666666666706, -0.500000000000004,
          -0.48333333333333733, -0.4666666666666708, -0.4500000000000042,
          -0.4333333333333376, -0.41666666666667096, -0.4000000000000044,
          -0.38333333333333774, -0.36666666666667114, -0.3500000000000045,
          -0.3333333333333379, -0.31666666666667126, -0.3000000000000047,
          -0.2833333333333381, -0.2666666666666715, -0.2500000000000049,
          -0.23333333333333828, -0.21666666666667167, -0.20000000000000503,
          -0.18333333333333843, -0.16666666666667185, -0.15000000000000524,
          -0.13333333333333863, -0.11666666666667203, -0.1000000000000054,
          -0.08333333333333881, -0.0666666666666722, -0.0500000000000056,
          -0.03333333333333899, -0.01666666666667238, -5.773159728050815e-15,
          0.016666666666660834, 0.03333333333332744, 0.04999999999999405,
          0.06666666666666066, 0.08333333333332726, 0.09999999999999389,
          0.11666666666666048, 0.1333333333333271, 0.14999999999999367,
          0.1666666666666603, 0.18333333333332688, 0.19999999999999352,
          0.21666666666666007, 0.23333333333332676, 0.2499999999999933,
          0.26666666666665995, 0.2833333333333265, 0.2999999999999932,
          0.31666666666665977, 0.3333333333333264, 0.349999999999993,
          0.3666666666666596, 0.38333333333332614, 0.3999999999999928,
          0.41666666666665936, 0.433333333333326, 0.44999999999999263,
          0.4666666666666592, 0.4833333333333258, 0.4999999999999925,
          0.5166666666666592, 0.5333333333333257, 0.5499999999999923,
          0.5666666666666589, 0.5833333333333255, 0.5999999999999921,
          0.6166666666666587, 0.6333333333333253, 0.6499999999999919,
          0.6666666666666585, 0.6833333333333251, 0.6999999999999916,
          0.7166666666666583, 0.733333333333325, 0.7499999999999916,
          0.7666666666666581, 0.7833333333333247, 0.7999999999999914,
          0.8166666666666581, 0.8333333333333246, 0.8499999999999912,
          0.8666666666666578, 0.8833333333333245, 0.899999999999991,
          0.9166666666666576, 0.9333333333333241, 0.9499999999999907,
          0.9666666666666575, 0.983333333333324, 0.9999999999999906,
          1.0166666666666573, 1.033333333333324, 1.0499999999999905,
          1.066666666666657, 1.0833333333333235, 1.0999999999999903,
          1.1166666666666567, 1.1333333333333235, 1.14999999999999,
          1.1666666666666567, 1.1833333333333231, 1.19999999999999,
          1.2166666666666563, 1.2333333333333232, 1.2499999999999896,
          1.2666666666666564, 1.283333333333323, 1.2999999999999896,
          1.3166666666666562, 1.3333333333333228, 1.3499999999999894,
          1.366666666666656, 1.3833333333333226, 1.3999999999999893,
          1.4166666666666559, 1.4333333333333225, 1.449999999999989,
          1.4666666666666557, 1.4833333333333223, 1.499999999999989,
          1.5166666666666555, 1.533333333333322, 1.5499999999999887,
          1.566666666666655, 1.583333333333322, 1.5999999999999883,
          1.6166666666666551, 1.6333333333333215, 1.6499999999999884,
          1.6666666666666548, 1.6833333333333216, 1.699999999999988,
          1.7166666666666548, 1.7333333333333214, 1.749999999999988,
          1.7666666666666546, 1.7833333333333212, 1.7999999999999878,
          1.8166666666666544, 1.8333333333333208, 1.849999999999988,
          1.8666666666666545, 1.8833333333333209, 1.8999999999999877,
          1.916666666666654, 1.9333333333333207, 1.9499999999999873,
          1.9666666666666537, 1.9833333333333203, 1.9999999999999871,
          2.0166666666666537, 2.0333333333333203, 2.049999999999987,
          2.066666666666653, 2.08333333333332, 2.0999999999999868,
          2.1166666666666534, 2.13333333333332, 2.1499999999999866,
          2.1666666666666528, 2.18333333333332, 2.1999999999999864,
          2.216666666666653, 2.23333333333332, 2.2499999999999862,
          2.266666666666653, 2.2833333333333194, 2.299999999999986,
          2.3166666666666527, 2.3333333333333193, 2.3499999999999854,
          2.3666666666666525, 2.383333333333319, 2.3999999999999857,
          2.4166666666666523, 2.433333333333319, 2.449999999999985,
          2.466666666666652, 2.4833333333333187, 2.4999999999999853,
          2.516666666666652, 2.5333333333333186, 2.5499999999999847,
          2.566666666666652, 2.5833333333333184, 2.599999999999985,
          2.6166666666666516, 2.633333333333318, 2.649999999999985,
          2.6666666666666514, 2.683333333333318, 2.6999999999999846,
          2.7166666666666512, 2.7333333333333174, 2.7499999999999845,
          2.766666666666651, 2.7833333333333177, 2.799999999999984,
          2.816666666666651, 2.833333333333317, 2.849999999999984,
          2.8666666666666507, 2.8833333333333173, 2.899999999999984,
          2.9166666666666505, 2.9333333333333167, 2.949999999999984,
          2.9666666666666504, 2.983333333333317, 2.9999999999999836,
          3.01666666666665, 3.033333333333317, 3.0499999999999834,
          3.0666666666666496, 3.0833333333333166, 3.099999999999983,
          3.11666666666665, 3.1333333333333164, 3.149999999999983,
          3.1666666666666496, 3.183333333333316, 3.199999999999983,
          3.216666666666649, 3.233333333333316, 3.2499999999999822,
          3.266666666666649, 3.283333333333316, 3.2999999999999825,
          3.3166666666666487, 3.333333333333316, 3.3499999999999823,
          3.366666666666649, 3.3833333333333155, 3.399999999999982,
          3.4166666666666488, 3.433333333333316, 3.4499999999999815,
          3.4666666666666486, 3.483333333333315, 3.499999999999982,
          3.5166666666666484, 3.533333333333315, 3.5499999999999816,
          3.566666666666648, 3.583333333333315, 3.599999999999981,
          3.616666666666648, 3.633333333333314, 3.649999999999981,
          3.666666666666648, 3.6833333333333136, 3.6999999999999806,
          3.716666666666648, 3.7333333333333134, 3.749999999999981,
          3.766666666666648, 3.7833333333333137, 3.7999999999999807,
          3.8166666666666473, 3.8333333333333135, 3.849999999999981,
          3.866666666666647, 3.8833333333333138, 3.89999999999998,
          3.916666666666647, 3.9333333333333136, 3.94999999999998,
          3.9666666666666472, 3.9833333333333134, 3.99999999999998,
          4.016666666666646, 4.033333333333314, 4.049999999999979,
          4.066666666666647, 4.083333333333313, 4.09999999999998, 4.116666666666646,
          4.133333333333312, 4.149999999999979, 4.166666666666647,
          4.183333333333312, 4.19999999999998, 4.216666666666645, 4.233333333333313,
          4.249999999999979, 4.266666666666646, 4.283333333333312,
          4.299999999999979, 4.316666666666645, 4.333333333333313,
          4.349999999999977, 4.366666666666646, 4.383333333333312,
          4.399999999999979, 4.416666666666645, 4.433333333333312,
          4.449999999999978, 4.466666666666645, 4.483333333333311,
          4.499999999999979, 4.516666666666644, 4.533333333333312,
          4.549999999999978, 4.566666666666645, 4.583333333333311,
          4.599999999999977, 4.616666666666644, 4.633333333333312,
          4.649999999999976, 4.666666666666645, 4.6833333333333105,
          4.699999999999978, 4.716666666666644, 4.733333333333311,
          4.749999999999977, 4.766666666666644, 4.78333333333331, 4.799999999999978,
          4.816666666666643, 4.833333333333311, 4.8499999999999766,
          4.866666666666644, 4.88333333333331, 4.899999999999976, 4.916666666666642,
          4.9333333333333105, 4.949999999999976, 4.966666666666644,
          4.9833333333333085, 4.999999999999977, 5.016666666666643,
          5.03333333333331, 5.049999999999976, 5.066666666666643, 5.083333333333309,
          5.0999999999999766, 5.116666666666641, 5.13333333333331,
          5.149999999999976, 5.166666666666642, 5.183333333333309,
          5.199999999999976, 5.216666666666642, 5.2333333333333085,
          5.249999999999975, 5.266666666666643, 5.283333333333308,
          5.299999999999976, 5.316666666666642, 5.333333333333309,
          5.349999999999975, 5.366666666666641, 5.383333333333308,
          5.399999999999976, 5.416666666666641, 5.433333333333309,
          5.449999999999974, 5.466666666666642, 5.483333333333308,
          5.499999999999975, 5.516666666666641, 5.533333333333308,
          5.549999999999974, 5.566666666666642, 5.583333333333307,
          5.599999999999975, 5.61666666666664, 5.633333333333308, 5.649999999999974,
          5.666666666666641, 5.683333333333306, 5.699999999999974, 5.71666666666664,
          5.733333333333308, 5.7499999999999725, 5.766666666666641,
          5.783333333333307, 5.799999999999974, 5.81666666666664, 5.833333333333307,
          5.849999999999973, 5.86666666666664, 5.883333333333305, 5.899999999999974,
          5.91666666666664, 5.933333333333306, 5.949999999999973, 5.96666666666664,
          5.983333333333306, 5.9999999999999725, 6.016666666666639,
          6.033333333333307, 6.049999999999972, 6.06666666666664,
          6.0833333333333055, 6.099999999999973, 6.11666666666664,
          6.133333333333305, 6.149999999999972, 6.16666666666664, 6.183333333333305,
          6.199999999999973, 6.216666666666638, 6.233333333333306,
          6.249999999999972, 6.266666666666639, 6.283333333333305,
          6.299999999999972, 6.316666666666638, 6.3333333333333055,
          6.349999999999971, 6.36666666666664, 6.383333333333304, 6.399999999999972,
          6.416666666666638, 6.433333333333305, 6.449999999999973,
          6.466666666666638, 6.483333333333304, 6.499999999999972,
          6.516666666666639, 6.533333333333305, 6.5499999999999705,
          6.566666666666638, 6.5833333333333055, 6.599999999999971,
          6.616666666666637, 6.633333333333304, 6.649999999999972,
          6.666666666666638, 6.683333333333303, 6.69999999999997, 6.716666666666638,
          6.733333333333304, 6.74999999999997, 6.766666666666636, 6.783333333333305,
          6.7999999999999705, 6.816666666666636, 6.833333333333304,
          6.849999999999971, 6.866666666666637, 6.8833333333333035,
          6.899999999999969, 6.916666666666638, 6.933333333333303,
          6.949999999999969, 6.966666666666637, 6.983333333333304, 6.99999999999997,
          7.016666666666636, 7.033333333333303, 7.0499999999999705,
          7.066666666666636, 7.083333333333302, 7.0999999999999694,
          7.116666666666637, 7.1333333333333035, 7.149999999999968,
          7.166666666666636, 7.183333333333303, 7.199999999999969,
          7.216666666666634, 7.233333333333302, 7.249999999999972,
          7.2666666666666355, 7.283333333333301, 7.299999999999968,
          7.316666666666637, 7.333333333333303, 7.349999999999967,
          7.366666666666635, 7.383333333333303, 7.399999999999968,
          7.416666666666633, 7.433333333333301, 7.44999999999997, 7.466666666666634,
          7.4833333333333, 7.499999999999968, 7.5166666666666355, 7.533333333333301,
          7.549999999999968, 7.566666666666634, 7.583333333333303,
          7.599999999999967, 7.616666666666633, 7.633333333333299,
          7.649999999999968, 7.666666666666633, 7.683333333333299,
          7.699999999999966, 7.716666666666634, 7.7333333333333, 7.749999999999966,
          7.766666666666634, 7.783333333333301, 7.799999999999968,
          7.816666666666632, 7.833333333333299, 7.849999999999967,
          7.866666666666633, 7.883333333333299, 7.899999999999967,
          7.916666666666633, 7.933333333333299, 7.949999999999965,
          7.966666666666634, 7.9833333333333, 7.999999999999966
        ],
        "intensity": [
          0.0, 0.003891050583657596, 0.003973071404922201, 0.00405770964833183,
          0.0041450777202072485, 0.004235294117647068, 0.0043284838283034685,
          0.004424778761061949, 0.004524318210380788, 0.0046272493573264635,
          0.004733727810650881, 0.004843918191603862, 0.004957994766561084,
          0.005076142131979685, 0.005198555956678712, 0.0053254437869822225,
          0.005457025920873108, 0.005593536357986327, 0.0057352238330412595,
          0.005882352941176454, 0.006035205364626978, 0.006194081211286973,
          0.006359300476947529, 0.00653120464441218, 0.006710158434296354,
          0.006896551724137925, 0.007090801654520351, 0.0072933549432738845,
          0.007504690431519682, 0.0077253218884119875, 0.007955801104972366,
          0.008196721311475363, 0.008448720957521673, 0.008712487899322318,
          0.00898876404494378, 0.009278350515463833, 0.009582113388341695,
          0.009900990099009844, 0.010235996588001109, 0.010588235294117582,
          0.010958904109588984, 0.011349306431273604, 0.011760862463247207,
          0.012195121951219443, 0.012653778558875128, 0.013138686131386808,
          0.013651877133105715, 0.014195583596214404, 0.014772260976610463,
          0.015384615384615235, 0.01603563474387513, 0.016728624535315855,
          0.01746724890829681, 0.018255578093306146, 0.01909814323607401,
          0.019999999999999855, 0.02096680256260904, 0.02200488997554988,
          0.02312138728323678, 0.02432432432432412, 0.02562277580071142,
          0.02702702702702668, 0.028548770816811748, 0.030201342281878873,
          0.03199999999999956, 0.03396226415094291, 0.03610832497492419,
          0.0384615384615379, 0.04104903078677245, 0.04390243902438932,
          0.04705882352941089, 0.05056179775280797, 0.054462934947048874,
          0.058823529411763525, 0.0637168141592905, 0.06923076923076783,
          0.07547169811320567, 0.08256880733944734, 0.09068010075566536,
          0.09999999999999735, 0.11076923076922764, 0.12328767123287268,
          0.137931034482754, 0.15517241379309754, 0.1756097560975534,
          0.19999999999999216, 0.22929936305731488, 0.2647058823529294,
          0.3076923076922934, 0.35999999999998283, 0.42352941176468273,
          0.49999999999997286, 0.590163934426198, 0.6923076923076551,
          0.7999999999999646, 0.8999999999999696, 0.972972972972956, 1.0,
          0.9729729729729932, 0.9000684869288876, 0.8003319898391893,
          0.6926622009062817, 0.5905260079579859, 0.5003698828803956,
          0.423907359037742, 0.36038627792143624, 0.3080871943516519,
          0.26510966833725974, 0.229712352160166, 0.200422509979045,
          0.17604211948496107, 0.15561497876280292, 0.1383841657795379,
          0.12375175116828944, 0.11124466029010888, 0.1008615472585792,
          0.09156616328472589, 0.08347578183738227, 0.07640033803343374,
          0.07018186486213082, 0.06469119491649024, 0.05982206629964605,
          0.05548654321439518, 0.05161143975291705, 0.04813551180660481,
          0.04500723964762217, 0.042183066953828376, 0.03962599439990947,
          0.03762979151803755, 0.0355235772582584, 0.033602772665341465,
          0.03184727712998013, 0.0302396665048004, 0.028764785209156422,
          0.02740940871559529, 0.026161963071215155, 0.025055460720915503,
          0.02399553502734928, 0.02310851127639354, 0.022205528543641218,
          0.021575947349213472, 0.020807671274259663, 0.020262538639031612,
          0.019608943762035314, 0.01900508918247521, 0.01844758920101576,
          0.017933441506014527, 0.017459988802825416, 0.017116223909357433,
          0.01700109250482449, 0.016644697110745524, 0.016321490303453878,
          0.016030153287369217, 0.015769582084074696, 0.01553887828303456,
          0.015337342770190972, 0.015164472389002764, 0.015019959565844851,
          0.014903695013669643, 0.014815773718070222, 0.014756504512647603,
          0.01472642367105966, 0.014726313087813518, 0.014762833800814612,
          0.014828824980555134, 0.014936297382658363, 0.015092709661536039,
          0.015265693132420408, 0.015480363766871183, 0.01574034597789587,
          0.016049975876225163, 0.016445001617509163, 0.016871150941466195,
          0.017365810966736703, 0.01793794637067392, 0.018598387284889623,
          0.019360276650060192, 0.02027741539926165, 0.02139506330100348,
          0.02265340564781228, 0.024215964657596928, 0.02582307680845409,
          0.02770646393851211, 0.029925276941982052, 0.03255400371914528,
          0.03568618792266998, 0.039438183003851726, 0.04395161588318507,
          0.049396347905066126, 0.05593774572615727, 0.06372917556163323,
          0.07281235769968086, 0.08297912055122572, 0.08968666903582638,
          0.09956504877300416, 0.106985658129584, 0.1105553529287392,
          0.10976166283155749, 0.10550302268599474, 0.09954066028792553,
          0.09359971188053476, 0.08894698680154246, 0.08611776697261757,
          0.08549802656897262, 0.08714704444740207, 0.09114323548348285,
          0.09741566916226682, 0.10570299682241792, 0.11534606210318205,
          0.12489566539676876, 0.1324663709406456, 0.1361582465387924,
          0.13517303448186327, 0.13039310047924793, 0.12373011438496852,
          0.1172246633030924, 0.11223132336840552, 0.10964438113207683,
          0.10970848399307127, 0.11247749074012411, 0.11768922280751624,
          0.12473707754788672, 0.13233632676821225, 0.1388812549798811,
          0.1427420541018731, 0.14319471281865284, 0.14110364763997182,
          0.13826829089995027, 0.1363279334870925, 0.13652200547175272,
          0.13932494130255624, 0.14470822166638303, 0.1521105848946017,
          0.16061207756974027, 0.16897722924770694, 0.1759261828247377,
          0.18029139969025185, 0.18149515421662843, 0.1797830536574096,
          0.1762170482718902, 0.17226873288254063, 0.1691475675474199,
          0.1671686571423933, 0.16548924618092917, 0.16242034016088563,
          0.15633214078963112, 0.14661349398571155, 0.13410546069691992,
          0.12044536220806938, 0.10718928699229796, 0.09532586355221329,
          0.08529339317605522, 0.07709066119281836, 0.07063904745880455,
          0.06568665577483854, 0.062078991816957016, 0.059617904082309055,
          0.058164564233077025, 0.05756091921572554, 0.057635772916898795,
          0.058225327937197355, 0.05915096685973496, 0.06033003213293948,
          0.06181828855366552, 0.06374490759060672, 0.06628981889926785,
          0.06958414097301331, 0.07372846515462701, 0.07885975952308069,
          0.0851664178607698, 0.09277070516830589, 0.10151164911253709,
          0.11073487266572096, 0.11922007584730741, 0.12537987745324689,
          0.1277625583305999, 0.1256732739092848, 0.11955130788860958,
          0.11079566712510833, 0.10112180177353332, 0.09192926638695936,
          0.08404615436832302, 0.07780751134483174, 0.07325039227702294,
          0.0702860388364263, 0.06882118316423944, 0.06876812106173276,
          0.07010374023997071, 0.07279255164035678, 0.07675045397804342,
          0.08174717338281955, 0.08735955311363625, 0.09306179365964579,
          0.09900498124429352, 0.10487737930796168, 0.11069291597185596,
          0.11639708496367848, 0.1217273908908785, 0.1265996020457453,
          0.13116896447439702, 0.135966288673545, 0.14142025008083,
          0.14751975109442883, 0.15352737719387624, 0.15816409853225305,
          0.1601857154835972, 0.1589545566775944, 0.1544852206038986,
          0.14869755741153032, 0.14263605104698895, 0.13741146743857324,
          0.133595436797124, 0.1313273368739534, 0.13056686253320388,
          0.1312641333278097, 0.1332797358903959, 0.13628483366420036,
          0.13952422967709147, 0.14204112486636356, 0.14294294009596903,
          0.1414293792565008, 0.13818933933035218, 0.1331860419733018,
          0.12665222914930274, 0.1187286978126514, 0.10961484592424504,
          0.09984258973974126, 0.09008223810188593, 0.08085685620230627,
          0.07256316222572513, 0.06510214772133885, 0.058610921444190896,
          0.05272378319996645, 0.04782334744197015, 0.04352307002441606,
          0.04013926610201627, 0.03746459966304642, 0.03544048418519373,
          0.033991331387312106, 0.03302552570019131, 0.03235083401139447,
          0.03178395118237268, 0.031763311390900446, 0.03201973702619608,
          0.03258483891250205, 0.033434036826116544, 0.03443820935102124,
          0.03536756518157945, 0.0359505047177961, 0.03596231076319577,
          0.035307682507203744, 0.03406049881290491, 0.032431453015792665,
          0.030672135044579777, 0.028966334931621377, 0.027363343807303785,
          0.025815923983005612, 0.024223887688296343, 0.022534439228242227,
          0.02080220500592597, 0.01906966307887128, 0.017415702302007743,
          0.015905951446525034, 0.014547887882829291, 0.013426539109273928,
          0.012476164752763268, 0.01169175984669532, 0.0110536908237312,
          0.010544300517995238, 0.010111764810362156, 0.00972206784273088,
          0.009455938247878402, 0.00917693218891364, 0.009188422430469106,
          0.009302694296132702, 0.009526867750149264, 0.00986838204117474,
          0.010331111121827347, 0.01090924976026132, 0.011580885210842348,
          0.012302396425264627, 0.013040057798095108, 0.01375875631275779,
          0.014446891702747667, 0.015096153108483168, 0.0156940023344889,
          0.016245522651620947, 0.01679928445342448, 0.01737505498767164,
          0.0181204113718608, 0.019033587276818326, 0.019970639491295936,
          0.02074138628625168, 0.021111052848654666, 0.021112069193101986,
          0.020665350292444727, 0.019932856436185555, 0.01901540556743102,
          0.018058869882539637, 0.017125363876573842, 0.016172326663091947,
          0.015272093379256828, 0.014377044247257916, 0.013569579387075379,
          0.012938043359667311, 0.012491246058805286, 0.01227021526391276,
          0.012229573379522967, 0.012411790448933363, 0.012631955771594887,
          0.012861890526208767, 0.012952664129169731, 0.012832477224745792,
          0.012455702351086588, 0.01199385158593986, 0.011501102142697736,
          0.011128819379458171, 0.01097831551997038, 0.010927316390904133,
          0.010806211169280888, 0.010614974257290192, 0.010271581326610123,
          0.009834131065227129, 0.009297598301658177, 0.008697139372068055,
          0.008024116887538398, 0.007315731922365474, 0.006565652453779356,
          0.005844794880350924, 0.005177767365665529, 0.004587412844911594,
          0.0040798944721002, 0.0036506665421485577, 0.00329037815035334,
          0.0029886090930426146, 0.002735690107776864, 0.002523366843905612,
          0.0023300631942332127, 0.002180374898760963, 0.002054958204967324,
          0.0019505886000300875, 0.0018648527274811324, 0.0017960239663209377,
          0.001720481626512626, 0.0016830996415389443, 0.0016262300718450644,
          0.001611919732637923, 0.0016048014922694148, 0.0016347432507004985,
          0.0016857628276620254, 0.001761334740481444, 0.001865932288006437,
          0.001989512518215736, 0.0021607489243893377, 0.002386736856454915,
          0.0026530571609377643, 0.002969667659174261, 0.0033068140847257966,
          0.003620015633850385, 0.0038444166455045207, 0.003916571185462839,
          0.0038092320327282624, 0.0035494402458889464, 0.00320043214610638,
          0.0028268467668079366, 0.002472937473226955, 0.002160175622001572,
          0.001894251048772865, 0.001672608969388938, 0.0014894646029960984,
          0.0013384345380275796, 0.0012136748094292323, 0.0011102474053009976,
          0.0010241407634558619, 0.0009521598820936355, 0.0008917842772384375,
          0.0008410336313034932, 0.0007882098897912334, 0.0007525906554877921,
          0.0007228641949372934, 0.0006982868399087982, 0.0006671157541095356,
          0.000645005379493612, 0.0006333058086720105, 0.000625184442884534,
          0.0006205035025779992, 0.0006192046745116873, 0.0006213057378856704,
          0.0006039945868221229, 0.0006137252238044462, 0.0006047776936573755,
          0.0006231581830360969, 0.0006337680871982241, 0.0006624848892488697,
          0.0006973192371910539, 0.0007392569480711444, 0.0007895426603224253,
          0.0008330084196076873, 0.0009054639619342336, 0.0009923357464075885,
          0.0010968178118700965, 0.0012229540649686605, 0.0013758345184867965,
          0.0015617780277680387, 0.0017884101805828436, 0.002064429183181777,
          0.002387968244156822, 0.002787075005635288, 0.0032330643719318663,
          0.0037448433409505576, 0.004266115855053602, 0.004733392359982105,
          0.0050731049261991245, 0.005228483226228465, 0.005177871012632568,
          0.004933801139556769, 0.004516681615965384, 0.004025914623300037,
          0.0035069432009657746, 0.003011562010941419, 0.0025693287122871486,
          0.002180151797621449, 0.0018631067214146704, 0.0016005279884154326,
          0.001383752803081267, 0.0012045262550681973, 0.0010557189196281143,
          0.0009314598629566572, 0.0008270276372756256, 0.0007386662934833399,
          0.000663398632862216, 0.0005988630824781945, 0.0005431803012114177,
          0.0004948475983603272, 0.00045265671581789455, 0.00041563027155241765,
          0.0003829727316072356, 0.0003540325485166859, 0.0003282728337111797,
          0.00030524854341540544, 0.0002845886426487827, 0.0002659820854651423,
          0.00024916673278896844, 0.00023392054231395035, 0.0002200545248037094,
          0.00020740708106580888, 0.00019583942400428853, 0.00018523185810550465,
          0.0001754807401376867, 0.00016649598393723487, 0.00015819900201364986,
          0.00015052099962416344, 0.00014340155465021373, 0.000136787430317109,
          0.0001306315784814117, 0.00012489229957700896, 0.00010650950352080627,
          0.00010176233346638824, 9.732407586281645e-5, 9.316862596969085e-5,
          8.927256629278886e-5, 8.56148429229433e-5, 8.217648623838878e-5,
          7.894036918914812e-5, 7.589099752037563e-5, 7.301432722262195e-5,
          7.029760526128519e-5, 6.772923026716017e-5, 6.529863039051561e-5,
          6.299615595285945e-5, 6.0812984889811416e-5, 5.874103927838362e-5,
          5.677291149306076e-5, 5.490179874591324e-5, 5.312144494355774e-5,
          5.1426088943718254e-5, 4.98104184211338e-5
        ],
        "residual": [
          0.03860835067784256, 0.034755929338874086, 0.034713767352860754,
          0.034670270277321384, 0.034625381306410005, 0.03457904058984698,
          0.03453118503564271, 0.03448174809779662, 0.0344306595476548,
          0.03437784522747757, 0.03432322678462423, 0.03426672138459972,
          0.034208241401028024, 0.0341476940804171, 0.03408498117935497,
          0.034019998571528126, 0.03395263582167139, 0.03388277572324744,
          0.03381029379630025, 0.03373505774153422, 0.03365692684622595,
          0.033575751337077325, 0.033491371674555175, 0.0334036177826287,
          0.03331230820709761, 0.033217249194892835, 0.03311823368581079,
          0.03301504020709824, 0.03290743166011859, 0.032795153986978146,
          0.03267793470345212, 0.03255548128279151, 0.03242747937298003,
          0.032293590827708996, 0.03215345152869319, 0.03200666897391602,
          0.031852819602894655, 0.03169144582602684, 0.03152205272042256,
          0.031344104349238136, 0.03115701965528346, 0.030960167872422326,
          0.03075286338984804, 0.0305343599944853, 0.03030384440529244,
          0.03006042899981081, 0.02980314361758412, 0.029530926306607953,
          0.029242612857274225, 0.028936924942721938, 0.02861245665437759,
          0.028267659185889516, 0.027900823376594754, 0.027510059775875558,
          0.027093275830804387, 0.02664814972962787, 0.02617210035090616,
          0.02566225267019198, 0.025115397860429232, 0.02452794718590352,
          0.023895878629637275, 0.023214675007755425, 0.02247925210934835,
          0.021683875156030277, 0.02082206160408097, 0.019886468021757357,
          0.01886875848316276, 0.017759451663624158, 0.01654774366568139,
          0.015221303666706196, 0.01376603996327215, 0.012165835246254315,
          0.010402252579275295, 0.008454218608935277, 0.006297699791160891,
          0.0039054039536188107, 0.0012465686863734893, -0.001713050737178562,
          -0.00501079129024537, -0.008685928829828285, -0.012777118852549577,
          -0.01731728446222318, -0.022323891084748734, -0.027780872985517707,
          -0.03360537151419199, -0.039586630446788645, -0.04527345615413636,
          -0.04976623524941967, -0.051332814029436236, -0.04670979648244089,
          -0.02992910866157955, 0.00834627278103478, 0.06757368359087457,
          0.07695004831992192, -0.045058986420534075, -0.028838642887844768,
          0.30668309108973946, 0.5407560669094325, 0.5116953022752087,
          0.3389883135922821, 0.15697239334297997, 0.04059965536957866,
          -0.024463855271129376, -0.06015334419556084, -0.07622680102286677,
          -0.0793043581904585, -0.07511572427795105, -0.06759871577631399,
          -0.05896867203894013, -0.0503368553875615, -0.0422132942886545,
          -0.03479894795370227, -0.028140603747496593, -0.022211425601807153,
          -0.016952565701173455, -0.012668729091475275, -0.008553585642755254,
          -0.00489974695071882, -0.001652693129829394, 0.0012394575301695049,
          0.0038219037778644133, 0.006133756561190765, 0.008208740150774704,
          0.010075892623749562, 0.011760215824865049, 0.013283255062883796,
          0.014663604385087438, 0.0159173409104287, 0.016733053695929964,
          0.017766665147062134, 0.018710003617794707, 0.019572247547523153,
          0.020361421692874027, 0.021084557322296506, 0.021747827764196943,
          0.022356663259406356, 0.022872678570613474, 0.023385525273261126,
          0.023764726477124663, 0.024195476076278324, 0.024385164795845616,
          0.024743002619652357, 0.024904579695912952, 0.02519920474436302,
          0.02546661839927864, 0.02570836016780407, 0.02592577144504429,
          0.026120012016892128, 0.026200736048967974, 0.02606777292793712,
          0.026189909003981292, 0.026291681924040352, 0.026373491165563957,
          0.026435602296030813, 0.02647814782687228, 0.026501126088400585,
          0.026504398037648043, 0.026487681853415337, 0.026450545107400122,
          0.026392394223961748, 0.02631246085005698, 0.02620978464633912,
          0.026083191874152034, 0.02592565897936336, 0.02574401100821977,
          0.025525925823794267, 0.025263655695028392, 0.024989300644709864,
          0.024677494748194834, 0.024324380806498985, 0.023925405694445512,
          0.023444618748470973, 0.022936103079279697, 0.022362294733430512,
          0.021714063563867105, 0.0209804244690447, 0.020148089248693563,
          0.0191631206994373, 0.017980131112409665, 0.016658814981058732,
          0.0150355370465865, 0.01336985445560971, 0.011429945194186747,
          0.009156563963226356, 0.0064751338341242845, 0.0032920271391578063,
          -0.0005091889097260938, -0.005070216200630487, -0.010560986961986457,
          -0.017146934914952366, -0.02498148976399059, -0.03410643193765691,
          -0.044313646848081874, -0.05106039347145185, -0.060976768719997756,
          -0.06843421965719515, -0.0720396483628944, -0.07128062846013256,
          -0.06705563659934542, -0.061125940345465854, -0.05521671379486265,
          -0.050594802332261, -0.04779552222259374, -0.04720488037631938,
          -0.048882186866967554, -0.05290588635208791, -0.05920507674235126,
          -0.06751843651914187, -0.07718683525038286, -0.0867610981075003,
          -0.09435581301832728, -0.09807107044527191, -0.09710863435895237,
          -0.09235089122052664, -0.08570953075487021, -0.0792251591004837,
          -0.07425237063206114, -0.07168546938562137, -0.07176911952711967,
          -0.0745571959295001, -0.07978753546156526, -0.08685355029202702,
          -0.09447052645498562, -0.10103276212787482, -0.10491046236098614,
          -0.10537962846027474, -0.10330468907073037, -0.10048508819776666,
          -0.09856012795835918, -0.0987692492285203, -0.10158689685868263,
          -0.1069845615516601, -0.11440099128593259, -0.1229162419384949,
          -0.1312948520224338, -0.1382569730684573, -0.14263507479160187,
          -0.14385143959417163, -0.14215168247645477, -0.1385977611732126,
          -0.1346612777224229, -0.1315516991484657, -0.12958413705459676,
          -0.12791584245251109, -0.12485782711843339, -0.11878029882710517,
          -0.1090721093619037, -0.09657432534097125, -0.08292427353267603,
          -0.06967804771425257, -0.05782428151994819, -0.04780128120387075,
          -0.03960783690149589, -0.0331653331223192, -0.028221878172900942,
          -0.024622982093127126, -0.022170497607437993, -0.020725600473844925,
          -0.02013024160805489, -0.020213228744033702, -0.02081076821224921,
          -0.021744246212504877, -0.022931008700836808, -0.024426823876550686,
          -0.02636086650939446, -0.028913069458135078, -0.03221455432506285,
          -0.03636591547086569, -0.041504123904576584, -0.04781757625385996,
          -0.055428540282731614, -0.06417604634238946, -0.07340572001308493,
          -0.08189726384849717, -0.08806329910753104, -0.09045210903131848,
          -0.08836885137726525, -0.08225281210779269, -0.07350300028029876,
          -0.0638348681901938, -0.05464797247297031, -0.04677040855763331,
          -0.04053722404292937, -0.03598547580815738, -0.03302640739251714,
          -0.03156675275540896, -0.0315188094684024, -0.032859466966464086,
          -0.035553237869954325, -0.03951602252943584, -0.04451754866790964,
          -0.05013466109664059, -0.05584156181744983, -0.06178933852801549,
          -0.0676662561056825, -0.07348624407247417, -0.07919479752185071,
          -0.08452942239300759, -0.0894058882769799, -0.09397944248660747,
          -0.09878089675424229, -0.10423892772299531, -0.11034243896722273,
          -0.11635401711419793, -0.12099463343712077, -0.12302008940332243,
          -0.12179271470972336, -0.11732710888789546, -0.11154312310417772,
          -0.10548524229848213, -0.10026423336928525, -0.09645172747501984,
          -0.0941871032926323, -0.09343005659054926, -0.09413070780522742,
          -0.09614964443262178, -0.0991580307596591, -0.10240067063878928,
          -0.10492076581329773, -0.10582573793503819, -0.10431529166490015,
          -0.10107832473843886, -0.09607805954791526, -0.08954723877752678,
          -0.08162666008600367, -0.07251572212328132, -0.06274634181906176,
          -0.05298882867553135, -0.04376624852953199, -0.03547532019714199,
          -0.028017035845409703, -0.021528504834072253, -0.015644027560684927,
          -0.01074621905792393, -0.006448535747191696, -0.003067293338511634,
          -0.0003951563638908834, 0.0016264611665431222, 0.0030731470125073337,
          0.00403651623252179, 0.004708801438807773, 0.005273307279916498,
          0.005291599098044171, 0.005032854033669258, 0.004465460801736619,
          0.0036139991743970312, 0.002607590125156947, 0.00167602452596409,
          0.0010909015517372028, 0.0010769379822836017, 0.0017294342197192863,
          0.0029745110005167663, 0.004601474596568067, 0.006358734694190963,
          0.008062500883528053, 0.009663481663984785, 0.0112089143610999,
          0.012798986389182872, 0.014486493093848495, 0.01621680772934184,
          0.017947451901962546, 0.01959953642695273, 0.021107432209499483,
          0.022463661561638905, 0.023583196673389425, 0.02453177761201577,
          0.025314409043957237, 0.02595072424193274, 0.026458380082618256,
          0.026889200401240473, 0.02727720077718678, 0.027541652304038197,
          0.027818998550005164, 0.027805866486628313, 0.02768997053124185,
          0.027464190465169777, 0.027121086789872087, 0.026656785307296402,
          0.026077091008209506, 0.025403916401429492, 0.02468088230261855,
          0.02394171408865085, 0.023221524551542437, 0.022531913737153665,
          0.021881192288255108, 0.02128189818726514, 0.020728947953946957,
          0.020173770988975038, 0.019596599842323294, 0.01884985719769351,
          0.01793530918884301, 0.01699689883491848, 0.016224807676107716,
          0.01585381033976923, 0.015851476628751245, 0.016296891390703068,
          0.01702809415961633, 0.017944266818813, 0.01889953700123892,
          0.0198317900439549, 0.020783586668289052, 0.021682591574673733,
          0.022576424381170378, 0.023382684810653385, 0.024013028147572175,
          0.02445864434606604, 0.024678505477077207, 0.0247179889888456,
          0.024534624693208038, 0.024313323148163687, 0.024082263034732973,
          0.023990374798471062, 0.02410945765924575, 0.02448513894518771,
          0.024945906446933536, 0.02543758282153983, 0.02580880258338305,
          0.025958253383176186, 0.026008209270662393, 0.02612828094714761,
          0.026318493890648633, 0.02666087231153804, 0.027097317405690314,
          0.02763285423022649, 0.028232326336364306, 0.028904371002117363,
          0.029611787043966158, 0.03036090637710841, 0.031080812497022207,
          0.03174689713576312, 0.03233631725534696, 0.03284290960050219,
          0.03327121977655904, 0.033630598589949254, 0.0339314661475279,
          0.03418349161634656, 0.034394929253071485, 0.03458735507229309,
          0.03473617324275961, 0.034860727427073204, 0.034964242049444504,
          0.03504913037901515, 0.03511711895072095, 0.03519182836977601,
          0.03522838461909429, 0.03528443555582591, 0.03529793428353716,
          0.03530424785380724, 0.03527350828774432, 0.03522169768780544,
          0.03514534145995077, 0.0350399662297014, 0.03491561487451031,
          0.0347436138275742, 0.034516867666469685, 0.03424979547318603,
          0.033932439355894926, 0.03359455351152, 0.03328061867524902,
          0.033055490440516144, 0.03298261467486666, 0.03308923853353158,
          0.03334832089305566, 0.03369662536829465, 0.034069512862708276,
          0.03442272994880601, 0.034734805208534364, 0.03500004874566511,
          0.035221015284577856, 0.03540348954715571, 0.03555385488678374,
          0.0356779552111106, 0.0357807284753947, 0.03586618618593307,
          0.035937523289375654, 0.0359972602152761, 0.03604737722751546,
          0.03609957232759082, 0.03613456786040966, 0.03616367550780477,
          0.036187638887056554, 0.03621820078416936, 0.03623970670755242,
          0.036250806515599795, 0.03625833275870845, 0.036262423168690355,
          0.03626313601165745, 0.03626045346188387, 0.03627718757931547,
          0.036266884316121586, 0.03627526358270603, 0.03625631914820919,
          0.036245149573727535, 0.03621587733306, 0.03618049173564935,
          0.036138006922428585, 0.03608717821346932, 0.03604317352213138,
          0.03597018307194, 0.035882780363824605, 0.03577777131947265,
          0.035651111993254624, 0.03549771233388474, 0.03531125344799047,
          0.03508410971023866, 0.03480758287727551, 0.03448353970385852,
          0.034083932511656, 0.03363744636058849, 0.03312517421742044,
          0.03260341210488503, 0.0321356495427573, 0.031795454426505075,
          0.03163959704994415, 0.03168973362725453, 0.03193333127143042,
          0.03234998194103846, 0.03284028342255379, 0.033358792644868476,
          0.033853714914675766, 0.03429549254195716, 0.03468421700350027,
          0.035000812814600143, 0.03526294544062774, 0.03547927764759439,
          0.035658064316657315, 0.03580643484371741, 0.03593026013406664,
          0.03603426160730104, 0.03612219518466567, 0.03619703803734262,
          0.03626115171104713, 0.036316415519992526, 0.03636433212828186,
          0.03640610976772744, 0.03644272579436591, 0.0364749757164544,
          0.03650351105605059, 0.03652886867660364, 0.03655149359705213,
          0.036571756827819706, 0.03658996939057171, 0.03660639340037514,
          0.036621250875796506, 0.036634730782597456, 0.036646994696757265,
          0.03665818138241675, 0.03666841051238907, 0.036677785707456716,
          0.036686397031581955, 0.036694323050298544, 0.03670163253663396,
          0.03670838589122964, 0.03671463632961832, 0.03672043087893344,
          0.03672581121796011, 0.036743837416226444, 0.03674823031024688,
          0.03675231659346057, 0.03675612235071341, 0.0367596709798196,
          0.03676298351522002, 0.03676607890727711, 0.03676897426398784,
          0.03677168506075774, 0.036774225322947926, 0.0367766077851432,
          0.03677884403045891, 0.03678094461268439, 0.03678291916362873,
          0.036784776487675516, 0.03678652464525312, 0.036788171026676315,
          0.03678972241760383, 0.0367911850571791, 0.036792564689771476,
          0.03679386661110809
        ],
        "fit": [
          0.03860835067784256, 0.03864697992253168, 0.038686838757782956,
          0.038727979925653216, 0.03877045902661726, 0.03881433470749405,
          0.03885966886394618, 0.038906526858858564, 0.03895497775803559,
          0.03900509458480403, 0.03905695459527511, 0.03911063957620358,
          0.03916623616758911, 0.039223836212396786, 0.03928353713603368,
          0.03934544235851035, 0.0394096617425445, 0.03947631208123376,
          0.03954551762934151, 0.03961741068271068, 0.03969213221085292,
          0.039769832548364296, 0.0398506721515027, 0.039934822427040884,
          0.040022466641393965, 0.04011380091903076, 0.040209035340331135,
          0.04030839515037212, 0.040412122091638275, 0.040520475875390136,
          0.040633735808424484, 0.04075220259426687, 0.040876200330501704,
          0.04100607872703131, 0.041142215573636974, 0.04128501948937985,
          0.04143493299123635, 0.04159243592503668, 0.04175804930842367,
          0.041932339643355715, 0.04211592376487244, 0.04230947430369593,
          0.04251372585309525, 0.04272948194570474, 0.042957622964167566,
          0.04319911513119762, 0.043455020750689834, 0.043726509902822355,
          0.044014873833884686, 0.04432154032733717, 0.04464809139825272,
          0.04499628372120537, 0.045368072284891564, 0.045765637869181704,
          0.046191419066878396, 0.046648149729627726, 0.0471389029135152,
          0.04766714264574186, 0.048236785143666014, 0.04885227151022764,
          0.049518654430348696, 0.05024170203478211, 0.0510280229261601,
          0.05188521743790915, 0.052822061604080525, 0.05384873217270027,
          0.054977083458086946, 0.05622099012516206, 0.05759677445245384,
          0.059123742691095514, 0.06082486349268304, 0.06272763299906228,
          0.06486518752632417, 0.0672777480206988, 0.07001451395045138,
          0.07313617318438664, 0.07671826679957916, 0.08085575660226878,
          0.08566930946542, 0.09131407117016907, 0.09799211191667806,
          0.1059703867706495, 0.11560714339800528, 0.12739154080757983,
          0.1420043845833614, 0.1604133695532035, 0.18402590690317852,
          0.21493964710350974, 0.25635949366285715, 0.31329020351754194,
          0.3936003031031032, 0.5083462727810076, 0.6577376180170725,
          0.769257740627577, 0.7549410135794306, 0.8711613571121248,
          1.2796560640626955, 1.5407560669094325, 1.4846682752482019,
          1.2390568005211697, 0.9573043831821693, 0.7332618562758604,
          0.5660621526868566, 0.4402165386848348, 0.34768055801487524,
          0.28108191973097774, 0.23297147007370084, 0.19751095256094575,
          0.17074368012122587, 0.1500856545914835, 0.13382882519630657,
          0.12081603080910065, 0.11024356203204132, 0.10154032556648229,
          0.09429209458893542, 0.08819281816710392, 0.08301257764197063,
          0.07857603488666345, 0.07474764490360435, 0.07142132239230033,
          0.06851309869435465, 0.06595582286083682, 0.06369528336516989,
          0.06168733237666661, 0.05989572763146986, 0.058290494710505965,
          0.056846671338915813, 0.05554333531033817, 0.05436284521396752,
          0.053290242405320536, 0.05231277628313617, 0.051419524677503284,
          0.05060108819767443, 0.04984934253145293, 0.049157236479792234,
          0.04851862633062151, 0.047928139291528976, 0.04738106030061041,
          0.046873237753518204, 0.04640100461991954, 0.04596111214505909,
          0.04555067389391202, 0.045167118334944564, 0.04480814850639833,
          0.04447170758175385, 0.04415594936881983, 0.04385921295105882,
          0.043580000819717545, 0.04331695995832541, 0.04306886543276161,
          0.042834606114726816, 0.04261317222749423, 0.042403644452933174,
          0.04220518438010551, 0.04201702610990684, 0.041838468858591556,
          0.04166887042665081, 0.04150764141926019, 0.041354240121069766,
          0.04120816794203197, 0.04106896536270458, 0.04093620831739878,
          0.04080950496196555, 0.04068849278017797, 0.040572835988774904,
          0.04046222320645263, 0.04035636535656443, 0.04025499377713027,
          0.040157858515066015, 0.040064726784394857, 0.039975381570670675,
          0.039889620365980136, 0.03980725402074589, 0.039728105700167216,
          0.03965200993454102, 0.03957881175393432, 0.039508365898753756,
          0.03944053609869895, 0.039375194413413146, 0.03931222062887101,
          0.03925150170418343, 0.0391929312640638, 0.039136409132698856,
          0.03908184090520841, 0.03902913755326957, 0.03897821506182779,
          0.03892899409412563, 0.038881399682554586, 0.03883536094307967,
          0.038790810811204904, 0.038747685797642636, 0.03870592576202395,
          0.03866547370314385, 0.03862627556437453, 0.03858828005300641,
          0.038551438472388844, 0.0385157045658448, 0.03848103437142493,
          0.03844738608664931, 0.03841471994245968, 0.03838299808567211,
          0.038352184469281465, 0.038322244750023826, 0.03829314619265324,
          0.03826485758043451, 0.03823734913139495, 0.03821059241991556,
          0.03818456030327605, 0.03815922685279918, 0.038134567289268465,
          0.03811055792231831, 0.0380871760935205, 0.0380644001229109,
          0.03804220925872129, 0.038020583630098304, 0.03799950420260871,
          0.037978952736344385, 0.037958911746455465, 0.0379393644659516,
          0.03792029481062402, 0.03790168734595098, 0.03788352725585971,
          0.03786580031322663, 0.03784849285200628, 0.03783159174088696,
          0.037815084358378104, 0.03779895856924145, 0.037783202702183605,
          0.03776780552873331, 0.03775275624323242, 0.0377380444438736,
          0.03772366011472293, 0.0377095936086691, 0.03769583563124537,
          0.03768237722527315, 0.03766920975628041, 0.03765632489864998,
          0.0376437146224568, 0.03763137118095483, 0.037619287098677595,
          0.037607455160117736, 0.03759586839895421, 0.03758452008779653,
          0.03757340372841808, 0.03756251304245224, 0.03755184196252595,
          0.03754138462380785, 0.03753113535594867, 0.037521088675393346,
          0.037511239278045394, 0.0375015820322651, 0.03749211197218447,
          0.03748282429132247, 0.037473714336485345, 0.037464777601937595,
          0.03745600972382989, 0.03744740647487106, 0.0374389637592321,
          0.037430677607670645, 0.03742254417286509, 0.03741455972494814,
          0.037406720647230086, 0.03739902343210267, 0.037391464677114836,
          0.03738404108121226, 0.03737674944113278, 0.03736958664795046,
          0.03736254968376132, 0.03735563561850411, 0.037348841606909836,
          0.03734216488557428, 0.03733560277014762, 0.03732915265263603,
          0.03732281199881024, 0.03731657834571585, 0.03731044929928143,
          0.03730442253201954, 0.0372984957808169, 0.03729266684480957,
          0.037286933583339524, 0.03728129391398905, 0.037275745810689716,
          0.03727028730190237, 0.037264916468865567, 0.03725963144390916,
          0.037254430408830475, 0.03724931159333036, 0.03724427327350662,
          0.03723931377040245, 0.03723443144860758, 0.037229624714909905,
          0.03722489201699566, 0.03722023184219596, 0.03721564271627803,
          0.03721112320227918, 0.03720667189938179, 0.03720228744182777,
          0.03719796849787091, 0.0371937137687654, 0.03718952198778955,
          0.0371853919193027, 0.037181322357834695, 0.0371773121272061,
          0.03717336007967831, 0.037169465095132276, 0.037165626080274766,
          0.037161841967871034, 0.03715811171600314, 0.0371544343073526,
          0.03715080874850682, 0.03714723406928799, 0.037143709322104146,
          0.0371402335813211, 0.037136805942654616, 0.03713342552258228,
          0.03713009145777413, 0.03712680290454126, 0.03712355903830218,
          0.03712035905306582, 0.03711720216093084, 0.037114087591600634,
          0.03711101459191332, 0.03710798242538654, 0.03710499037177596,
          0.03710203772664773, 0.037099123800963724, 0.037096247920679504,
          0.03709340942635458, 0.037090607672774285, 0.037087842028583146,
          0.037085111875929146, 0.03708241661011864, 0.03707975563928152,
          0.03707712838404622, 0.03707453427722437, 0.037071972763504636,
          0.037069443299155534, 0.03706694535173685, 0.03706447839981944,
          0.0370620419327131, 0.037059635450202244, 0.037057258462289175,
          0.03705491048894462, 0.03705259105986534, 0.03705029971423867,
          0.037048036000513575, 0.037045799476178184, 0.03704358970754354,
          0.037041406269533304, 0.03703924874547937, 0.03703711672692303,
          0.03703500981342168, 0.03703292761236073, 0.03703086973877074,
          0.03702883581514943, 0.03702682547128857, 0.03702483834410551,
          0.037022874077479215, 0.03702093232209072, 0.03701901273526781,
          0.03701711498083383, 0.037015238728960474, 0.037013383656024516,
          0.037011549444468196, 0.03700973578266335, 0.037007942364779035,
          0.03700616889065256, 0.03700441506566394, 0.03700268060061349,
          0.03700096521160263, 0.03699926861991766, 0.0369975905519166,
          0.036995930738918804, 0.03699428891709742, 0.03699266482737455,
          0.03699105821531904, 0.036989468831046826, 0.03698789642912375,
          0.03698634076847083, 0.03698480161227184, 0.03698327872788318,
          0.03698177188674596, 0.036980280864300226, 0.036978805439901334,
          0.036977345396738276, 0.03697590052175404, 0.036974470605567904,
          0.03697305544239952, 0.036971654829994934, 0.03697026856955431,
          0.03696889646566134, 0.03696753832621442, 0.036966193962359395,
          0.036964863188423895, 0.03696354582185323, 0.036962241683147795,
          0.036960950595801886, 0.03695967238624402, 0.036958406883778556,
          0.03695715392052874, 0.036955913331381, 0.03695468495393056,
          0.03695346862842829, 0.03695226419772876, 0.03695107150723949,
          0.03694989040487132, 0.03694872074098997, 0.03694756236836857,
          0.0369464151421414, 0.03694527891975857, 0.03694415356094174,
          0.036943038927640795, 0.03694193488399154, 0.0369408412962743,
          0.036939758032873395, 0.036938684964237564, 0.03693762196284122,
          0.03693656890314657, 0.03693552566156653, 0.0369344921164285,
          0.036933468147938825, 0.03693245363814816, 0.03693144847091744,
          0.036930452531884664, 0.03692946570843236, 0.03692848788965576,
          0.03692751896633163, 0.036926558830887767, 0.03692560737737313,
          0.036924664501428645, 0.03692373010025855, 0.03692280407260239,
          0.036921886318707596, 0.03692097674030259, 0.03692007524057051,
          0.03691918172412342, 0.036918296096977096, 0.0369174182665263,
          0.03691654814152057, 0.03691568563204053, 0.03691483064947459,
          0.03691398310649628, 0.03691314291704189, 0.03691230999628864,
          0.03691148426063324, 0.03691066562767097, 0.03690985401617509,
          0.03690904934607665, 0.03690825153844482, 0.03690746051546746,
          0.03690667620043221, 0.03690589851770784, 0.03690512739272604,
          0.03690436275196354, 0.0369036045229246, 0.036902852634123795,
          0.036902107015069185, 0.03690136759624579, 0.03690063430909941,
          0.036899907086020665, 0.0368991858603295, 0.03689847056625984,
          0.03689776113894461, 0.03689705751440103, 0.036896359629516214,
          0.036895667422032964, 0.03689498083053594, 0.03689429979443798,
          0.03689362425396679, 0.03689295415015181, 0.03689228942481132,
          0.03689163002053983, 0.036890975880695696, 0.03689032694938893,
          0.03688968317146929, 0.03688904449251454, 0.03688841085881896,
          0.03688778221738205, 0.03688715851589745, 0.03688653970274206,
          0.036885925726965356, 0.036885316538278895, 0.03688471208704604,
          0.03688411232427181, 0.03688351720159298, 0.03688292667126836,
          0.036882340686169135, 0.03688175919976954, 0.036881182166137595,
          0.03688060953992603, 0.03688004127636341, 0.03687947733124529,
          0.036878917660925756, 0.036878362222308864, 0.0368778109728404,
          0.03687726387049973, 0.03687672087379175, 0.03687618194173906,
          0.036875647033874234, 0.03687511611023219, 0.03687458913134275,
          0.036874066058223284, 0.036873546852371535, 0.03687303147575851,
          0.036872519890821506, 0.03687201206045729, 0.036871507948015345,
          0.03687100751729129, 0.03687051073252036, 0.036870017558371,
          0.03686952795993863, 0.0368690419027394, 0.0368685593527042,
          0.03686808027617262, 0.0368676046398871, 0.03686713241098719,
          0.03686666355700385, 0.036866198045853824, 0.036865735845834254,
          0.03686527692561718, 0.036864821254244305, 0.03686436880112172,
          0.03686391953601481, 0.03686347342904317, 0.03686303045067566,
          0.036862590571725515, 0.03686215376334552, 0.0368617199970233,
          0.03686128924457667, 0.03686086147814901, 0.03686043667020484,
          0.036860014793525325, 0.03685959582120395, 0.03685917972664218,
          0.03685876648354534, 0.03685835606591833, 0.03685794844806164,
          0.03685754360456728, 0.03685714151031482, 0.03685674214046753,
          0.03685634547046849, 0.03685595147603685, 0.03685556013316411,
          0.036855171418110455, 0.03685478530740117, 0.03685440177782307,
          0.036854020806421035, 0.03685364237049457, 0.0368532664475944,
          0.03685289301551919, 0.036852522052312195, 0.03685215353625812,
          0.03685178744587986, 0.03685142375993543, 0.03685106245741485,
          0.03685070351753712, 0.03685034691974725, 0.03684999264371327,
          0.03684964066932339, 0.0368492909766831, 0.036848943546112393,
          0.03684859835814296, 0.036848255393515494, 0.03684791463317699,
          0.03684757605827811, 0.036847239650170546, 0.036846905390404486,
          0.03684657326072607, 0.03684624324307491, 0.03684591531958159,
          0.036845589472565325, 0.0368452656845315, 0.036844943938169374,
          0.03684462421634974, 0.036844306502122656, 0.0368439907787152,
          0.036843677029529225
        ],
        "pseudovoigt_1": [
          0.0010203787554590932, 0.0010414867929510528, 0.0010632564601278677,
          0.0010857156923063493, 0.0011088939144357798, 0.0011328221374159867,
          0.001157533061758024, 0.0011830611892340247, 0.0012094429432274996,
          0.001236716798567391, 0.0012649234217094027, 0.0012941058222175556,
          0.0013243095165987808, 0.0013555827056549597, 0.0013879764666417237,
          0.0014215449616632964, 0.0014563456638896925, 0.0014924396033590538,
          0.001529891634326391, 0.001568770726343699, 0.0016091502815087193,
          0.0016511084806048093, 0.0016947286611770133, 0.0017400997309551908,
          0.0017873166204501656, 0.001836480779020952, 0.0018877007192486866,
          0.001941092615066285, 0.001996780959793788, 0.0020548992910319514,
          0.002115590990287214, 0.0021790101662591196, 0.00224532263193951,
          0.0023147069870783337, 0.0023873558191960303, 0.002463477038205273,
          0.002543295361891246, 0.002627053972044079, 0.0027150163640052125,
          0.002807468415860106, 0.0029047207075780504, 0.0030071111251808147,
          0.003115007790655349, 0.0032288123649816146, 0.0033489637795326706,
          0.0034759424604748923, 0.00361027512196472, 0.0037525402172909773,
          0.003903374153127332, 0.0040634783913331045, 0.004233627586015814,
          0.0044146789317775345, 0.004607582933383012, 0.004813395848995123,
          0.005033294110508854, 0.0052685910877879535, 0.0055207566418594145,
          0.005791440009338805, 0.006082496681716756, 0.006396020095382287,
          0.006734379140247754, 0.00710026273826672, 0.0074967330535409115,
          0.007927289293891407, 0.008395944577746, 0.008907319008019672,
          0.009466752968403491, 0.010080445808964776, 0.010755626617170532,
          0.01150076581777973, 0.012325839109600827, 0.013242659014067735,
          0.01426529449287676, 0.015410606294245286, 0.016698935805936184,
          0.018154999573410845, 0.019809062330407034, 0.021698491546744223,
          0.02386984107680995, 0.02638167838137046, 0.029308471781395704,
          0.032746012390989385, 0.03681909528587662, 0.04169258710013812,
          0.047587669642544246, 0.054806163227427096, 0.06376775098873315,
          0.07506830401988039, 0.08957358499248821, 0.1085735272966188,
          0.13403919458094876, 0.16902639784460446, 0.218123416140869,
          0.28727222905756417, 0.38200899053722776, 0.5066139952417967,
          0.6690083240842193, 0.8629428281200358, 0.9827433697474828,
          0.8986257236264162, 0.7065903576489863, 0.5357310897879607,
          0.40439010734055114, 0.3040361302823388, 0.23015392043296964,
          0.17754368511019047, 0.14015461899913745, 0.11307194304344162,
          0.09296404147700855, 0.07768000538891869, 0.06581841656915285,
          0.056443553354201176, 0.048914530654551605, 0.04278195815347782,
          0.037723942467631236, 0.03350544242539946, 0.02995183190218515,
          0.02693131886511055, 0.024343012951228156, 0.02210867354230479,
          0.020166903989532105, 0.018469001685053797, 0.016975948165187722,
          0.01565619651336172, 0.014484024521478765, 0.01343829475159477,
          0.012501510929102073, 0.011659092671368413, 0.010898812840859605,
          0.010210357261964106, 0.009584977386235472, 0.009015214193185597,
          0.008494677144200859, 0.008017866019194948, 0.007580026404516575,
          0.007177031773237084, 0.006805286719008788, 0.0064616471226569975,
          0.006143353953468091, 0.005847978111455222, 0.005573374258213927,
          0.005317642002809423, 0.005079093135240759, 0.004856223855465166,
          0.004647691147203988, 0.004452292605160974, 0.00426894915122208,
          0.004096690176795282, 0.003934640730142415, 0.0037820104335519,
          0.003638083868753228, 0.0035022122126122353, 0.0033738059408507447,
          0.0032523284468619416, 0.0031372904468736484, 0.0030282450627210113,
          0.0029247834901055835, 0.002826531174061615, 0.0027331444249222223,
          0.0026443074177814148, 0.0025597295266089797, 0.002479142951059257,
          0.0024023005998381267, 0.002328974199432072, 0.002258952601204106,
          0.002192040263443452, 0.002128055888017703, 0.002066831193899841,
          0.0020082098120957448, 0.0019520462884375608, 0.0018982051823815903,
          0.0018465602513961785, 0.0017969937117783637, 0.0017493955678262003,
          0.0017036630022400174, 0.0016596998214506973, 0.0016174159502931479,
          0.0015767269710730218, 0.001537553702626637, 0.0014998218154584856,
          0.0014634614794666022, 0.0014284070411411628, 0.0013945967274524675,
          0.0013619723739367374, 0.0013304791747467074, 0.0013000654526631027,
          0.0012706824472663656, 0.0012422841196486482, 0.001214826972206804,
          0.0011882698822003306, 0.0011625739478859835, 0.0011377023461548953,
          0.0011136202007001725, 0.0010902944598342968, 0.0010676937831576906,
          0.0010457884363533484, 0.0010245501934485835, 0.0010039522459444213,
          0.0009839691182667821, 0.000964576589041879, 0.0009457516177419135,
          0.0009274722762865196, 0.0009097176852210864, 0.000892467954125332,
          0.0008757041259347721, 0.0008594081248842378, 0.0008435627078067051,
          0.0008281514185425766, 0.0008131585452344874, 0.0007985690803008134,
          0.0007843686828976236, 0.0007705436436938446, 0.0007570808517981837,
          0.0007439677636889294, 0.0007311923740092102, 0.0007187431881008322,
          0.0007066091961594315, 0.0006947798489024892, 0.0006832450346498692,
          0.000671995057723946, 0.000661020618083217, 0.0006503127921095659,
          0.0006398630144751044, 0.0006296630610198226, 0.0006197050325761794,
          0.0006099813396812568, 0.0006004846881212595, 0.0005912080652569796,
          0.0005821447270823841, 0.0005732881859717486, 0.0005646321990738001,
          0.0005561707573141163, 0.0005478980749696234, 0.0005398085797814416,
          0.0005318969035745404, 0.0005241578733547348, 0.0005165865028554681,
          0.000509177984508597, 0.0005019276818150538, 0.0004948311220927875,
          0.0004878839895808128, 0.00048108211887952707, 0.0004744214887086856,
          0.0004678982159655772, 0.0004615085500670163, 0.0004552488675597643,
          0.00044911566698492463, 0.0004431055639827278, 0.00043721528662493437,
          0.00043144167096283983, 0.0004257816567795755, 0.0004202322835360662,
          0.00041479068650061303, 0.00040945409305266655, 0.0004042198191518837,
          0.0003990852659640781, 0.00039404791663614683, 0.000389105333212505,
          0.0003842551536859756, 0.0003794950891764781, 0.00037482292123122533,
          0.00037023649924048367, 0.0003657337379632825, 0.0003613126151577531,
          0.00035697116931107816, 0.0003527074974642892, 0.0003485197531274167,
          0.0003444061442807223, 0.00034036493145798166, 0.000336394425907987,
          0.0003324929878306449, 0.00032865902468422946, 0.0003248909895605308,
          0.00032118737962480247, 0.00031754673461757476, 0.00031396763541554105,
          0.00031044870264887616, 0.0003069885953724676, 0.0003035860097886727,
          0.00030023967801933094, 0.0002969483669248714, 0.00029371087696846424,
          0.0002905260411232634, 0.00028739272382087946, 0.00028430981993931876,
          0.0002812762538287026, 0.00027829097837316226, 0.00027535297408738674,
          0.0002724612482463635, 0.0002696148340469311, 0.0002668127897998147,
          0.0002640541981508929, 0.00026133816533048597, 0.00025866382042952424,
          0.0002560303147015, 0.00025343682088915874, 0.0002508825325749333,
          0.00024836666355417057, 0.00024588844723023634, 0.00024344713603063634,
          0.00024104200084331835, 0.00023867233047236428, 0.00023633743111231326,
          0.00023403662584039095, 0.00023176925412594983, 0.00022953467135645997,
          0.00022733224837941186, 0.00022516137105952637, 0.00022302143985068865,
          0.0002209118693820499, 0.00021883208805776295, 0.00021678153766984168,
          0.0002147596730236539, 0.00021276596157557924, 0.00021079988308238335,
          0.0002088609292618749, 0.0002069486034644358, 0.00020506242035502612,
          0.00020320190560528306, 0.00020136659559535247, 0.00019955603712509964,
          0.00019776978713436497, 0.00019600741243194425, 0.0001942684894329796,
          0.00019255260390446782, 0.00019085935071860011, 0.00018918833361365685,
          0.00018753916496219586, 0.0001859114655462824, 0.000184304864339513,
          0.00018271899829560477, 0.00018115351214332114, 0.0001796080581875204,
          0.00017808229611611718, 0.00017657589281275867, 0.00017508852217502165,
          0.00017361986493794548, 0.00017216960850272364, 0.00017073744677038115,
          0.0001693230799802734, 0.00016792621455324642, 0.00016654656293930737,
          0.000165183843469655, 0.0001638377802129307, 0.0001625081028355506,
          0.00016119454646598935, 0.0001598968515628859, 0.00015861476378685156,
          0.00015734803387585777, 0.00015609641752409572, 0.00015485967526419154,
          0.00015363757235267668, 0.00015242987865860604, 0.00015123636855523056,
          0.0001500568208146234, 0.00014889101850517383, 0.00014773874889185436,
          0.00014659980333918068, 0.000145473977216777, 0.00014436106980747224,
          0.0001432608842178445, 0.00014217322729114377, 0.00014109790952251833,
          0.0001400347449764779, 0.00013898355120652256, 0.00013794414917687724,
          0.00013691636318626557, 0.00013590002079366407, 0.00013489495274597764,
          0.0001339009929075806, 0.00013291797819166658, 0.00013194574849335715,
          0.00013098414662451486, 0.0001300330182502138, 0.000129092211826818,
          0.00012816157854162277, 0.0001272409722540113, 0.00012633024943808823,
          0.00012542926912674168, 0.00012453789285709891, 0.0001236559846173318,
          0.00012278341079477751, 0.00012192004012533411, 0.00012106574364409854,
          0.00012022039463720957, 0.00011938386859486416, 0.00011855604316547333,
          0.00011773679811092724, 0.00011692601526293749, 0.00011612357848042899,
          0.00011532937360795038, 0.00011454328843507752, 0.00011376521265678119,
          0.00011299503783473469, 0.00011223265735953354, 0.00011147796641380593,
          0.00011073086193618655, 0.00010999124258613457, 0.00010925900870956903,
          0.00010853406230530401, 0.00010781630699225922, 0.00010710564797742818,
          0.00010640199202458136, 0.00010570524742368826, 0.00010501532396103588,
          0.00010433213289002971, 0.00010365558690265538, 0.00010298560010158685,
          0.00010232208797292337, 0.00010166496735953913, 0.00010101415643502935,
          0.00010036957467823919, 9.97311428483589e-5, 9.909878296057192e-5,
          9.847241826224124e-5, 9.785197320962143e-5, 9.723737344508203e-5,
          9.662854577483034e-5, 9.602541814712053e-5, 9.542791963093752e-5,
          9.483598039514337e-5, 9.424953168807536e-5, 9.366850581758324e-5,
          9.309283613149729e-5, 9.252245699851377e-5, 9.195730378948998e-5,
          9.139731285913727e-5, 9.084242152810365e-5, 9.029256806543505e-5,
          8.974769167140809e-5, 8.920773246072315e-5, 8.867263144605134e-5,
          8.814233052192477e-5, 8.761677244896393e-5, 8.709590083843238e-5,
          8.657966013711259e-5, 8.60679956124938e-5, 8.556085333826623e-5,
          8.505818018011227e-5, 8.455992378179057e-5, 8.406603255150296e-5,
          8.357645564854049e-5, 8.309114297019981e-5, 8.261004513896578e-5,
          8.213311348995183e-5, 8.166030005859441e-5, 8.119155756859382e-5,
          8.072683942009731e-5, 8.026609967811742e-5, 7.98092930611819e-5,
          7.9356374930208e-5, 7.890730127759839e-5, 7.846202871655102e-5,
          7.802051447058042e-5, 7.758271636324459e-5, 7.714859280807296e-5,
          7.671810279869102e-5, 7.629120589913739e-5, 7.586786223436873e-5,
          7.544803248094878e-5, 7.503167785791701e-5, 7.461876011783346e-5,
          7.420924153799472e-5, 7.380308491181963e-5, 7.340025354039793e-5,
          7.300071122420099e-5, 7.260442225494975e-5, 7.221135140763655e-5,
          7.182146393269764e-5, 7.143472554833376e-5, 7.105110243297433e-5,
          7.067056121788353e-5, 7.029306897990404e-5, 6.991859323433652e-5,
          6.954710192795112e-5, 6.917856343212896e-5, 6.881294653613008e-5,
          6.8450220440486e-5, 6.809035475051331e-5, 6.773331946994714e-5,
          6.737908499468983e-5, 6.702762210667536e-5, 6.667890196784397e-5,
          6.633289611422732e-5, 6.598957645014013e-5, 6.564891524247695e-5,
          6.531088511511182e-5, 6.497545904339849e-5, 6.464261034876926e-5,
          6.431231269343022e-5, 6.398454007515145e-5, 6.36592668221497e-5,
          6.333646758806192e-5, 6.301611734700765e-5, 6.26981913887388e-5,
          6.238266531387477e-5, 6.206951502922127e-5, 6.175871674317105e-5,
          6.145024696118516e-5, 6.114408248135311e-5, 6.084020039003013e-5,
          6.05385780575499e-5, 6.023919313401189e-5, 5.994202354514116e-5,
          5.964704748821969e-5, 5.935424342808726e-5, 5.906359009321115e-5,
          5.877506647182303e-5, 5.848865180812158e-5, 5.820432559853976e-5,
          5.792206758807556e-5, 5.764185776668465e-5, 5.7363676365734294e-5,
          5.708750385451647e-5, 5.681332093682021e-5, 5.6541108547561035e-5,
          5.627084784946696e-5, 5.600252022981951e-5, 5.5736107297249397e-5,
          5.5471590878585174e-5, 5.5208953015754167e-5, 5.494817596273455e-5,
          5.468924218255787e-5, 5.4432134344360746e-5, 5.417683532048495e-5,
          5.39233281836252e-5, 5.367159620402306e-5, 5.342162284670725e-5,
          5.317339176877831e-5, 5.292688681673749e-5, 5.268209202385884e-5,
          5.243899160760396e-5, 5.219756996707819e-5, 5.19578116805274e-5,
          5.1719701502875656e-5, 5.1483224363301716e-5, 5.1248365362854474e-5,
          5.101510977210615e-5, 5.078344302884297e-5, 5.055335073579262e-5,
          5.032481865838723e-5, 5.0097832722562e-5, 4.98723790125883e-5,
          4.9648443768941085e-5, 4.942601338619959e-5, 4.920507441098051e-5,
          4.898561353990419e-5, 4.8767617617591966e-5, 4.85510736346947e-5,
          4.83359687259519e-5, 4.812229016828107e-5, 4.791002537889618e-5,
          4.7699161913455596e-5, 4.748968746423786e-5, 4.72815898583461e-5,
          4.707485705593939e-5, 4.686947714849163e-5, 4.666543835707626e-5,
          4.646272903067771e-5, 4.626133764452818e-5, 4.60612527984696e-5,
          4.586246321534025e-5, 4.566495773938598e-5, 4.5468725334694975e-5,
          4.5273755083656305e-5, 4.508003618544137e-5, 4.488755795450798e-5,
          4.469630981912715e-5, 4.4506281319931255e-5, 4.431746210848412e-5,
          4.4129841945872115e-5, 4.3943410701316335e-5, 4.375815835080485e-5,
          4.357407497574543e-5, 4.339115076163789e-5, 4.320937599676614e-5,
          4.302874107090888e-5
        ],
        "pseudovoigt_2": [
          0.0008192445898919191, 0.0008367657970890763, 0.0008548549651635387,
          0.0008735369008553154, 0.0008928377796899282, 0.0009127852375865147,
          0.0009334084696966048, 0.000954738337132994, 0.0009768074823165388,
          0.0009996504537450903, 0.0010233038410741566, 0.0010478064214944763,
          0.001073199318498782, 0.001099526174250279, 0.001126833336900406,
          0.0011551700643555025, 0.0011845887461632576, 0.0012151451453831575,
          0.0012468986625235724, 0.0012799126238754273, 0.0013142545968526543,
          0.0013499967352679399, 0.001387216157834144, 0.0014259953635941418,
          0.0014664226884522518, 0.0015085928075182593, 0.0015526072885909013,
          0.0015985752028142852, 0.0016466137993529396, 0.0016968492518666329,
          0.00174941748564572, 0.0018044650955162072, 0.0018621503660706433,
          0.0019226444074614303, 0.001986132421949395, 0.002052815118683034,
          0.002122910296853553, 0.002196654620501058, 0.002274305611926903,
          0.0023561438950040663, 0.00244247572480284, 0.0025336358460235665,
          0.0026299907299483535, 0.0027319422482315783, 0.0028399318521433437,
          0.002954445338231177, 0.003076018296233562, 0.0032052423530398257,
          0.0033427723482658076, 0.0034893346035125153, 0.003645736479745359,
          0.003812877456936287, 0.003991762019017006, 0.00418351468769503,
          0.004389397623877995, 0.004610831309348223, 0.0048494189391642345,
          0.005106975303911505, 0.005385561129457711, 0.005687524082353807,
          0.006015547957609393, 0.006372711964023837, 0.0067625625401276385,
          0.007189200811526193, 0.007657389693842981, 0.008172685832189044,
          0.008741603157191904, 0.009371816983705738, 0.01007242050279176,
          0.010854249540824236, 0.011730297050590668, 0.012716246652502995,
          0.013831165700955852, 0.015098414393961961, 0.016546850812023648,
          0.018212446278484253, 0.02014047713668057, 0.022388537723033,
          0.02503074105611849, 0.028163665456307063, 0.03191491280279081,
          0.03645564704716857, 0.04201932077963711, 0.04893022637495016,
          0.057647987608325624, 0.06883847899328488, 0.08348942858195167,
          0.10310261575013842, 0.13001718109380564, 0.16794791756021857,
          0.2227902677692082, 0.30247621542621883, 0.40144916094629907,
          0.43154170834763916, 0.2657736647929631, 0.13735546223617767,
          0.3031323769667468, 0.4387246557498286, 0.3856966266613826,
          0.287260762361435, 0.21216596283786704, 0.16066058685292614,
          0.12490027784170292, 0.09941163318863112, 0.08075790985307471,
          0.0667695072865715, 0.056048123742067885, 0.0476702821850126,
          0.04101091131172576, 0.03563692187007328, 0.031241681294662142,
          0.02760375012240792, 0.024560304044998163, 0.021989640080512924,
          0.019799424788812636, 0.017918648409212902, 0.01629201840729393,
          0.014875988689061358, 0.013635904619884641, 0.012543921517503984,
          0.011577467372330999, 0.01071809384329147, 0.009950607867490614,
          0.009262408530813348, 0.008642975777499548, 0.008083472626419647,
          0.007576433077322195, 0.007115515306478207, 0.006695305040616366,
          0.006311157810864881, 0.00595907156440915, 0.00563558315182614,
          0.005337683720982022, 0.005062749179766427, 0.004808482742784108,
          0.00457286722489288, 0.0043541252400286405, 0.004150685845461861,
          0.003961156467558566, 0.0037842991759727703, 0.00361901055435361,
          0.003464304558611049, 0.0033192978672122553, 0.0031831973184416134,
          0.0030552891020583146, 0.0029349294311673034, 0.0028215364673451846,
          0.0027145833104307124, 0.002613591895691443, 0.0025181276667181627,
          0.0024277949134820357, 0.0023422326823904433, 0.002261111179590879,
          0.0021841286007520224, 0.002111008330541643, 0.0020414964633789943,
          0.00197535960405368, 0.0019123829127070204, 0.0018523683636559967,
          0.0017951331917590032, 0.0017405085036040493, 0.001688338033847974,
          0.0016384770296358762, 0.0015907912482543527, 0.0015451560550792498,
          0.001501455610517629, 0.0014595821360551763, 0.0014194352507388842,
          0.001380921370478721, 0.0013439531634657467, 0.001308449055797535,
          0.0012743327820924075, 0.0012415329764759774, 0.0012099827998494697,
          0.0011796195998094558, 0.0011503845999920783, 0.001122222615969059,
          0.0010950817951343758, 0.0010689133782949604, 0.0010436714809209757,
          0.0010193128922252783, 0.0009957968904310904, 0.0009730850727548365,
          0.0009511411987801194, 0.0009299310460313121, 0.0009094222766731369,
          0.0008895843143677206, 0.0008703882304143916, 0.0008518066383813138,
          0.0008338135965130208, 0.0008163845172651001, 0.0007994960833775104,
          0.0007831261699521231, 0.0007672537720486825, 0.0007518589373571695,
          0.0007369227035439478, 0.0007224270399046658, 0.0007083547929889494,
          0.0006946896358909787, 0.000681416020926253, 0.0006685191354386475,
          0.0006559848605033951, 0.0006437997323111913, 0.0006319509060363619,
          0.0006204261220081892, 0.0006092136740191636, 0.0005983023796173097,
          0.0005876815522419211, 0.0005773409750731563, 0.0005672708764760948,
          0.0005574619069291377, 0.0005479051173351085, 0.0005385919386211707,
          0.0005295141625407996, 0.0005206639235975471, 0.0005120336820163234,
          0.000503616207693405, 0.0004954045650614196, 0.0004873920988101802,
          0.0004795724204085242, 0.0004719393953762153, 0.0004644871312585911,
          0.00045720996625997327, 0.0004501024584949169, 0.0004431593758192281,
          0.000436375686205288, 0.0004297465486286445, 0.00042326730443507216,
          0.0004169334691593754, 0.00041074072476911857, 0.00040468491230825476,
          0.00039876202491726307, 0.00039296820120793616, 0.0003872997189723749,
          0.000381752989207063, 0.00037632455043411933, 0.0003710110633029586,
          0.00036580930545664965, 0.000360716166648243, 0.0003557286440932607,
          0.0003508438380453769, 0.0003460589475831372, 0.0003413712665962839,
          0.00033677817996095676, 0.00033227715989367807, 0.000327865762474643,
          0.0003235416243313791, 0.00031930245947438805, 0.0003151460562768576,
          0.000311070274590996, 0.000307073042993973, 0.0003031523561568577,
          0.0002993062723303061, 0.00029553291094112677, 0.0002918304502941642,
          0.0002881971253742633, 0.0002846312257433636, 0.0002811310935280472,
          0.0002776951214931226, 0.0002743217511970658, 0.000271009471225369,
          0.0002677568154980567, 0.00026456236164783693, 0.0002614247294655338,
          0.0002583425794096339, 0.00025531461117694063, 0.00025233956233149444,
          0.00024941620698905174, 0.00024654335455457586, 0.0002437198485103028,
          0.00024094456525208628, 0.00023821641297183392, 0.0002355343305839605,
          0.00023289728669388803, 0.0002303042786067233, 0.00022775433137432985,
          0.00022524649687910995, 0.00022277985295288472, 0.00022035350252934765,
          0.00021796657282863548, 0.00021561821457263383, 0.00021330760122970053,
          0.00021103392828755466, 0.00020879641255313447, 0.00020659429147828952,
          0.0002044268225102226, 0.00020229328246564862, 0.00020019296692768643,
          0.00019812518966454373, 0.00019608928206910208, 0.00019408459261854435,
          0.0001921104863532133, 0.00019016634437391957, 0.0001882515633569599,
          0.00018636555508613352, 0.00018450774600107993, 0.00018267757676129133,
          0.0001808745018251818, 0.00017909798904361924, 0.0001773475192673578,
          0.00017562258596782925, 0.00017392269487077533, 0.00017224736360222802,
          0.00017059612134636372, 0.00016896850851477797, 0.00016736407642674843,
          0.0001657823870000694, 0.00016422301245206124, 0.00016268553501037347,
          0.00016116954663321709, 0.00015967464873867577, 0.00015820045194276077,
          0.00015674657580588985, 0.0001553126485874787, 0.00015389830700835412,
          0.00015250319602070042, 0.0001511269685852717, 0.0001497692854556061,
          0.00014842981496899225, 0.00014710823284394854, 0.00014580422198398377,
          0.00014451747228741587, 0.00014324768046304, 0.00014199454985143616,
          0.00014075779025172423, 0.00013953711775357552, 0.00013833225457429932,
          0.00013714292890083053, 0.000135968874736451, 0.00013480983175208144,
          0.0001336655451419913, 0.00013253576548377481, 0.00013142024860245198,
          0.00013031875543855384, 0.00012923105192006126, 0.00012815690883806756,
          0.00012709610172604265, 0.00012604841074257962, 0.00012501362055750918,
          0.00012399152024127286, 0.00012298190315744727, 0.000121984566858319,
          0.00012099931298340979, 0.00012002594716085935, 0.00011906427891157138,
          0.00011811412155603763, 0.00011717529212375237, 0.00011624761126513763,
          0.00011533090316589635, 0.00011442499546372306, 0.00011352971916729094,
          0.00011264490857745207, 0.00011177040121057477, 0.00011090603772395829,
          0.00011005166184325602, 0.00010920712029184921, 0.00010837226272210843,
          0.00010754694164848834, 0.00010673101238239711, 0.00010592433296879004,
          0.00010512676412443209, 0.00010433816917778218, 0.00010355841401044885,
          0.00010278736700017208, 0.00010202489896528395, 0.00010127088311060664,
          0.00010052519497474382, 9.978771237872564e-5, 9.905831537596654e-5,
          9.833688620349942e-5, 9.762330923444684e-5, 9.691747093169607e-5,
          9.621925980274069e-5, 9.552856635565749e-5, 9.484528305618468e-5,
          9.416930428587118e-5, 9.350052630126456e-5, 9.283884719411196e-5,
          9.218416685254066e-5, 9.153638692319512e-5, 9.089541077430033e-5,
          9.026114345962852e-5, 8.96334916833412e-5, 8.901236376568522e-5,
          8.839766960951641e-5, 8.778932066763066e-5, 8.71872299108779e-5,
          8.659131179703998e-5, 8.600148224044887e-5, 8.541765858232833e-5,
          8.483975956183605e-5, 8.426770528779043e-5, 8.370141721106122e-5,
          8.314081809760831e-5, 8.258583200214898e-5, 8.203638424243958e-5,
          8.149240137415285e-5, 8.095381116633734e-5, 8.042054257744142e-5,
          7.98925257318892e-5, 7.936969189719188e-5, 7.885197346158282e-5,
          7.833930391215985e-5, 7.783161781352502e-5, 7.732885078690547e-5,
          7.683093948974656e-5, 7.633782159576158e-5, 7.584943577542937e-5,
          7.536572167692667e-5, 7.488661990748473e-5, 7.441207201515924e-5,
          7.394202047100345e-5, 7.3476408651634e-5, 7.301518082217985e-5,
          7.25582821196041e-5, 7.210565853639097e-5, 7.165725690458634e-5,
          7.121302488018592e-5, 7.077291092785999e-5, 7.033686430600822e-5,
          6.990483505213528e-5, 6.947677396854021e-5, 6.905263260831095e-5,
          6.863236326161793e-5, 6.821591894229805e-5, 6.78032533747231e-5,
          6.739432098094488e-5, 6.69890768681116e-5, 6.658747681614716e-5,
          6.618947726568936e-5, 6.579503530627863e-5, 6.540410866479306e-5,
          6.501665569412267e-5, 6.463263536207828e-5, 6.425200724052835e-5,
          6.387473149475979e-5, 6.350076887305592e-5, 6.313008069648823e-5,
          6.276262884891505e-5, 6.239837576718453e-5, 6.203728443153482e-5,
          6.167931835618918e-5, 6.132444158013944e-5, 6.0972618658115566e-5,
          6.062381465173501e-5, 6.027799512082949e-5, 5.993512611494393e-5,
          5.959517416500453e-5, 5.925810627515134e-5, 5.892388991473247e-5,
          5.8592493010455517e-5, 5.826388393869327e-5, 5.793803151793989e-5,
          5.7614905001414264e-5, 5.729447406980755e-5, 5.697670882417134e-5,
          5.666157977894336e-5, 5.634905785510801e-5, 5.6039114373488473e-5,
          5.573172104816756e-5, 5.5426849980034484e-5, 5.5124473650455e-5,
          5.4824564915061767e-5, 5.4527096997662996e-5, 5.4232043484266133e-5,
          5.393937831721451e-5, 5.36490757894345e-5, 5.336111053879081e-5,
          5.3075457542547025e-5, 5.279209211193048e-5, 5.2510989886797616e-5,
          5.223212683039902e-5, 5.1955479224241134e-5, 5.168102366304335e-5,
          5.140873704978756e-5, 5.1138596590859346e-5, 5.087057979127771e-5,
          5.0604664450012594e-5, 5.034082865538729e-5, 5.007905078056521e-5,
          4.9819309479117665e-5, 4.9561583680672936e-5, 4.9305852586642965e-5,
          4.905209566602762e-5, 4.8800292651294224e-5, 4.855042353433053e-5,
          4.8302468562470595e-5, 4.8056408234591275e-5, 4.78122232972779e-5,
          4.756989474105831e-5, 4.7329403796703276e-5, 4.7090731931592434e-5,
          4.685386084614401e-5, 4.66187724703072e-5, 4.638544896011623e-5,
          4.615387269430442e-5, 4.592402627097728e-5, 4.569589250434352e-5,
          4.5469454421502686e-5, 4.524469525928835e-5, 4.5021598461166e-5,
          4.48001476741839e-5, 4.458032674597668e-5, 4.436211972182013e-5,
          4.414551084173634e-5, 4.393048453764809e-5, 4.371702543058175e-5,
          4.350511832791763e-5, 4.329474822068677e-5, 4.3085900280913395e-5,
          4.28785598590022e-5, 4.2672712481169414e-5, 4.2468343846917126e-5,
          4.226543982654949e-5, 4.206398645873065e-5, 4.186396994808343e-5,
          4.1665376662827354e-5, 4.146819313245634e-5, 4.127240604545447e-5,
          4.1078002247049506e-5, 4.088496873700335e-5, 4.069329266743872e-5,
          4.050296134070135e-5, 4.031396220725737e-5, 4.012628286362455e-5,
          3.99399110503375e-5, 3.97548346499456e-5, 3.957104168504358e-5,
          3.9388520316333784e-5, 3.9207258840719535e-5, 3.902724568942921e-5,
          3.8848469426170554e-5, 3.867091874531438e-5, 3.849458247010693e-5,
          3.831944955091137e-5, 3.814550906347674e-5, 3.7972750207234464e-5,
          3.780116230362176e-5, 3.7630734794431556e-5, 3.7461457240188474e-5,
          3.729331931855013e-5, 3.7126310822733576e-5, 3.696042165996636e-5,
          3.679564184996181e-5, 3.6631961523418004e-5, 3.646937092053987e-5,
          3.630786038958455e-5, 3.6147420385429095e-5, 3.598804146816008e-5,
          3.582971430168522e-5, 3.567242965236617e-5, 3.551617838767226e-5,
          3.536095147485507e-5, 3.520673997964266e-5, 3.505353506495445e-5,
          3.490132798963498e-5, 3.475011010720733e-5, 3.459987286464499e-5,
          3.445060780116261e-5, 3.4302306547024884e-5, 3.4154960822373234e-5,
          3.4008562436070106e-5, 3.386310328456072e-5, 3.371857535075167e-5,
          3.357497070290638e-5, 3.343228149355674e-5, 3.3290499958431115e-5,
          3.314961841539827e-5, 3.300962926342669e-5, 3.287052498155941e-5,
          3.273229812790386e-5, 3.25949413386366e-5, 3.245844732702256e-5,
          3.232280888244874e-5, 3.218801886947186e-5, 3.205407022688011e-5,
          3.1920955966768215e-5
        ],
        "constant_3": [
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155, 0.03676872733249155, 0.03676872733249155,
          0.03676872733249155
        ],
        "gaussian_4": [
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 1e-323, 1.78772040377626e-310, 1.8032804745638036e-297,
          9.560027216324996e-285, 2.6637112322435962e-272, 3.900742843443814e-260,
          3.0022002979695774e-248, 1.214406748796896e-236, 2.581789590092358e-225,
          2.88475997458685e-214, 1.694067407172288e-203, 5.22858117890097e-193,
          8.481432079270852e-183, 7.230805618269816e-173, 3.2399353925736414e-163,
          7.629888269479909e-154, 9.443482318596115e-145, 6.142969085323184e-136,
          2.1001806506598716e-127, 3.7736979952081206e-119, 3.563771039717098e-111,
          1.7688239601240874e-103, 4.614148798060406e-96, 6.326022667889939e-89,
          4.5582911044351154e-82, 1.7262573274432265e-75, 3.435905243038288e-69,
          3.5942558333395547e-63, 1.9761001873913888e-57, 5.710065596892935e-52,
          8.671723073903939e-47, 6.921526221986705e-42, 2.903557972517465e-37,
          6.401640765551718e-33, 7.417956165452716e-29, 4.517616809165431e-25,
          1.4459946417733081e-21, 2.4325184426209592e-18, 2.1506897466208535e-15,
          9.993820679784684e-13, 2.4407174464664605e-10, 3.132821304213062e-8,
          2.113420454650224e-6, 7.493217769268222e-5, 0.0013963135974129001,
          0.013675075889881988, 0.07038963091674806, 0.1904231723016589,
          0.27074663567923785, 0.20231985570707672, 0.07945955150684494,
          0.016401587200826954, 0.0017793353628243944, 0.00010145230248197641,
          3.0401721109090353e-6, 4.788137334638579e-8, 3.9633934857367174e-10,
          1.7242488658334508e-12, 3.942437995785727e-15, 4.737638938119847e-18,
          2.992204089785455e-21, 9.932364063416592e-25, 1.732791115813526e-28,
          1.588809984234179e-32, 7.656492703577398e-37, 1.939188159150705e-41,
          2.581322062425891e-46, 1.805912071231515e-51, 6.640230782055112e-57,
          1.2832223383564624e-62, 1.3033252640112674e-68, 6.957222317430592e-75,
          1.951871010969456e-81, 2.878051172814559e-88, 2.2303759534766652e-95,
          9.08426514701918e-103, 1.9446152813742607e-110, 2.1878107491501e-118,
          1.2936535192317675e-126, 4.0202990733029856e-135, 6.566454121793289e-144,
          5.63683901498046e-153, 2.543153149166632e-162, 6.030336704853497e-172,
          7.515238611957875e-182, 4.922391494019721e-192, 1.6945004715889732e-202,
          3.065768809317157e-213, 2.915206165895905e-224, 1.4569052599246102e-235,
          3.826709668292917e-247, 5.282650527748491e-259, 3.8327493032816837e-271,
          1.4615077098342504e-283, 2.9290310330625155e-296, 3.085169294723996e-309,
          1.73e-322, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
          0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ]
      }
    }
    ```

## Jupyter Notebook Interface

`SpectraFit` provides also an interface to [Jupyter Notebook][20] as an package
import. This interface is useful for interactive fitting and plotting of the
results. For interactive working the following tools are implemented:

1. [Plotly][21] for interactive plotting of the results
2. [Dtale][22] for interactive data exploration (_external_)
3. [itables][23] for interactive data exploration (_internal_)

For more information, please check the [Jupyter Notebook Interface][24] section.

[1]: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.describe.html
[2]: ../../api/spectrafit_api/#spectrafit.spectrafit.extracted_from_command_line_runner
[3]: https://lmfit.github.io/lmfit-py/model.html?highlight=report#lmfit.model.ModelResult.fit_report
[4]: https://en.wikipedia.org/wiki/Akaike_information_criterion
[5]: https://en.wikipedia.org/wiki/Bayesian_information_criterion
[6]: /spectrafit/interface/features/#fit-statistic
[7]: ../../doc/models/#spectrafit.models.pseudovoigt
[8]: /spectrafit/interface/features/#variable-analysis
[9]: https://lmfit.github.io/lmfit-py/fitting.html?highlight=correlation
[10]: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.corr.html
[11]: https://en.wikipedia.org/wiki/Confidence_interval
[12]: https://lmfit.github.io/lmfit-py/examples/example_confidence_interval.html?highlight=confidence
[13]: ../../api/plotting_api/
[14]: /spectrafit/interface/features/#correlation-analysis
[15]: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.from_dict.html
[16]: /spectrafit/interface/features/#pre-analysis
[17]: https://en.wikipedia.org/wiki/Correlation
[18]: https://docs.python.org/3/library/socket.html
[19]: https://docs.python.org/3/library/getpass.html
[20]: https://jupyter.org
[21]: https://plotly.com/python/
[22]: https://github.com/man-group/dtale
[23]: https://mwouts.github.io/itables/quick_start.html
[24]: ../../plugins/jupyter_interface
