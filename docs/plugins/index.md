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

This section documents the external plugin surface for **SpectraFit**.

## Overview

Plugins enhance **SpectraFit** by adding specialized workflows that complement
the core fitting engine without expanding the core package itself.

!!! tip "Plugin usage"
    External plugins are exposed through the `spectrafit plugins ...` command
    group after they are installed via Python entry points.

## Current policy

SpectraFit v2 does **not** currently ship built-in `spectrafit.plugins`
entry-point plugins.

In particular:

- Jupyter is a first-class top-level interface (`spectrafit jupyter` and
  `spectrafit-jupyter`)
- Mössbauer plugin entry points are not bundled with the core package
- the `plugins` command group is reserved for discovered **external plugins**

!!! note "Legacy converters"

    Historical converter plugins (file, data, PKL, PPTX, and RIXS converters) have been removed from SpectraFit v2 to simplify maintenance. Use the core CLI or build bespoke tooling on top of the public APIs if you need similar workflows.

## Plugin Benefits

Using external **SpectraFit** plugins provides several advantages:

- Seamless integration with external tools and file formats
- Specialized commands for domain-specific workflows
- Optional dependencies isolated to plugin packages
- Streamlined workflows for local extension authors
- Clear separation between core runtime and optional tooling

## Development

**SpectraFit** has a plugin architecture that allows for the development of
custom extensions. To create a new plugin:

1. Start from `examples/plugin_template/` in the **SpectraFit** repository
2. Implement the required interfaces
3. Register your plugin via the `spectrafit.plugins` entry-point group
4. Document the functionality following the standard format

For detailed instructions on plugin development, see the
[Plugin Development Guide](plugin-development-guide.md).

## Next Steps

After exploring the plugin system, you may want to:

- Check the [Examples](../examples/index.md) for practical applications
- Review the [API Reference](../api/index.md) for programmatic access
- Learn about [integration with other tools](../doc/index.md) in your workflow
