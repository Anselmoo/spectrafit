#!/usr/bin/env zsh

ENV_NAME=$1
PACKAGE_NAME=$2
PYTHON_VERSION=${3:-3.11}

conda create -n $ENV_NAME python=$PYTHON_VERSION --no-default-packages
conda activate $ENV_NAME
conda config --add channels conda-forge
conda config --set channel_priority strict
conda install mamba -y

# Install spectrafit-all package
mamba install spectrafit-all -y
# Install an dditional package if provided
if [[ -n $PACKAGE_NAME ]]; then
    mamba install $PACKAGE_NAME -y
fi
