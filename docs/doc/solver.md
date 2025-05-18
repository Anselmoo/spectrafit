---
title: Solver
description: SpectraFit Solver
tags:
  - solver
  - lmfit
  - scipy
  - optimization
---

## Solver

The solving process of `SpectraFit` is based on the following three steps:

1. _Defining the defining the model parameters_: The proposed peak is translated
   into a `lmfit`-type dictionary based on the **object-type** input
   _parameters_. The proposed peak can be manual or [automatically][2]
   generated. In the case of manual _parameters_, the fitting procedure can also
   be applied to a global or hybrid global-fitting routine. For more information
   check please in API-section [ModelParameters][2]
2. _Solving of the curve models_: Next, [SolverModels][3] will solve the
   `lmfit`-compatible model for a 2D- or 3D-fitting problem. All _parameters_,
   _boundaries_, and _conditions_ will pass to the proposed models. In the case
   of global fitting, the spectra have to be flattened.
3. _Calculating the model parameters_ Independent of a 2D- or 3D-fitting
   problem, the calculated/optimized spectra will always be created in a
   two-dimensional fashion; for more information, please check the API-Section
   about [calculated model][4].

[1]: ../../api/modelling_api/#spectrafit.models.ModelParameters
[2]: ../../interface/usage/#activating-automatic-peak-detection-for-fitting
[3]: ../../api/modelling_api/#spectrafit.models.SolverModels
[4]: ../../api/modelling_api/#spectrafit.models.calculated_model
