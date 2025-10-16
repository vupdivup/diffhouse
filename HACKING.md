# Developer Guide

## Setup

To get started with local development:

1. Clone the repository:

```bash
git clone https://github.com/vupdivup/diffhouse.git .
```

2. Run a [uv](https://docs.astral.sh/uv/) sync to install dependencies.

```bash
uv sync
```

3. Install [pre-commit](https://pre-commit.com/) hooks:

```bash
pre-commit install
```

4. Load the following variables into your environment:

| Variable| Purpose |
| --- | --- |
| `GITHUB_TOKEN` | GitHub API calls in tests |
| `TESTPYPI_TOKEN` | Smoke-testing releases |
| `PYPI_TOKEN` | Publishing releases |

A `.env` file with terminal auto-injection is recommended.

## Branching

The `main` branch always reflects the latest stable release.

For each upcoming version, start by creating a branch named `release/x.y.z` from `main`. Develop features on dedicated branches forked from and eventually merged back into this release branch. Direct commits to the release branch are allowed for admin-type changes.

If a feature branch is linked to an issue, prefix its name with the issue number, e.g. `72-fix-bugs`.

## Releases

To publish a new package version when development of a release is complete:

1. Bump the package version to a new release candidate:

```bash
uv version --bump <major|minor|patch> --bump rc
```

2. Delete the `/dist` directory if it exists locally.

3. Build the package and publish to TestPyPI for a smoke test:

```bash
uv build
```

```bash
uv publish --index testpypi --token $TESTPYPI_TOKEN
```

4. Install the TestPyPI release in an isolated environment (e.g. [Google Colab](https://colab.research.google.com/)) and test for basic functionality:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ diffhouse==x.y.zrc1
```

5. Bump the package version in `pyproject.toml` to the target release:

```bash
uv version --bump stable
```

6. Open a PR from the release branch onto `main` to run CI checks.

7. Build and publish to PyPI:

```bash
uv build
```

```bash
uv publish --token $PYPI_TOKEN
```

8. Merge the release branch onto `main`.

9. Create a GitHub release, listing every major change made since the last one.

If an error is encountered during any stage, debug and restart from step 1.
