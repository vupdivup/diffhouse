# diffhouse: Repository Mining at Scale

[![PyPI](https://img.shields.io/pypi/v/diffhouse)](https://pypi.org/project/diffhouse/) [![DOI](https://zenodo.org/badge/1052651155.svg)](https://doi.org/10.5281/zenodo.17368264) [![Test status](https://img.shields.io/github/actions/workflow/status/vupdivup/diffhouse/os-test.yml?label=tests&branch=main)](https://github.com/vupdivup/diffhouse/actions/workflows/os-test.yml)

[Documentation](https://vupdivup.github.io/diffhouse/)

<!-- home-start -->

diffhouse is a **Python solution for structuring Git metadata**, designed to enable
large-scale codebase analysis at practical speeds.

Key features are:

- Fast access to commit data, file changes and more
- Easy integration with **pandas** and **polars**
- Simple-to-use Python interface

## Requirements

<table>
    <tr>
        <td><strong>Python</strong></td>
        <td>3.10 or higher</td>
    </tr>
    <tr>
        <td><strong>Git</strong></td>
        <td>2.22 or higher</td>
    </tr>
</table>

Git also needs to be added to the system PATH.

## Limitations

At its core, diffhouse is a data *extraction* tool and therefore does not calculate software metrics like code churn or cyclomatic complexity; if this is needed, take a look at [PyDriller](https://github.com/ishepard/pydriller) instead.

<!-- home-end -->

## User Guide

<!-- user-guide-start -->

This guide aims to cover the basic use cases of diffhouse. For a full list of objects, consider reading the
[API Reference](https://vupdivup.github.io/diffhouse/api-reference).

### Installation

Install diffhouse from PyPI:

```sh
pip install diffhouse
```

If you plan to combine diffhouse with pandas or Polars, install the package with either the `[pandas]` or `[polars]` extra:

```sh
pip install diffhouse[pandas]  # or [polars]
```

### Quickstart

```py
from diffhouse import Repo

with Repo('https://github.com/user/repo') as r:
    for c in r.commits:
        print(c.commit_hash[:10], c.committer_date, c.author_email)

    if len(r.branches.to_list()) > 100:
        print('🎉')

    df = r.diffs.to_pandas()
```

To start, create a [`Repo`](https://vupdivup.github.io/diffhouse/api-reference/repo/) instance by passing either a Git-hosting URL or a local path as its `source` argument. Next, use the `Repo` in a `with` statement to clone the source into a local, non-persistent
location.

Inside the `with` block, you can access data through the following properties:

| Property | Description | Record Type
| --- | --- | --- |
| [`Repo.commits`](https://vupdivup.github.io/diffhouse/repo/#diffhouse.Repo.commits) | Commit history of the repository. | [`Commit`](https://vupdivup.github.io/diffhouse/api-reference/commit/) |
| [`Repo.filemods`](https://vupdivup.github.io/diffhouse/repo/#diffhouse.Repo.filemods) | File modifications across the commit history. | [`FileMod`](https://vupdivup.github.io/diffhouse/api-reference/filemod/) |
| [`Repo.diffs`](https://vupdivup.github.io/diffhouse/repo/#diffhouse.Repo.diffs) | Source code changes across the commit history. | [`Diff`](https://vupdivup.github.io/diffhouse/api-reference/diff/) |
| [`Repo.branches`](https://vupdivup.github.io/diffhouse/repo/#diffhouse.Repo.branches) | Branches of the repository. | [`Branch`](https://vupdivup.github.io/diffhouse/api-reference/branch/) |
| [`Repo.tags`](https://vupdivup.github.io/diffhouse/repo/#diffhouse.Repo.tags) | Tags of the repository. | [`Tag`](https://vupdivup.github.io/diffhouse/api-reference/tag/) |

### Querying Results

Data accessors like `Repo.commits` are [`Extractor`](https://vupdivup.github.io/diffhouse/api-reference/extractor/) objects and can output their results in various formats:

#### Looping Through Objects

You can use extractors in a `for` loop to process objects one by one. Data will be extracted on demand for memory efficiency:

```py
with Repo('https://github.com/user/repo') as r:
    for c in r.commits:
        print(c.commit_hash[:10])
        print(c.author_name)

        if c.in_main:
            break
```

`iter_dicts()` is a `for` loop alternative that yields dictionaries instead of diffhouse objects. A good use case for this is writing results into a newline-delimited JSON file:

```py
import json

with (
    Repo('https://github.com/user/repo') as r,
    open('commits.jsonl', 'w') as f
):
    for c in r.commits.iter_dicts():
        f.write(json.dumps(c) + '\n')
```

#### Converting to Dataframes

pandas and Polars `DataFrame` APIs are supported out of the box. To convert result sets to dataframes, call the following methods:

- `to_pandas()` or `pd()` for pandas
- `to_polars()` or `pl()` for Polars

```py
with Repo('https://github.com/user/repo') as r:
    df1 = r.filemods.to_pandas()  # pandas
    df2 = r.diffs.to_polars()  # Polars
```

Datetime values are stored as ISO 8601 strings to preserve time zone offsets. When converting these to datetime objects in a `DataFrame`, use the parser's UTC option. With pandas, it'd look like this:

```py
import pandas as pd

with Repo('https://github.com/user/repo') as r:
    df = r.commits.to_pandas()

df['author_date'] = pd.to_datetime(
    df['author_date'], utc=True
)
```

### Preliminary Filtering

You can filter data along certain dimensions *before* processing takes place to reduce extraction time and/or network load.

> [!NOTE]
> Filters are a WIP feature. Additional options like date and branch filtering are planned for future releases.

#### Skipping File Downloads

If no blob-level data is needed, pass `blobs=False` when creating the `Repo` to skip file downloads during cloning. Note that this will not populate:

- `files_changed`, `lines_added` and `lines_deleted` fields of `Repo.commits`
- `Repo.filemods`
- `Repo.diffs`

```py
with Repo('https://github.com/user/repo', blobs=False) as r:
    for b in r.branches:
        pass  # business as usual

    r.filemods  # throws FilterError
```

<!-- user-guide-end -->
