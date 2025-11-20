# SpectraFit Development Container

This folder contains the configuration for the SpectraFit development container, which provides a consistent and fully-configured development environment using VS Code Dev Containers or GitHub Codespaces.

## 📋 Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop) or compatible container runtime
- [Visual Studio Code](https://code.visualstudio.com/) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- Or use [GitHub Codespaces](https://github.com/features/codespaces) directly in your browser

## 🚀 Quick Start

### Option 1: Using VS Code

1. Open the SpectraFit repository in VS Code
2. When prompted, click "Reopen in Container" (or use Command Palette: `Dev Containers: Reopen in Container`)
3. Wait for the container to build and start (first time may take a few minutes)
4. Once ready, the development environment is fully configured!

### Option 2: Using GitHub Codespaces

1. Go to the [SpectraFit repository](https://github.com/Anselmoo/spectrafit)
2. Click the green "Code" button
3. Select "Codespaces" tab
4. Click "Create codespace on main"
5. Wait for the environment to initialize

## 🛠️ What's Included

### Base Image
- **Python 3.12** (Debian Bookworm based)
- Latest stable Python tools and libraries

### Development Tools
- **uv**: Fast Python package installer and resolver
- **Git**: Version control
- **GitHub CLI**: GitHub integration from terminal
- **Docker-in-Docker**: For container operations

### VS Code Extensions
- **Python**: Core Python language support
- **Pylance**: Fast Python language server
- **Ruff**: Fast Python linter and formatter
- **mypy**: Static type checker
- **autodocstring**: Automatic docstring generation
- **Even Better TOML**: Enhanced TOML support
- **YAML**: YAML language support
- **Markdown All in One**: Markdown productivity tools
- **GitHub Pull Requests**: GitHub integration

### Pre-configured Settings
- Python interpreter: `.venv/bin/python`
- Default formatter: Ruff
- Format on save: Enabled
- Organize imports on save: Enabled
- Pytest integration: Enabled
- Line length rulers at 88 and 100 characters

## 📦 Dependencies

All project dependencies are automatically installed during container creation:
- **Core dependencies**: Listed in `pyproject.toml`
- **Development tools**: pytest, ruff, mypy, pre-commit, etc.
- **Documentation tools**: mkdocs-material and plugins
- **Optional extras**: Jupyter, Dash, graph tools

## 🏗️ Post-Creation Setup

The `setup.sh` script runs automatically after container creation and:
1. ✅ Upgrades pip
2. ✅ Creates a Python 3.12 virtual environment
3. ✅ Installs all dependencies (including dev and docs groups)
4. ✅ Sets up pre-commit hooks

## 💻 Common Commands

Once inside the container, you can use these commands:

```bash
# Run tests
uv run pytest spectrafit/

# Run specific test file
uv run pytest spectrafit/test/test_file.py -v

# Run pre-commit checks
uv run pre-commit run --all-files

# Run SpectraFit CLI
uv run spectrafit --help

# Build documentation
uv run mkdocs serve

# Add a new dependency
uv add package-name

# Add a development dependency
uv add package-name --group dev
```

## 🔧 Customization

### Modify devcontainer.json
To customize the container configuration, edit `.devcontainer/devcontainer.json`:
- Change Python version in the `image` field
- Add/remove VS Code extensions
- Modify VS Code settings
- Add additional dev container features

### Modify setup.sh
To change post-creation setup steps, edit `.devcontainer/setup.sh`:
- Add custom initialization commands
- Install additional system packages
- Configure environment variables

## 🐛 Troubleshooting

### Container fails to build
- Ensure Docker is running
- Check Docker daemon logs
- Try rebuilding without cache: Command Palette → `Dev Containers: Rebuild Container`

### Python interpreter not found
- Verify virtual environment was created: `ls .venv/`
- Manually create if needed: `uv venv --python 3.12`
- Reload VS Code window

### Extensions not working
- Reload window: Command Palette → `Developer: Reload Window`
- Check extension logs in Output panel
- Verify extension is installed in container (not locally)

### Dependencies not installed
- Check `setup.sh` output in terminal
- Manually run: `uv sync --all-extras --all-groups`
- Check `uv.lock` file is present

## 📚 Additional Resources

- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Dev Container Features](https://containers.dev/features)
- [SpectraFit Documentation](https://anselmoo.github.io/spectrafit/)
- [uv Documentation](https://docs.astral.sh/uv/)

## 🤝 Contributing

If you improve the devcontainer setup, please:
1. Test your changes thoroughly
2. Update this README if needed
3. Submit a pull request with clear description

## 📝 Version History

- **v2.0** (2025): Major update to Python 3.12, uv-based setup, enhanced VS Code integration
- **v1.0** (2023): Initial devcontainer configuration
