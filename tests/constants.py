from datetime import datetime

from diffhouse import Branch, Commit, Diff, FileMod, Tag

# 1-10k commits
# can't do larger since ubuntu runners have trouble computing dataframe results
REPOS = [
    'https://github.com/vuejs/vue',
    'https://github.com/Significant-Gravitas/AutoGPT',
    'https://github.com/Genymobile/scrcpy',
    'https://github.com/d3/d3',
    'https://github.com/axios/axios',
    'https://github.com/microsoft/terminal',
    'https://github.com/ohmyzsh/ohmyzsh',
    'https://github.com/ollama/ollama',
    'https://github.com/microsoft/PowerToys',
    'https://github.com/excalidraw/excalidraw',
    'https://github.com/fatedier/frp',
    'https://github.com/rustdesk/rustdesk',
    'https://github.com/tauri-apps/tauri',
    'https://github.com/fastapi/fastapi',
    'https://github.com/angular/angular.js',
    'https://github.com/AUTOMATIC1111/stable-diffusion-webui',
    'https://github.com/expressjs/express',
    'https://github.com/Eugeny/tabby',
    'https://github.com/redis/redis',
    'https://github.com/pallets/flask',
    'https://github.com/vitejs/vite',
    'https://github.com/koekeishiya/yabai',
    'https://github.com/pypa/pipenv',
    'https://github.com/ai/nanoid',
    'https://github.com/rollup/rollup',
    'https://github.com/Modernizr/Modernizr',
    'https://github.com/request/request',
    'https://github.com/microsoft/winget-cli',
    'https://github.com/google/flatbuffers',
    'https://github.com/libuv/libuv',
    'https://github.com/PostgREST/postgrest',
    'https://github.com/hammerjs/hammer.js',
    'https://github.com/emilk/egui',
    'https://github.com/winstonjs/winston',
    'https://github.com/sxyazi/yazi',
    'https://github.com/stretchr/testify',
    'https://github.com/vuejs/vuepress',
]

VALID_URL = 'https://github.com/ohmyzsh/ohmyzsh'

INVALID_URL = 'yh8sxKcLRFS14zEa6PvNNPaGMzZA3l'

GITHUB_COMMITS_SAMPLE_SIZE = 1000
GITHUB_SHORTSTATS_SAMPLE_SIZE = 10

TYPED_SCHEMAS_BY_OBJECT_TYPE = {
    Commit: {
        'commit_hash': str,
        'date': datetime,
        'date_local': datetime,
        'message_subject': str,
        'message_body': str,
        'author_name': str,
        'author_email': str,
        'author_date': datetime,
        'author_date_local': datetime,
        'committer_name': str,
        'committer_email': str,
        'files_changed': lambda x: isinstance(x, int) or x is None,
        'lines_added': lambda x: isinstance(x, int) or x is None,
        'lines_deleted': lambda x: isinstance(x, int) or x is None,
        'source': str,
        'in_main': bool,
        'is_merge': bool,
        'parents': lambda x: isinstance(x, list)
        and all(isinstance(i, str) for i in x),
    },
    Branch: {
        'name': str,
    },
    FileMod: {
        'commit_hash': str,
        'path_a': str,
        'path_b': str,
        'filemod_id': str,
        'change_type': str,
        'similarity': int,
        'lines_added': int,
        'lines_deleted': int,
    },
    Diff: {
        'commit_hash': str,
        'path_a': str,
        'path_b': str,
        'filemod_id': str,
        'start_a': int,
        'length_a': int,
        'start_b': int,
        'length_b': int,
        'lines_added': int,
        'lines_deleted': int,
        'additions': lambda x: isinstance(x, list)
        and all(isinstance(i, str) for i in x),
        'deletions': lambda x: isinstance(x, list)
        and all(isinstance(i, str) for i in x),
    },
    Tag: {
        'name': str,
    },
}

SCHEMAS_BY_OBJECT_TYPE = {
    k: set(v.keys()) for k, v in TYPED_SCHEMAS_BY_OBJECT_TYPE.items()
}

OBJECT_TYPES_BY_REPO_ATTR = {
    'commits': Commit,
    'branches': Branch,
    'filemods': FileMod,
    'diffs': Diff,
    'tags': Tag,
}

REPO_ATTRS = list(OBJECT_TYPES_BY_REPO_ATTR.keys())
