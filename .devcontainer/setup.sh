python -m pip install --upgrade pip
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python 3.10
uv sync --all-extras --all-groups
