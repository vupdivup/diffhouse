<!-- home-start -->

# diffhouse

diffhouse is a **Git metadata extraction tool** for Python designed for
large-scale analysis of repositories. Key features are:

- Fast access to commit data, file changes and more
- Easy integration with `pandas` and `polars`
- Simple-to-use Python interface

## Requirements

Requires Git 2.22 and Python 3.10 or higher.

<!-- home-end -->

## User guide

<!-- user-guide-start -->

### Installation

Install diffhouse through PyPi:

```sh
pip install diffhouse
```

### Quickstart

First, construct a `Repo` object and define its target repository via the
`location` argument; this can be either a remote URL or a local path. Pass
`blobs = True` to extract file data as well.

Calling `Repo.load()` will load all requested metadata into memory, which can
then be accessed through the object's
[properties](https://vupdivup.github.io/diffhouse/api-reference/#diffhouse.Repo)
.

> `blobs = True` requires a complete clone of the repository and therefore
> takes longer to execute. Omit this argument whenever possible.

#### Example

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
