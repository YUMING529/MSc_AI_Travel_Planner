#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-lock.txt
(cd frontend && npm ci && npm run build && npm test)
.venv/bin/python -m unittest discover -s backend/tests -v
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  chmod 600 backend/.env
fi
printf '\nSetup complete. Configure backend/.env locally, then run: .venv/bin/python scripts/start.py --preview\n'
