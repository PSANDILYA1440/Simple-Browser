#!/bin/bash
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Virtualenv not found. Create it first with: python3 -m venv .venv"
  exit 1
fi

SYSTEM_PY="/usr/bin/python3"
if [ ! -x "$SYSTEM_PY" ]; then
  echo "System Python not found at /usr/bin/python3. Please install or use a compatible Python interpreter."
  exit 1
fi

PACK_VENV="$(pwd)/.packaging-venv"
if [ ! -d "$PACK_VENV" ]; then
  "$SYSTEM_PY" -m venv "$PACK_VENV"
fi

PACK_PY="$PACK_VENV/bin/python"
"$PACK_PY" -m pip install --upgrade pip
"$PACK_PY" -m pip install py2app dmgbuild macholib PyQt6 PyQt6-WebEngine
"$PACK_PY" setup.py py2app
mkdir -p dist

dmgbuild -s dmgbuild.json "SimpleBrowser" dist/SimpleBrowser.dmg

echo "Packaged dist/SimpleBrowser.dmg"
