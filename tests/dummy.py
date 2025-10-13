from diffhouse import Repo

from .constants import CLEANUP_REPO_URL

if __name__ == '__main__':
    Repo(CLEANUP_REPO_URL, blobs=True).load()
