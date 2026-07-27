#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ -d ".venv" ]; then
  . .venv/bin/activate
else
  echo "Virtual environment not found. Run: python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi
python browser.py
