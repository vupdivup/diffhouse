import os
import warnings

import requests

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

if not GITHUB_TOKEN:
    warnings.warn('GITHUB_TOKEN environment variable not set.')


def get_github_response(url: str, per_page: int = 50) -> requests.Response:
    """Get a response from the GitHub API.

    Args:
        url: The API endpoint URL.
        per_page: The number of items to return per page.

    Returns:
        response: The response object from the API call.

    """
    headers = {}
    params = {'per_page': per_page}

    if GITHUB_TOKEN:
        headers['Authorization'] = f'Bearer {GITHUB_TOKEN}'

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response


def extract_repo_info(repo_url) -> tuple[str, str]:
    """Extract owner and repository name from a GitHub URL.

    Args:
        repo_url: URL of the GitHub repository.

    Returns:
        owner: Owner of the repository.
        repo: Name of the repository. DOESNT WORK

    """
    if repo_url.endswith('/'):
        repo_url = repo_url[:-1]

    parts = repo_url.split('/')

    owner = parts[-2]
    repo = parts[-1]
    return owner, repo


def get_branches(repo_url) -> list[dict]:
    """Fetch branches from a GitHub repository.

    Args:
        repo_url: URL of the GitHub repository.

    Returns:
        branches: List of branches in the repository.

    """
    owner, repo = extract_repo_info(repo_url)
    url = f'https://api.github.com/repos/{owner}/{repo}/branches'
    response = get_github_response(url)

    return response.json()


def get_tags(repo_url) -> list[dict]:
    """Fetch tags from a GitHub repository.

    Args:
        repo_url: URL of the GitHub repository.

    Returns:
        tags: List of tags in the repository.

    """
    owner, repo = extract_repo_info(repo_url)
    url = f'https://api.github.com/repos/{owner}/{repo}/tags'
    response = get_github_response(url)

    return response.json()


def get_commits(repo_url) -> list[dict]:
    """Fetch commits from a GitHub repository.

    Args:
        repo_url: URL of the GitHub repository.

    Returns:
        commits: List of commits in the repository.

    """
    owner, repo = extract_repo_info(repo_url)
    url = f'https://api.github.com/repos/{owner}/{repo}/commits'
    response = get_github_response(url)
    return response.json()
