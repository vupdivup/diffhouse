from datetime import datetime
from types import LambdaType

from diffhouse import Branch, Commit, Diff, FileMod, Repo, Tag
from tests.constants import (
    OBJECT_TYPES_BY_REPO_ATTR,
    SCHEMAS_BY_OBJECT_TYPE,
    TYPED_SCHEMAS_BY_OBJECT_TYPE,
)
from tests.fixtures import repo  # noqa: F401


def assert_branch_is_valid(b: Branch) -> None:
    """Assert that branch data is valid."""
    assert isinstance(b, Branch)
    assert b.name != ''
    assert ' ' not in b.name
    assert ': ' not in b.name


def assert_tag_is_valid(t: Tag) -> None:
    """Assert that tag data is valid."""
    assert isinstance(t, Tag)
    assert t.name != ''
    assert ' ' not in t.name
    assert ': ' not in t.name


def assert_commit_is_valid(c: Commit) -> None:
    """Assert that commit data is valid."""
    assert isinstance(c, Commit)
    assert len(c.commit_hash) == 40
    assert c.is_merge or len(c.parents) < 2

    for p in c.parents:
        assert len(p) == 40

    for dt in (
        c.date,
        c.date_local,
        c.author_date,
        c.author_date_local,
    ):
        assert isinstance(dt, datetime)
        assert dt.tzinfo is None  # all datetimes are naive

    assert c.lines_added >= 0
    assert c.lines_deleted >= 0
    assert c.files_changed >= 0


def assert_filemod_is_valid(f: FileMod) -> None:
    """Assert that file modification data is valid."""
    assert isinstance(f, FileMod)
    assert len(f.commit_hash) == 40

    assert f.path_a != ''
    assert f.path_b != ''

    assert f.change_type in ['A', 'D', 'M', 'R', 'C', 'T', 'U']

    assert f.path_a == f.path_b or f.change_type in ['R', 'C']
    assert f.similarity == 100 or f.change_type in ['R', 'C']

    assert f.lines_added >= 0
    assert f.lines_deleted >= 0


def assert_diff_is_valid(d: Diff) -> None:
    """Assert that diff data is valid."""
    assert isinstance(d, Diff)
    assert len(d.commit_hash) == 40

    assert d.lines_added >= 0
    assert d.lines_deleted >= 0

    assert len(d.additions) == d.lines_added
    assert len(d.deletions) == d.lines_deleted


ASSERT_FUNCS_BY_OBJECT_TYPE = {
    Branch: assert_branch_is_valid,
    Tag: assert_tag_is_valid,
    Commit: assert_commit_is_valid,
    FileMod: assert_filemod_is_valid,
    Diff: assert_diff_is_valid,
}


def assert_dict_matches_typed_schema(item: dict, schema: dict) -> None:
    """Assert that a dictionary matches a typed schema."""
    for field, field_type in schema.items():
        if isinstance(field_type, LambdaType):
            assert field_type(item[field])
        else:
            assert isinstance(item[field], field_type)


def test_iter(repo: Repo) -> None:  # noqa: F811
    """Test that items can be iterated and are valid."""
    for attr, type_ in OBJECT_TYPES_BY_REPO_ATTR.items():
        assertor = ASSERT_FUNCS_BY_OBJECT_TYPE[type_]
        for item in getattr(repo, attr):
            assertor(item)


def test_to_list(repo: Repo) -> None:  # noqa: F811
    """Test that items can be converted to a list and are valid."""
    for attr, type_ in OBJECT_TYPES_BY_REPO_ATTR.items():
        assertor = ASSERT_FUNCS_BY_OBJECT_TYPE[type_]
        for item in getattr(repo, attr).to_list():
            assertor(item)


def test_iter_dicts(repo: Repo) -> None:  # noqa: F811
    """Test that items can be iterated as dicts with the correct schema."""
    for attr, type_ in OBJECT_TYPES_BY_REPO_ATTR.items():
        schema = TYPED_SCHEMAS_BY_OBJECT_TYPE[type_]
        for item in getattr(repo, attr).iter_dicts():
            assert_dict_matches_typed_schema(item, schema)


def test_to_dicts(repo: Repo) -> None:  # noqa: F811
    """Test that items can be converted to a dict with the correct schema."""
    for attr, type_ in OBJECT_TYPES_BY_REPO_ATTR.items():
        schema = TYPED_SCHEMAS_BY_OBJECT_TYPE[type_]
        for item in getattr(repo, attr).to_dicts():
            assert_dict_matches_typed_schema(item, schema)


def test_to_pandas(repo: Repo) -> None:  # noqa: F811
    """Test conversion to pandas DataFrames."""
    for attr, type_ in OBJECT_TYPES_BY_REPO_ATTR.items():
        schema = SCHEMAS_BY_OBJECT_TYPE[type_]
        df = getattr(repo, attr).to_pandas()

        assert set(df.columns) == schema


def test_to_polars(repo: Repo) -> None:  # noqa: F811
    """Test conversion to Polars DataFrames."""
    for attr, type_ in OBJECT_TYPES_BY_REPO_ATTR.items():
        schema = SCHEMAS_BY_OBJECT_TYPE[type_]
        df = getattr(repo, attr).to_polars()

        assert set(df.columns) == schema
