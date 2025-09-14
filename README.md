# diffhouse

*diffhouse* is a commit history analysis tool for Python. It extracts tabular commit data from a git repository via its `git log` output.

> Only main-branch commits are shown.

## Requirements

Git v2.19 or greater.

## User guide

Simply create a `Repo` object with the git repository URL as an argument. Commit data will automatically be loaded into its `commits` property as a *pandas* [`DataFrame`](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html).

```python
from diffhouse import Repo

r = Repo('https://github.com/user/name.git')
r.commits.head()
```
