#!/bin/sh
cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
  echo "Creating the project environment. This happens only once."
  python3 -m venv .venv || { echo "Install Python 3 first."; read -r; exit 1; }
  .venv/bin/python -m pip install --upgrade pip || { read -r; exit 1; }
  .venv/bin/python -m pip install -r requirements.txt || { read -r; exit 1; }
fi

exec .venv/bin/python run_project.py
