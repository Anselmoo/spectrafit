---
title: MCP Server Plugin
description: GitHub Copilot integration for SpectraFit through Model Context Protocol
tags:
  - mcp
  - copilot
  - ai-integration
  - spectral-analysis
  - natural-language
---

# MCP Server Plugin

The **MCP Server Plugin** enables seamless integration between SpectraFit and GitHub Copilot through the Model Context Protocol (MCP), allowing users to perform spectral analysis using natural language interactions.

## Overview

This plugin implements an MCP server that provides AI assistants with access to SpectraFit's powerful spectral analysis capabilities. Users can interact with their spectroscopic data through natural language queries via GitHub Copilot or other MCP-compatible AI tools.

!!! info "About Model Context Protocol"

    The Model Context Protocol (MCP) is an open standard that enables AI assistants to securely access external tools and data sources. It provides a standardized way for AI models to interact with applications while maintaining security and control.

## Installation

### Basic Installation

Install SpectraFit with MCP support:

```bash
pip install spectrafit[mcp]
```

### Development Installation

For development with all dependencies:

```bash
pip install spectrafit[all]
```

## Quick Start

### 1. Start the MCP Server

Launch the SpectraFit MCP server:

```bash
spectrafit-mcp-server
```

The server will start and listen for MCP connections from AI assistants.

### 2. Configure VS Code with GitHub Copilot

Add the following configuration to your VS Code `settings.json`:

```json
{
  "mcp.servers": {
    "spectrafit": {
      "command": "spectrafit-mcp-server",
      "description": "SpectraFit spectral analysis server"
    }
  }
}
```

### 3. Start Using with Copilot

Once configured, you can interact with your spectral data through natural language:

```text
"Analyze this Raman spectrum and fit it with Lorentzian peaks"
"Detect peaks in my UV-Vis data with prominence > 0.1"
"Generate an XPS fitting model for a carbon sample"
"Validate this IR spectrum data quality"
```

## Available Tools

The MCP server provides four main tools for spectral analysis:

### fit_spectrum

Performs complete spectral fitting with model validation and comprehensive results reporting.

**Parameters:**
- `data`: CSV data with 'Energy' and 'Intensity' columns
- `model`: Peak model configuration 
- `technique`: Spectroscopic technique (optional)
- `minimizer_settings`: Minimizer configuration (optional)
- `optimizer_settings`: Optimizer configuration (optional)

**Example:**
```text
"Fit this spectrum with two Gaussian peaks at 400 and 600 nm"
```

### auto_peak_detection

Automatic peak detection using scipy with prominence/height parameters and suggested model generation.

**Parameters:**
- `data`: CSV data with 'Energy' and 'Intensity' columns
- `prominence`: Peak prominence threshold (optional)
- `height`: Peak height threshold (optional)
- `distance`: Minimum distance between peaks (optional)
- `width`: Peak width constraints (optional)
- `technique`: Spectroscopic technique for model suggestions (optional)

**Example:**
```text
"Find all peaks in this Raman data with prominence > 10"
```

### generate_fit_model

Generates technique-specific model templates for various spectroscopic methods.

**Parameters:**
- `technique`: Spectroscopic technique (raman, uv-vis, xps, ir, moessbauer)
- `num_peaks`: Number of peaks to include (optional)
- `energy_range`: Energy range [min, max] (optional)
- `peak_positions`: Specific peak positions (optional)

**Example:**
```text
"Create an XPS model template with 3 peaks between 280-290 eV"
```

### validate_spectral_data

Validates data format, performs quality analysis, and provides recommendations.

**Parameters:**
- `data`: CSV data to validate
- `technique`: Expected spectroscopic technique (optional)

**Example:**
```text
"Check if this data is suitable for Raman analysis"
```

## Available Resources

The server provides access to SpectraFit resources through MCP:

### spectrafit://models/fitting-functions

JSON list of available peak and background functions in SpectraFit:
- Peak functions: Gaussian, Lorentzian, Voigt, Pseudo-Voigt, Pearson distributions
- Background functions: Linear, exponential, polynomial
- Step functions: Atan, erf, log, Heaviside
- Convolution functions: Gaussian, Lorentzian, Voigt
- Mössbauer functions: Singlet, doublet, sextet, octet

### spectrafit://examples/sample-data

CSV sample spectral data for testing and demonstration purposes.

### spectrafit://config/default-parameters

JSON configuration templates for different spectroscopic techniques with recommended parameters.

## Supported Spectroscopic Techniques

The MCP server provides optimized support for various spectroscopic techniques:

### Raman Spectroscopy
- **Energy Range**: 200-4000 cm⁻¹
- **Recommended Function**: Lorentzian
- **Typical FWHM**: 5-50 cm⁻¹
- **Use Cases**: Vibrational analysis, molecular identification

### UV-Vis Spectroscopy  
- **Energy Range**: 200-800 nm
- **Recommended Function**: Gaussian
- **Typical FWHM**: 10-100 nm
- **Use Cases**: Electronic transitions, concentration analysis

### X-ray Photoelectron Spectroscopy (XPS)
- **Energy Range**: 0-1500 eV
- **Recommended Function**: Voigt
- **Typical FWHM**: 0.5-5 eV
- **Use Cases**: Surface composition, chemical states

### Infrared (IR) Spectroscopy
- **Energy Range**: 400-4000 cm⁻¹
- **Recommended Function**: Lorentzian
- **Typical FWHM**: 2-30 cm⁻¹
- **Use Cases**: Functional group identification, molecular structure

### Mössbauer Spectroscopy
- **Energy Range**: -10 to 10 mm/s
- **Recommended Function**: Lorentzian
- **Typical FWHM**: 0.1-2 mm/s
- **Use Cases**: Iron oxidation states, magnetic properties

## Data Format Requirements

All spectral data must be provided in CSV format with specific column requirements:

### Required Columns
- `Energy`: X-axis values (wavenumber, wavelength, binding energy, etc.)
- `Intensity`: Y-axis values (counts, absorbance, etc.)

### Data Quality Requirements
- Energy values should be monotonic (increasing or decreasing)
- No missing values (NaN) in required columns
- Numeric data types for both columns
- Minimum 10 data points recommended

### Example CSV Format
```csv
Energy,Intensity
200.0,10.5
201.0,12.3
202.0,15.8
...
```

## Configuration Examples

### Basic Raman Analysis
```json
{
  "description": {
    "project_name": "Raman Analysis",
    "keywords": ["raman", "vibrational"]
  },
  "minimizer": {
    "nan_policy": "propagate",
    "calc_covar": true
  },
  "optimizer": {
    "max_nfev": 1000,
    "method": "leastsq"
  },
  "peaks": {
    "1": {
      "lorentzian": {
        "amplitude": {"max": 100, "min": 0, "vary": true, "value": 50},
        "center": {"max": 1020, "min": 980, "vary": true, "value": 1000},
        "fwhm": {"max": 50, "min": 5, "vary": true, "value": 25}
      }
    }
  }
}
```

### Advanced XPS Fitting
```json
{
  "peaks": {
    "1": {
      "voigt": {
        "amplitude": {"max": 1000, "min": 0, "vary": true, "value": 500},
        "center": {"max": 290, "min": 280, "vary": true, "value": 285},
        "fwhmg": {"max": 3, "min": 0.5, "vary": true, "value": 1.5},
        "fwhml": {"max": 3, "min": 0.5, "vary": true, "value": 1.0}
      }
    }
  }
}
```

## Natural Language Examples

Here are example natural language queries you can use with GitHub Copilot:

### Data Analysis
```text
"Load this CSV file and analyze it as a Raman spectrum"
"What peaks can you detect in this UV-Vis data?"
"Fit my XPS spectrum with Voigt functions"
"Check the quality of this infrared spectrum"
```

### Model Generation
```text
"Create a fitting model for benzene Raman spectrum"
"Generate an XPS template for carbon analysis"
"Set up a Mössbauer model with two doublets"
"Make a UV-Vis model for organic dyes"
```

### Peak Analysis
```text
"Find all peaks above 50% intensity"
"Detect Raman bands with prominence > 20"
"Identify XPS peaks in the C 1s region"
"Locate IR absorption bands"
```

### Data Validation
```text
"Is this data suitable for spectral fitting?"
"Check if my Raman data covers the expected range"
"Validate this XPS spectrum quality"
"Does this IR data have proper resolution?"
```

## Troubleshooting

### Common Issues

#### MCP Dependencies Not Found
```bash
Error: MCP dependencies are not available.
```
**Solution**: Install with MCP support: `pip install spectrafit[mcp]`

#### Server Connection Issues
If the MCP server fails to connect:
1. Ensure the server is running: `spectrafit-mcp-server`
2. Check VS Code MCP configuration
3. Restart VS Code after configuration changes

#### Data Format Errors
```text
Error: Data must contain 'Energy' and 'Intensity' columns.
```
**Solution**: Ensure your CSV has the correct column names and format

#### Fitting Convergence Issues
If fits don't converge:
1. Check initial parameter values
2. Adjust parameter bounds
3. Try different optimization methods
4. Ensure data quality is sufficient

### Debug Mode

Enable debug logging by setting the environment variable:
```bash
export SPECTRAFIT_DEBUG=1
spectrafit-mcp-server
```

### Performance Tips

1. **Data Size**: For large datasets (>10,000 points), consider downsampling
2. **Peak Number**: Start with fewer peaks and add more as needed
3. **Parameter Bounds**: Use realistic bounds to improve convergence
4. **Background**: Include background functions for better fits

## API Reference

### SpectraFitMCPServer Class

The main server class that handles MCP communication and tool registration.

#### Methods

##### `__init__()`
Initialize the MCP server with tool and resource registration.

##### `async run()`
Start the MCP server and handle client connections.

### Tool Functions

All tools are async functions that accept arguments and return MCP text content.

#### Tool Schemas

Each tool defines a JSON schema for parameter validation:

```python
{
    "type": "object",
    "properties": {
        "data": {"type": "string", "description": "CSV spectral data"},
        "technique": {"type": "string", "enum": ["raman", "uv-vis", "xps", "ir", "moessbauer"]}
    },
    "required": ["data"]
}
```

## Integration with SpectraFit Ecosystem

The MCP server integrates seamlessly with the broader SpectraFit ecosystem:

- **Core Engine**: Uses `SpectraFitNotebook` for all fitting operations
- **Model Library**: Access to all built-in peak and background functions
- **Auto Peak Detection**: Leverages existing `AutoPeakDetection` class
- **Validation**: Uses established data quality metrics
- **Export**: Compatible with all SpectraFit output formats

## Contributing

To contribute to the MCP server plugin:

1. Fork the SpectraFit repository
2. Create a feature branch
3. Add tests for new functionality
4. Follow the existing code style
5. Submit a pull request

### Development Setup

```bash
git clone https://github.com/Anselmoo/spectrafit.git
cd spectrafit
pip install -e .[all]
pytest spectrafit/plugins/test/test_mcp_server.py
```

## License

The MCP Server Plugin is distributed under the same BSD-3-Clause license as SpectraFit.

## Support

For issues and questions:
- **GitHub Issues**: [Report bugs and request features](https://github.com/Anselmoo/spectrafit/issues)
- **Documentation**: [Complete SpectraFit documentation](https://anselmoo.github.io/spectrafit/)
- **Examples**: [Browse example notebooks](https://github.com/Anselmoo/spectrafit/tree/main/Examples)

## Version History

### v1.0.0 (Current)
- Initial MCP server implementation
- Support for four main analysis tools
- Integration with GitHub Copilot
- Comprehensive spectroscopic technique support
- Full validation and error handling