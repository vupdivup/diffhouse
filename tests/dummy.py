import time

from diffhouse import Repo
from tests.constants import VALID_URL

if __name__ == '__main__':
    with Repo(VALID_URL) as r:
        while True:
            time.sleep(1)
