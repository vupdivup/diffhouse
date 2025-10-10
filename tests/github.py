import math
import os
import random
import re
import warnings
from collections.abc import Iterator
from typing import Literal

import requests

PER_PAGE_LIMIT = 100

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

if not GITHUB_TOKEN:
    warnings.warn('GITHUB_TOKEN environment variable not set.')


def extract_repo_info(repo_url: str) -> tuple[str, str]:
    """Extract owner and repository name from a GitHub URL.

    Args:
        repo_url: URL of the GitHub repository.

    Returns:
        owner: Owner of the repository.
        repo: Name of the repository.

    """
    if repo_url.endswith('/'):
        repo_url = repo_url[:-1]

    parts = repo_url.split('/')

    owner = parts[-2]
    repo = parts[-1]
    return owner, repo


def get_github_response(url: str, headers={}, params={}) -> requests.Response:
    """Get a response from the GitHub API.

    Args:
        url: The API endpoint URL.
        headers: Optional headers to include in the request.
        params: Optional query parameters to include in the request.

    Returns:
        response: The response object from the API call.

    """
    headers = {**headers}
    params = {**params}

    params['per_page'] = PER_PAGE_LIMIT

    if GITHUB_TOKEN:
        headers['Authorization'] = f'Bearer {GITHUB_TOKEN}'

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response


def sample_github_endpoint(
    repo_url: str,
    entity: Literal['commits', 'branches', 'tags'],
    n: int,
    headers: dict = {},
    params: dict = {},
) -> Iterator[dict]:
    """Sample at least n items from a GitHub repository endpoint, in a semi-random manner.

    Args:
        repo_url: URL of the GitHub repository.
        entity: The entity to fetch (e.g., 'branches', 'tags', 'commits').
        n: Minimum number of items to sample. Actual number is determined by
            pagination.
        headers: Optional headers to include in the request.
        params: Optional query parameters to include in the request.

    Yields:
        An item from the specified entity.

    """
    owner, repo = extract_repo_info(repo_url)
    url = f'https://api.github.com/repos/{owner}/{repo}/{entity}'

    resp = get_github_response(url, headers, params)
    yield from resp.json()

    link = resp.headers.get('Link', None)

    # if there's no Link header, there's only one page of results
    if not link:
        return

    last_page = int(re.search(r'page=(\d+)>; rel="last"', link).group(1))

    pages_left = math.ceil(n / PER_PAGE_LIMIT) - 1

    # randomly select pages
    pages = random.sample(
        range(2, last_page + 1), min(pages_left, last_page - 1)
    )

    for p in pages:
        yield from get_github_response(
            url, headers, {**params, 'page': p}
        ).json()
