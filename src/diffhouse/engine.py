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

def get_branches(path: str) -> pd.Series:
    '''
    Get branches of a git repository at `path` via `git ls-remote`.
    '''
    git = GitCLI(path)
    output = git.run('ls-remote', '--branches', '--refs')

    branches = [b.strip() for b in re.findall(r'refs/heads/(.+)\n', output)]

    return pd.Series(branches)

def get_tags(path: str) -> pd.Series:
    '''
    Get tags of a git repository at `path` via `git ls-remote`.
    '''
    git = GitCLI(path)
    output = git.run('ls-remote', '--tags', '--refs')

    tags = [t.strip() for t in re.findall(r'refs/tags/(.+)\n', output)]

    return pd.Series(tags)

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
                from_file = items[1]
            else:
                similarity = None
                file = items[1]
                from_file = None
            
            data.append({
                'commit_hash': hash,
                'file': file,
                'status': status,
                'from_file': from_file,
                'similarity': similarity
            })

    return pd.DataFrame(data)

def get_numstats(path: str) -> pd.DataFrame:
    '''
    Get file-level number of lines added and deleted per commit for repository
    at `path`.
    '''
    git = GitCLI(path)
    output = git.run('log', f'--pretty=format:{chr(0x1f)}%H', '--numstat')
    commits = output.split(chr(0x1f))[1:]

    data = []
    for c in commits:
        lines = [l.strip() for l in c.strip().split('\n')]
        hash = lines[0]

        for l in lines[1:]:
            items = [i.strip() for i in l.split('\t')]
            lines_added = 0 if items[0] == '-' else int(items[0])
            lines_deleted = 0 if items[1] == '-' else int(items[1])

            file_expr = items[2]

            if '{' in file_expr:
                # ../../{a => b}
                # ../{ => a}/..
                from_file = re.sub(r'\{(.*) => .*\}', r'\1', file_expr) \
                    .replace('//', '/')
                file = re.sub(r'\{.* => (.*)\}', r'\1', file_expr) \
                    .replace('//', '/')
            else:
                # ../../a => ../../b
                # when the file is moved to a different branch in the tree
                match = re.match(r'(.+) => (.+)', file_expr)
                from_file = match.group(1) if match else file_expr
                file = match.group(2) if match else file_expr

            data.append({
                'commit_hash': hash,
                'file': file,
                'from_file': from_file,
                'lines_added': lines_added,
                'lines_deleted': lines_deleted
            })

    df = pd.DataFrame(data)
    df['from_file'] = df.from_file.where(df['from_file'] != df['file'], None)

    return df
