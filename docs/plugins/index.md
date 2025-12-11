---
title: SpectraFit Plugins
description: Extend SpectraFit's functionality with plugins for file conversion, data processing, and visualization
tags:
  - plugins
  - extensions
  - converters
  - visualization
  - integration
---

# SpectraFit Plugins

This section documents the plugins available for **SpectraFit**, which extend its functionality beyond core spectral fitting.

## Overview

Plugins enhance **SpectraFit** by adding specialized workflows (for example, custom notebooks and advanced visualizations) that complement the core fitting engine.

!!! tip "Plugin Usage"

    Plugins can be accessed through dedicated functions in the API or through the command-line interface with specific flags.

## Available Plugins

<div class="grid cards" markdown>

- :material-notebook: **[Jupyter-Notebook-Integration](jupyter_interface.md)** - Enhanced features for interactive analysis in Jupyter.

</div>

!!! note "Legacy converters"

    Historical converter plugins (file, data, PKL, PPTX, and RIXS converters) have been removed from SpectraFit v2 to simplify maintenance. Use the core CLI or build bespoke tooling on top of the public APIs if you need similar workflows.

## Plugin Benefits

Using **SpectraFit** plugins provides several advantages:

- Seamless integration with external tools and file formats
- Specialized visualization for specific spectroscopic techniques
- Advanced data preprocessing and transformation
- Streamlined workflows for common analysis tasks
- Enhanced presentation and sharing of results

## Development

**SpectraFit** has a plugin architecture that allows for the development of custom extensions. To create a new plugin:

1. Use the plugin template in the **SpectraFit** repository
2. Implement the required interfaces
3. Register your plugin with the main package
4. Document the functionality following the standard format

For detailed instructions on plugin development, see the [Contributing](../contributing.md) guide.

## Next Steps

After exploring the plugins, you may want to:

- Check the [Examples](../examples/index.md) for practical applications
- Review the [API Reference](../api/index.md) for programmatic access
- Learn about [integration with other tools](../doc/index.md) in your workflow
