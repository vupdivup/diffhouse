import os
import warnings

import requests

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

if not GITHUB_TOKEN:
    warnings.warn('GITHUB_TOKEN environment variable not set.')


def extract_repo_info(repo_url):
    """Extract owner and repository name from a GitHub URL."""
    if repo_url.endswith('/'):
        repo_url = repo_url[:-1]

    parts = repo_url.split('/')

    owner = parts[-2]
    repo = parts[-1]
    return owner, repo


def get_branches(repo_url):
    """Fetch branches from a GitHub repository."""
    owner, repo = extract_repo_info(repo_url)
    url = f'https://api.github.com/repos/{owner}/{repo}/branches'
    headers = {'Authorization': f'Bearer {GITHUB_TOKEN}'}
    response = requests.get(url, headers=headers)
    branches = response.json()

    return branches


def get_tags(repo_url):
    """Fetch tags from a GitHub repository."""
    owner, repo = extract_repo_info(repo_url)
    url = f'https://api.github.com/repos/{owner}/{repo}/tags'
    headers = {'Authorization': f'Bearer {GITHUB_TOKEN}'}
    response = requests.get(url, headers=headers)
    tags = response.json()

    return tags


def get_commits(repo_url, per_page=30):
    """Fetch commits from a GitHub repository."""
    owner, repo = extract_repo_info(repo_url)
    url = f'https://api.github.com/repos/{owner}/{repo}/commits'
    headers = {'Authorization': f'Bearer {GITHUB_TOKEN}'}
    params = {'per_page': per_page}
    response = requests.get(url, headers=headers, params=params)
    commits = response.json()

    return commits
