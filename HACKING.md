## Setup

1. Clone the repository:

```bash
git clone https://github.com/vupdivup/diffhouse.git .
```

2. Run a [uv](https://docs.astral.sh/uv/) sync to install dependencies. Install additional groups as needed:

```bash
uv sync --group test
```

3. Install [pre-commit](https://pre-commit.com/) hooks:

```bash
pre-commit install
```

3. Load the following variables into your environment:

| Variable| Purpose |
| --- | --- |
| `GITHUB_TOKEN` | GitHub API calls in tests |
| `TESTPYPI_TOKEN` | Smoke-testing releases |
| `PYPI_TOKEN` | Publishing releases |

A `.env` file with terminal auto-injection is recommended.

4. You're good to go!

## Releases

1. Bump the package version in `pyproject.toml`.

2. Build the package:

```bash
uv build
```

3. Publish to TestPyPI first for a smoke test:

```bash
uv publish --index testpypi --token $TESTPYPI_TOKEN
```

4. Install the pending version in an isolated environment (e.g. [Google Colab](https://colab.research.google.com/)):

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ diffhouse
```

5. Manually test the basic functionalities.

5. If everything looks good, publish to PyPI:

```bash
uv publish --token $PYPI_TOKEN
```
