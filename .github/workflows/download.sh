#!/usr/bin/bash


git config --global user.email "iamrony777@pm.me"
git config --global user.name "iamrony777"

## Poetry Installation    
export PATH="$HOME/.local/bin:$PATH"
curl -sSL https://install.python-poetry.org | POETRY_HOME="$HOME/.local" python3.10
# poetry config virtualenvs.prefer-active-python true
poetry config virtualenvs.create false && \
poetry export --output=requirements.txt --without=dev --without-hashes --no-ansi && \
pip3.10 install -r requirements.txt

if [[ -e scripts/async_download_exts.py ]]; then
    mkdir extensions
    git lfs install && \
    python3.10 scripts/async_download_exts.py && \
    git add -f extensions/*.vsix && \
    git commit -am "Update $(date)"
    git push origin main
else
    "File not Found"
fi