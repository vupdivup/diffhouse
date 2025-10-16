# diffhouse: Repository Mining at Scale

[![PyPI](https://img.shields.io/pypi/v/diffhouse)](https://pypi.org/project/diffhouse/) [![DOI](https://zenodo.org/badge/1052651155.svg)](https://doi.org/10.5281/zenodo.17368264) [![Test status](https://img.shields.io/github/actions/workflow/status/vupdivup/diffhouse/os-test.yml?label=tests&branch=main)](https://github.com/vupdivup/diffhouse/actions/workflows/os-test.yml)

[Documentation](https://vupdivup.github.io/diffhouse/)

<!-- home-start -->

diffhouse is a **Python solution for structuring Git metadata**, designed to enable
large-scale codebase analysis at practical speeds.

Key features are:

- Fast access to commit data, file changes and more
- Easy integration with `pandas` and `polars`
- Simple-to-use Python interface

## Requirements

| Python | Git |
| --- | --- |
| 3.10 or higher | 2.22 or higher |

Git also needs to be available in the system PATH.

## Limitations

At its core, diffhouse is a data *extraction* tool and therefore does not calculate software metrics like code churn or cyclomatic complexity; if this is needed, take a look at [PyDriller](https://github.com/ishepard/pydriller) instead.

Also note that revision data is limited to **default branches only**.

<!-- home-end -->

## User Guide

<!-- user-guide-start -->

This guide aims to cover the basic use cases of diffhouse. For the list of
available repository objects and fields, check out the
[API Reference](https://vupdivup.github.io/diffhouse/api-reference).

### Installation

Install diffhouse through PyPi:

```sh
pip install diffhouse
```

### Quickstart

```python
from diffhouse import Repo

url = 'https://github.com/user/repo'

r = Repo(location = url, blobs = True).load()

for c in r.commits:
    print(c.commit_hash[:10], c.committer_date, c.author_email)

print(r.branches)
print(r.diffs[0].to_dict())
```

First, construct a `Repo` object and define
its target repository via the `location` argument; this can be either a
remote URL or a local path. Pass `blobs = True` to extract file data as well.

Calling `Repo.load()` will load all metadata into memory, which can
then be accessed through the object's properties.
[See all properties](https://vupdivup.github.io/diffhouse/api-reference/#diffhouse.Repo.branches)

> `blobs = True` requires a complete clone of the repository and therefore
> takes longer to execute. Omit this argument whenever possible.

### Lazy Loading

For large repositories, calling
`load()` can be slow and/or take up gigabytes of memory. It is recommended to
use the lazy method via `with` instead:

```python
with Repo(location = url, blobs = True) as r:
    c = list(r.stream_commits())

    for d in r.stream_diffs():
        if d.lines_added == 3:
            break
```

This brings two big benefits:

1. Object streaming functions are lazy generators, allowing for efficient memory use.
2. No processing power is spent on objects that are not explicitly requested.

[See all streaming functions](https://vupdivup.github.io/diffhouse/api-reference/#diffhouse.Repo.stream_commits)

### Tabular Data

`Commit`, `ChangedFile` and `Diff` iterables can be passed directly to
pandas and polars `DataFrame` constructors. No pre-processing is needed;
table schemas will be inferred correctly.

```python
import polars as pl

df = pl.DataFrame(r.changed_files)
print(df.schema)
```

> diffhouse stores datetime values as ISO 8601 strings to preserve time zone
> offsets. When converting these to datetime objects in a `DataFrame`, use
> the parser's UTC option.

<!-- user-guide-end -->
