#!/bin/bash
# SpectraFit Development Container Setup Script
# This script runs after the container is created to set up the development environment

set -e

echo "🔧 Setting up SpectraFit development environment..."

# Upgrade pip
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

# Create virtual environment with uv (uv is installed via devcontainer feature)
echo "🐍 Creating virtual environment..."
uv venv --python 3.12

# Sync all dependencies including dev and docs groups
echo "📥 Installing dependencies..."
uv sync --all-extras --all-groups

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
uv run pre-commit install

echo "✅ Setup complete! You can now start developing SpectraFit."
echo "💡 Run 'uv run pytest spectrafit/' to run tests."
echo "💡 Run 'uv run pre-commit run --all-files' to run pre-commit checks."
