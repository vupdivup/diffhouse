<!-- home-start -->

# diffhouse

*diffhouse* is a **git metadata extraction tool** for Python that retrieves high-quality repository information such as commit history, branches, diffs and more.

## Requirements

Git 2.22 and Python 3.10 or greater required.

<!-- home-end -->

## User guide

<!-- user-guide-start -->

### Installation

Install diffhouse through PyPi:

```sh
pip install diffhouse
```

### Quickstart

First, construct a `Repo` object and define its target repository via the `location` argument; this can be either a remote URL or a local path. Pass `blobs = True` to extract file data as well.

Calling `Repo.load()` will load all requested metadata into memory, which can then be accessed through the object's [properties](https://vupdivup.github.io/diffhouse/api-reference/#diffhouse.Repo).

> `blobs = True` requires a complete clone of the repository and therefore takes longer to execute. Omit this argument whenever possible.

```python
from diffhouse import Repo

r = Repo(
    location = 'https://github.com/octocat/Hello-World',
    blobs = True
).load()

for c in r.commits:
    print(c.commit_hash[:10])
    print(c.author_email)
    print(c.subject)

print(r.branches)
```

<!-- user-guide-end -->
