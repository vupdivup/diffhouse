# diffhouse

*diffhouse* is a **git metadata extraction tool** for Python that retrieves high-quality repository information such as commit history, branches, tags and more.

## Requirements

Git 2.19 or greater.

## Quick start

1. Install *diffhouse* with pip:

```bash
pip install diffhouse
```

2. Import the `Repo` class in Python:

```python
from diffhouse import Repo
```

3. Create a `Repo` instance with the git repository URL as an argument. Expect a few seconds of wait time as the repository metadata is extracted.

```python
r = Repo(url='https://github.com/user/name.git')
```

4. Access data through the following *pandas* [`DataFrames`](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html):

| Table | Description |
| --- | --- |
| `Repo.commits` | Commit history. |
| `Repo.branches` | Branch names. |
| `Repo.tags` | Tag names. |

For a full list of metadata tables and columns, see the [documentation](https://vupdivup.github.io/diffhouse/).
