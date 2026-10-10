#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
    echo "Python環境がありません。README.md のセットアップ手順を実行してください。"
    exit 1
fi
export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-8888}"
exec .venv/bin/python main.py
