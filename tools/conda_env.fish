#!/usr/bin/env fish

set ENV_NAME $argv[1]
set PACKAGE_NAME $argv[2]
set PYTHON_VERSION $argv[3]

if test -z "$PYTHON_VERSION"
    set PYTHON_VERSION 3.11
end

conda create -n $ENV_NAME python=$PYTHON_VERSION --no-default-packages -y
conda activate $ENV_NAME
conda config --add channels conda-forge
conda config --set channel_priority strict
conda install mamba -y

# Install spectrafit-all package
mamba install spectrafit-all -y
# Install an dditional package if provided
if test -n "$PACKAGE_NAME"
    mamba install $PACKAGE_NAME -y
end
