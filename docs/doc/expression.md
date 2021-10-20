`lmfit` also provides an expression parser for use in fitting models.
Consequently, the expression parser can be also used in SpectraFit for
generating fits with constraint conditions or global fits.

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
    },
    "2": {
        "pseudovoigt": {
            "amplitude": {
                "expr": "pseudovoigt_amplitude_1"
            },
            "center": {
                "expr": "pseudovoigt_center_1 + 1.68"
            }
        }
    }
}

```

In this particular use case, the _amplitude_ of the second peak is set to the
_amplitude_ of the first peak; the _center_ of the second peak is set to the
_center_ of the first peak plus 1.68.

![_](../../examples/images/Figure_5.png)

> In this example, the expression parser is used to set the _amplitude_ of the
> peak 1 and 2 to equaly, as well as the _center_ of peak 2 to the center of
> peak 1 plus 1.68.

!!! note "The right notation of peaks"

    In contrast to the `json`, `yaml`, or `toml` file, the peaks are written in
    the following way, that number of the peak is the last number.

    | `toml`                    | Definition                |
    | ------------------------- | ------------------------- |
    | number.function.attribute | function_attribute_number |
