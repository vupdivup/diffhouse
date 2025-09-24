# diffhouse

*diffhouse* is a **git metadata extraction tool** for Python that retrieves high-quality repository information such as commit history, branches, diffs and more.

## Requirements

Git 2.20 and Python 3.10 or greater required.

## Quick start

1. Install *diffhouse* with pip:

```bash
pip install diffhouse
```

2. Import the `Repo` class in Python:

```python
from diffhouse import Repo
```

3. Create a `Repo` instance with the git repository URL as an argument. Set `blobs` to `True` to load file-level diffs as well.

> Note that `blobs=True` greatly increases processing time, as it requires a complete clone of the repository.

```python
r = Repo(url='https://github.com/user/name.git', blobs=True)
```

4. Access data through the following *pandas* [`DataFrames`](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html):

| Table | Description |
| --- | --- |
| `Repo.commits` | Commit history. |
| `Repo.branches` | Branch names. |
| `Repo.tags` | Tag names. |
| `Repo.diffs` | File-level changes. Available if `blobs` is `True`. |

For a full list of objects and table columns, see the [documentation](https://vupdivup.github.io/diffhouse/).
