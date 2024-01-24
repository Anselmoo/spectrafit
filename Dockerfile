# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
# Reference File: https://github.com/jupyter/docker-stacks/blob/main/scipy-notebook/Dockerfile
# This Dockerfile is modified from the original version to include the SpectraFit package.
ARG OWNER=jupyter
ARG BASE_CONTAINER=$OWNER/minimal-notebook
FROM $BASE_CONTAINER

LABEL maintainer="Anselm Hahn <anselm.hahn@gmail.com>"
LABEL project="SpectraFit"
LABEL description="📊📈🔬 SpectraFit is a command-line and Jupyter-notebook tool for quick data-fitting based on the regular expression of distribution functions."
LABEL license = "BSD-3-Clause"
LABEL url = "https://github.com/Anselmoo/spectrafit"
LABEL vendor = "https://github.com/jupyter/docker-stacks/tree/main/images/scipy-notebook"

# Fix: https://github.com/hadolint/hadolint/wiki/DL4006
# Fix: https://github.com/koalaman/shellcheck/wiki/SC3014
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

USER root

RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends \
    # for cython: https://cython.readthedocs.io/en/latest/src/quickstart/install.html
    build-essential \
    # for latex labels
    cm-super \
    dvipng \
    # for matplotlib anim
    ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

USER ${NB_UID}

# Install Python 3 packages
RUN mamba install --yes \
    'altair' \
    'beautifulsoup4' \
    'bokeh' \
    'bottleneck' \
    'cloudpickle' \
    'conda-forge::blas=*=openblas' \
    'cython' \
    'dask' \
    'dill' \
    'h5py' \
    'ipympl'\
    'ipywidgets' \
    'matplotlib-base' \
    'numba' \
    'numexpr' \
    'openpyxl' \
    'pandas' \
    'patsy' \
    'protobuf' \
    'pytables' \
    'scikit-image' \
    'scikit-learn' \
    'scipy' \
    'seaborn' \
    'spectrafit-all' \
    'sqlalchemy' \
    'statsmodels' \
    'sympy' \
    'widgetsnbextension'\
    'xlrd' && \
    mamba clean --all -f -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

# Install facets which does not have a pip or conda package at the moment
WORKDIR /tmp
RUN git clone https://github.com/PAIR-code/facets.git && \
    jupyter nbclassic-extension install facets/facets-dist/ --sys-prefix && \
    rm -rf /tmp/facets && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

# Import matplotlib the first time to build the font cache.
ENV XDG_CACHE_HOME="/home/${NB_USER}/.cache/"

#RUN MPLBACKEND=Agg python -c "import matplotlib.pyplot; from spectrafit.plugins import notebook, color_schemas" && \
#    fix-permissions "/home/${NB_USER}"
RUN MPLBACKEND=Agg python -c "import matplotlib.pyplot as plt; "\
    "import pandas as pd; from spectrafit.plugins import notebook as nb" && \
    fix-permissions "/home/${NB_USER}"

USER ${NB_UID}

WORKDIR "${HOME}"
