# Hermes Argumap

Local, deterministic argument-graph tooling for Hermes. The package will provide
versioned argument cases, reproducible snapshots, and portable verdict exports.

## Local development

Use Python 3.11 or later. Create an isolated environment and install the package
with its test dependency:

```console
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
```

The initial package intentionally contains only the project foundation. Domain
models, graph behavior, storage, and Hermes integration are added in later tasks.
