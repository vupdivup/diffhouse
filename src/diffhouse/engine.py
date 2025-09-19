import pandas as pd
import re
import csv

from io import StringIO

from .git import GitCLI

def get_remote_url(path: str, remote: str='origin') -> str:
    '''
    Get the URL of a remote of a git repository.

    Args:
        path (str): Path to the local git repository.
        remote (str): Name of the remote.

    Returns:
        url (str): URL of the remote.
    '''
    git = GitCLI(path)
    return git.run('remote', 'get-url', remote).strip()

def get_commits(path: str) -> pd.DataFrame:
    '''
    Get tabular `git log` output from a git repository at `path`.

    Args:
        path (str): Path to the local git repository.

    Returns:
        output (DataFrame): Tabular git log output.
    '''
    FORMAT_SPECIFIERS = {
        'commit_hash': '%H',
        'author_name': '%an',
        'author_email': '%ae',
        'author_date': '%ad',
        'committer_name': '%cn',
        'committer_email': '%ce',
        'committer_date': '%cd',
        'subject': '%s',
        'body': '%b'
    }

    COLUMNS = list(FORMAT_SPECIFIERS.keys())

    COLUMN_SEPARATOR = chr(0x1f)
    RECORD_SEPARATOR = chr(0x1e)

    # prepare git log command
    specifiers = COLUMN_SEPARATOR.join(
        FORMAT_SPECIFIERS.values()
    )
    pattern = f'{specifiers}{RECORD_SEPARATOR}'

    # run git log
    git = GitCLI(path)
    output = git.run('log', f'--pretty=format:{pattern}', '--date=iso')

    try:
        df = pd.read_csv(
            StringIO(output), 
            sep=COLUMN_SEPARATOR,
            lineterminator=RECORD_SEPARATOR,
            engine='c',
            header=None,
            names=COLUMNS,
            on_bad_lines='warn',
            encoding_errors='replace',
            quoting=csv.QUOTE_NONE
        )
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=COLUMNS)

    # parse dates, UTC for mixed timezones
    for col in ['author_date', 'committer_date']:
        df[col] = pd.to_datetime(df[col], utc=True)

    # trim all whitespace of string columns
    for col in df:
        if df[col].dtype == 'object':
            df[col] = df[col].str.strip()

    return df

def get_branches(path: str) -> pd.DataFrame:
    '''
    Get branches of a remote git repository via `git branch`.

    Args:
        path (str): Path to the local git repository.
    
    Returns:
        branches (DataFrame): List of branches.
    '''
    git = GitCLI(path)
    output = git.run('branch')

    branches = re.findall(r' +(.+)\n', output)

    return pd.DataFrame(branches, columns=['branch'])

def get_tags(path: str) -> pd.DataFrame:
    '''
    Get tags of a remote git repository via `git tag`.

    Args:
        path (str): Path to the local git repository.

    Returns:
        tags (DataFrame): List of tags.
    '''
    git = GitCLI(path)
    output = git.run('tag')

    tags = output.split('\n')[:-1]

    return pd.DataFrame(tags, columns=['tag'])

def get_status_changes(path: str) -> pd.DataFrame:
    '''
    Get file status changes (e.g. `A` for added) for repository at `path`.
    '''
    git = GitCLI(path)
    output = git.run('log', f'--pretty=format:{chr(0x1f)}%H', '--name-status')
    commits = output.split(chr(0x1f))[1:]

    data = []
    for c in commits:
        lines = [l.strip() for l in c.strip().split('\n')]
        hash = lines[0]

        for l in lines[1:]:
            items = [i.strip() for i in l.split('\t')]
            status = items[0][0]

            if status in ['R', 'C']:
                similarity = float(items[0][1:])
                file = items[2]
                renamed_from = items[1] if status == 'R' else None
                copied_from = items[1] if status == 'C' else None

            else:
                similarity = None
                file = items[1]
                renamed_from = None
                copied_from = None
            
            data.append({
                'commit_hash': hash,
                'file': file,
                'status': status,
                'renamed_from': renamed_from,
                'copied_from': copied_from,
                'similarity': similarity
            })

    return pd.DataFrame(data)
