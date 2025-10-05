<!-- home-start -->

# diffhouse

diffhouse is a **Git metadata extraction tool** for Python, designed to enable
large-scale repository analyses. Key features are:

- Fast access to commit data, file changes and more
- Easy integration with `pandas` and `polars`
- Simple-to-use Python interface

## Requirements

Requires Git 2.22 and Python 3.10 or higher.

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

After importing the package in Python, construct a `Repo` object and define
its target repository via the `location` argument; this can be either a
remote URL or a local path. Pass `blobs = True` to extract file data as well.

Calling `Repo.load()` will load all requested metadata into memory, which can
then be accessed through the object's
[properties](https://vupdivup.github.io/diffhouse/api-reference/#diffhouse.Repo).

> `blobs = True` requires a complete clone of the repository and therefore
> takes longer to execute. Omit this argument whenever possible.

#### Example: Basic Querying

```python
from diffhouse import Repo

r = Repo(
    location = 'https://github.com/octocat/Hello-World',
    blobs = True
).load()

for c in r.commits:
    print(c.commit_hash[:10], c.committer_date, c.author_email)

print(r.branches)
```

outputs:

```text
7fd1a60b01 2012-03-06T15:06:50-08:00 octocat@nowhere.com
762941318e 2011-09-13T21:42:41-07:00 Johnneylee.rollins@gmail.com
553c2077f0 2011-01-26T11:06:08-08:00 cameron@github.com
['master', 'octocat-patch-1', 'test']
```

### Tabular Data

`commits`, `changed_files` and `diffs` iterables can be passed directly to
pandas and polars `DataFrame` constructors. No pre-processing is needed;
table schemas will be inferred correctly.

#### Example: Using Polars

```python
import polars as pl

df = pl.DataFrame(r.changed_files)
df.schema
```

outputs:

```text
Schema([('commit_hash', String),
        ('path_a', String),
        ('path_b', String),
        ('changed_file_id', String),
        ('change_type', String),
        ('similarity', Int64),
        ('lines_added', Int64),
        ('lines_deleted', Int64)])
```

> diffhouse stores datetime values as ISO 8601 strings to preserve time zone
> offsets. When converting these to datetime objects in a `DataFrame`, use
> the parser's UTC option.

### Lazy Loading

For large repositories (100k+ commits), passing `blobs = True` and calling
`load()` can take up gigabytes of memory; in these cases, it's better to use
the lazy method:

```python
with Repo(
    location='https://github.com/octocat/Hello-World',
    blobs = True
) as r:
    for d in r.diffs:
        if d.lines_added == 3:
            break
```

This has two benefits:

1. Data is only loaded for accessed properties.
2. Properties act as lazy iterators, only loading one record at a time.

<!-- user-guide-end -->
