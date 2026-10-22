#!/bin/bash
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo 'Run bash scripts/setup.sh first. See docs/Delivery.md.'
  read -r -p 'Press Enter to close.'
  exit 1
fi
.venv/bin/python scripts/start.py --preview
read -r -p 'Press Enter to close.'
