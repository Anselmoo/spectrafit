python -m pip install --upgrade pip
python -m pip install poetry
poetry config virtualenvs.in-project true
python -m poetry install --with dev,docs --all-extras
