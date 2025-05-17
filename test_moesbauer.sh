#!/bin/bash
# Script to run Mössbauer-specific tests

echo "Running Mössbauer plugin tests..."
uv run pytest spectrafit/plugins/test/test_moesbauer.py -v

echo "Running Mössbauer API model tests..."
uv run pytest spectrafit/api/test/test_moesbauer_models.py -v

# Exit with the pytest exit code of the last command
exit $?
