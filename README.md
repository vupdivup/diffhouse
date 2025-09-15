# diffhouse

*diffhouse* is a commit history analysis tool for Python. It extracts tabular commit data from a git repository via `git log`.

> *diffhouse* currently provides data for main-branch commits only.

## Requirements

Git version 2.19 or greater.

## Quick start

1. Install *diffhouse* with pip:

```bash
pip install diffhouse
```

2. Import the `Repo` class in Python:

```python
from diffhouse import Repo
```

3. Create a `Repo` instance with the git repository URL as an argument. Commit data will automatically be loaded into its `commits` property as a *pandas* [`DataFrame`](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html):

```python
r = Repo('https://github.com/user/name.git')
r.commits.head()
```

## Schema

*diffhouse* commit history tables have the following structure:

| Column | Description |
| --- | --- |
| `commit_hash` | Full hash of the commit. |
| `author_name` | Author username. |
| `author_email`   | Author email. |
| `author_date`    | Commit creation date. |
| `committer_name` | Committer username. |
| `committer_email`| Committer email. |
| `committer_date` | Commit apply date. |
| `subject`        | Subject line of the commit message. |
| `body`           | Body of the commit message. |
