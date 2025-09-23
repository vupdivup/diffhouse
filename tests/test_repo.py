import pytest
import pandas as pd

from diffhouse import Repo

REPOS = [
    'https://github.com/ohmyzsh/ohmyzsh',
    'https://github.com/tailwindlabs/tailwindcss',
    'https://github.com/ollama/ollama',
    'https://github.com/microsoft/PowerToys',
    'https://github.com/excalidraw/excalidraw'
]
VALID_URL = 'https://github.com/vupdivup/diffhouse'
INVALID_URL = 'yh8sxKcLRFS14zEa6PvNNPaGMzZA3l'

@pytest.fixture(scope='module', params=REPOS)
def repo(request):
    return Repo(request.param, blobs=True)

@pytest.mark.parametrize('attr,col', [
    ('commits', 'commit_hash'),
    ('branches', 'branch'),
    ('tags', 'tag')])
def test_primary_key(repo, attr, col):
    '''
    Test that `repo.attr` has a valid primary key in column `col`.
    '''
    df = getattr(repo, attr)
    assert col in df.columns
    assert df[col].notna().all()
    assert df[col].is_unique

@pytest.mark.parametrize('attr', ['commits', 'branches', 'tags', 'diffs'])
def test_nulls(repo, attr):
    '''
    Test that `repo.attr` has no fully null rows.
    '''
    df = getattr(repo, attr)
    assert len(df.replace("", pd.NA).dropna(how='all')) == len(df)

@pytest.mark.parametrize('attr', ['commits', 'branches', 'diffs'])
def test_not_empty(repo, attr):
    '''
    Test that `repo.attr` is not empty.
    '''
    df = getattr(repo, attr)
    assert not df.empty

def test_diff_matches(repo):
    '''
    Tests that the join of status changes and line changes to form diffs is
    correct.
    '''
    assert len(repo.diffs) == len(repo._status_changes)
    assert len(repo.diffs) == len(repo._line_changes)

@pytest.mark.parametrize('df', ['commits', 'branches', 'tags', 'diffs'])
def test_source_col(repo, df):
    '''
    Test that `repo.attr` has a `repository` column.
    '''
    assert 'repository' in getattr(repo, df).columns

def test_invalid_url():
    '''
    Test that initializing `Repo` with an invalid URL raises an exception.
    '''
    with pytest.raises(Exception):
        Repo(INVALID_URL)

def test_no_blobs():
    '''
    Test that initializing `Repo` with `blobs`=`False` does not load diffs.
    '''
    r = Repo(VALID_URL, blobs=False)
    with pytest.raises(ValueError):
        r.diffs
