<!-- trunk-ignore-all(prettier) -->
<!-- trunk-ignore(markdownlint/MD041) -->
*[API]: Application Programming Interface
*[ASCII]: American Standard Code for Information Interchange; a common plain text format
*[Amplitude]: The height or maximum value of a peak function
*[Athena]: Interactive graphical utility for XAS analysis based on IFEFFIT or LARCH
*[Automatic Peak Detection]: Automatically finding peaks in the data using algorithms like find*peaks
*[Background Subtraction]: Removing the underlying signal or baseline from the raw data
*[Baseline]: The underlying signal or background upon which spectral features are superimposed
*[Baseline Correction]: The process of estimating and removing the baseline signal
*[Bayesian Inference]: Statistical method used for updating probabilities based on evidence, applicable in parameter estimation
*[Bounds]: The lower and upper limits constraining a Parameter during optimization
*[Calibration]: Process of correlating the readings of an instrument with a standard to ensure accuracy, e.g., energy calibration
*[Center]: The position of the maximum of a peak function along the independent variable axis (e.g., energy, wavenumber)
*[CI/CD]: Continuous Integration/Continuous Deployment
*[CLI]: Command Line Interface
*[CSV]: Comma-Separated Values file format
*[Chi-squared (χ²)]: A statistical measure of the Goodness-of-fit between observed data and a Model
*[Confidence Intervals]: A range of values providing an estimate of the uncertainty of a fitted Parameter
*[Configuration File]: A file containing settings and parameters for software, often in formats like JSON, YAML, or TOML
*[Convergence]: The state reached when an iterative optimization algorithm finds a stable solution where further iterations do not significantly improve the fit
*[Conventional Commits]: A specification for adding human and machine readable meaning to commit messages
*[Convolution]: A mathematical operation combining two functions to produce a third function, expressing how the shape of one is modified by the other; relevant for Voigt profiles
*[Correlation]: A statistical measure indicating the extent to which two fitted Parameters move in relation to each other
*[Covariance Matrix]: A matrix whose elements represent the covariances between pairs of fitted Parameters, used to estimate uncertainties
*[Curve Fitting]: The process of constructing a curve, or mathematical function, that has the best fit to a series of data points
*[Data Acquisition]: The process of collecting data from an experiment or instrument
*[Data Model API]: Application programming interface that allows interaction with the data model defined using Pydantic
*[Deconvolution]: Process of resolving overlapping peaks or removing instrumental broadening effects
*[Degrees of Freedom (DoF)]: The number of independent pieces of information available to estimate another quantity; typically number of data points minus number of varied parameters
*[Derivative]: The rate of change of a function; used in spectroscopy for peak finding or enhancing features
*[Detector]: Device used to measure the intensity of radiation in spectroscopic experiments
*[Dictionaries]: Collection of key-value pairs in Python
*[Diffraction]: The bending of waves as they pass around an obstacle or through an aperture, relevant in X-ray techniques
*[Docker]: Platform for developing, shipping, and running applications in containers
*[Emission]: Process by which a substance releases energy in the form of electromagnetic radiation
*[Energy]: Physical quantity often used as the independent variable (x-axis) in spectroscopic measurements (e.g., eV, keV)
*[Environment (Virtual)]: Isolated Python environment managing dependencies for a specific project (e.g., using venv, Conda, Poetry)
*[Excel]: Spreadsheet software developed by Microsoft
*[Expressions]: Mathematical constraints or dependencies between different fitting Parameters, evaluated by lmfit
*[Fluorescence]: Emission of light by a substance that has absorbed light or other electromagnetic radiation
*[Fourier Transform]: Mathematical transform used to decompose a function into its constituent frequencies, used in FT-IR spectroscopy
*[Frequency]: Number of occurrences of a repeating event per unit of time, related to energy and wavelength
*[FWHM]: Full Width at Half Maximum; a measure of the width of a peak function (e.g., fwhmg, fwhml)
*[Gaussian]: A common bell-shaped peak function used in curve fitting
*[Git]: Distributed version control system
*[GitHub]: Platform for hosting Git repositories and collaboration
*[GUI]: Graphical User Interface
*[Global Fitting]: Simultaneously fitting multiple datasets with shared Parameters
*[Goodness-of-fit]: Statistical measures (e.g., Chi-squared, R-squared) indicating how well a Model fits the observed data
*[IDE]: Integrated Development Environment
*[Initial Values]: The starting values assigned to Parameters before the optimization process begins
*[Intensity]: The dependent variable (y-axis) in spectroscopy, representing the strength of the signal
*[Integration]: Calculating the area under a curve, often used to quantify peak intensity
*[IR]: Infrared Spectroscopy
*[Iteration]: A single step or cycle within an optimization algorithm
*[JSON]: JavaScript Object Notation
*[Jupyter Notebook]: Web-based interactive computing environment for creating and sharing documents that contain live code, equations, visualizations, and narrative text
*[JupyterLab]: Next-generation web-based user interface for Project Jupyter
*[L-edge]: Features in X-ray Absorption Spectroscopy (XAS) arising from electron transitions from the L atomic shell (n=2)
*[Least-Squares]: An optimization method that minimizes the sum of the squares of the Residuals between observed data and a Model
*[Levenberg-Marquardt]: An iterative algorithm used for solving non-linear Least-Squares problems, the default Optimizer in lmfit
*[Lorentzian]: A common peak function, also known as the Cauchy distribution, used in curve fitting
*[Matplotlib]: Plotting library for the Python programming language
*[Maximum Likelihood Estimation (MLE)]: Method for estimating the parameters of a statistical model given observations
*[Metadata]: Data that provides information about other data (e.g., experimental conditions, sample details)
*[Minimizer]: The lmfit class used for defining and performing the optimization (fitting) problem
*[MkDocs Material]: A theme for the MkDocs static site generator, used for SpectraFit's documentation
*[Model]: A mathematical function used to describe the data, often composed of one or more peak functions and a baseline, implemented using lmfit Models
*[Model Component]: A distinct part of a composite Model, such as an individual peak or a baseline function
*[Monte Carlo Methods]: Computational algorithms relying on repeated random sampling to obtain numerical results, sometimes used in error estimation
*[Nelder-Mead]: A simplex-based optimization algorithm available in lmfit
*[NetworkX]: Python library for the creation, manipulation, and study of complex networks
*[NMR]: Nuclear Magnetic Resonance Spectroscopy, a technique used to observe local magnetic fields around atomic nuclei
*[Noise]: Random fluctuations in data that obscure the underlying signal
*[Non-linear Fitting]: Curve fitting where the model depends non-linearly on its parameters
*[Normalization]: Scaling data to a common range or standard, often between 0 and 1 or based on a specific feature
*[NumPy]: Fundamental package for scientific computing with Python
*[Objective Function]: The function that an optimization algorithm seeks to minimize or maximize (e.g., sum of squared residuals in Least-Squares)
*[ORCA]: A computational chemistry software package for quantum chemistry calculations
*[Optimizer]: The algorithm (e.g., Levenberg-Marquardt, Nelder-Mead) used by the Minimizer to find the best-fit Parameters
*[Overfitting]: Fitting a model too closely to the noise or random fluctuations in the data, rather than the underlying trend
*[Pandas DataFrames]: Two-dimensional, size-mutable, and potentially heterogeneous tabular data structures in the Pandas Python library
*[Parameter Space]: The multi-dimensional space defined by the possible values of the model parameters
*[Parameters]: The adjustable variables within a Model (e.g., amplitude, center, width) that are optimized during fitting
*[Peak Shape]: The functional form used to describe a peak (e.g., Gaussian, Lorentzian, Voigt)
*[Peak Width]: A measure of the extent of a peak along the independent variable axis, often characterized by FWHM or sigma
*[Photon]: A quantum of electromagnetic radiation
*[Pip]: The standard package installer for Python
*[Pickle File]: Python's built-in serialization format
*[Plotly]: A graphing library for creating interactive charts and dashboards
*[Poetry]: Tool for Python dependency management and packaging
*[PPTX]: PowerPoint file format
*[Preprocessing]: Steps taken to prepare raw data for analysis (e.g., normalization, baseline correction, smoothing)
*[Pseudo-Voigt]: A peak function approximating the Voigt profile, calculated as a linear combination or sum of Gaussian and Lorentzian shapes
*[Pydantic]: Data validation and settings management library for Python
*[Python]: High-level, interpreted, general-purpose programming language
*[pytest]: A testing framework for Python code
*[Quantification]: Determining the amount or concentration of a substance based on spectral features
*[R-squared (R²)]: Coefficient of determination; a statistical measure of how well the regression predictions approximate the real data points (1 indicates perfect fit)
*[Raman Spectroscopy]: Spectroscopic technique used to observe vibrational, rotational, and other low-frequency modes in a system
*[Reduced Chi-squared (χ²・ν)]: Chi-squared divided by the Degrees of Freedom, providing a measure of Goodness-of-fit normalized by the number of free parameters
*[Regression]: Statistical process for estimating the relationships between variables
*[Repository]: A central location where code and its history are stored, typically using a VCS like Git
*[Resolution (Spectral)]: The ability of a spectrometer to distinguish between closely spaced spectral features
*[Residuals]: The differences between the observed data values and the values predicted by the fitted Model
*[RIXS]: Resonant Inelastic X-ray Scattering
*[Robust Fitting]: Fitting methods less sensitive to outliers in the data compared to standard Least-Squares
*[Savitzky-Golay Filter]: A digital filter used for smoothing data and computing derivatives
*[Scattering]: Process where waves or particles are deflected from a straight path due to interaction with other matter
*[SciPy]: Open-source Python library used for scientific and technical computing
*[SDK]: Software Development Kit
*[Sensitivity Analysis]: Study of how the uncertainty in the output of a model can be attributed to different sources of uncertainty in its inputs or parameters
*[Signal Processing]: Manipulation and analysis of signals, such as spectroscopic data
*[Sigma (σ)]: The standard deviation parameter, often related to the width (FWHM) of peak functions like the Gaussian
*[Simulation]: Imitation of the operation of a real-world process or system, e.g., simulating spectra based on a model
*[Smoothing]: Applying algorithms to reduce noise in data, often using moving averages or Savitzky-Golay filters
*[SpectraFit]: Software for analyzing and fitting spectroscopic data
*[Spectroscopy]: Study of the interaction between matter and electromagnetic radiation as a function of wavelength or frequency
*[Spectrum]: Data representing intensity as a function of energy, wavelength, frequency, or wavenumber
*[Standard Deviation]: A measure of the amount of variation or dispersion of a set of values
*[Standard Error]: An estimate of the standard deviation of a fitted Parameter, indicating its uncertainty
*[TOML]: Tom's Obvious, Minimal Language
*[Tolerance]: A threshold used in optimization algorithms to determine when convergence has been reached
*[Trunk-Based Development]: A source-control branching model where developers collaborate on code in a single branch called 'trunk' (or main)
*[Uncertainty]: The range of possible values within which the true value of a measurement or parameter lies
*[Units]: Standard quantities used for measurement (e.g., eV, nm, cm⁻¹)
*[UV-Vis]: Ultraviolet-Visible Spectroscopy
*[Validation]: Process of checking if the model and its results are acceptable for the intended purpose
*[Vary]: A boolean flag for a Parameter indicating whether its value should be adjusted (True) or kept fixed (False) during optimization
*[VCS]: Version Control System
*[Version Control]: System for tracking changes to files over time, like Git
*[Visualization]: Creating graphical representations of data or models
*[Voigt]: A peak function resulting from the Convolution of a Gaussian and a Lorentzian profile
*[VS Code]: Visual Studio Code, a source-code editor
*[Wavelength]: Spatial period of a periodic wave, inversely related to frequency and energy
*[Wavenumber]: Spatial frequency, often used as the independent variable (x-axis) in IR and Raman spectroscopy (e.g., cm⁻¹)
*[Weighting]: Assigning different levels of importance to data points during fitting, often based on their uncertainty
*[Width]: General term for the extent of a peak, often quantified by FWHM or sigma
*[XAS]: X-ray Absorption Spectroscopy
*[XPS]: X-ray Photoelectron Spectroscopy
*[X-ray]: Form of electromagnetic radiation with high energy
*[YAML]: YAML Ain't Markup Language
*[Zero Filling]: Adding zeros to the end of a time-domain signal before Fourier Transform to increase spectral resolution (interpolation)
