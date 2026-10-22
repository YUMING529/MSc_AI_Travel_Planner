#!/usr/bin/env python3
"""Local-only launcher; never terminates an existing process or overwrites credentials."""
import argparse
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import signal

def stop(signum, frame):
    raise KeyboardInterrupt

signal.signal(signal.SIGTERM, stop)
if hasattr(signal, "SIGHUP"): signal.signal(signal.SIGHUP, stop)

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description='Start TripMind on localhost; Ctrl+C stops both services.')
parser.add_argument('--preview', action='store_true', help='Serve the production build (same port/storage as development).')
parser.add_argument('--sample', action='store_true', help='Use offline London sample mode without credentials.')
args = parser.parse_args()
python = ROOT/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
npm = shutil.which('npm')
if not python.exists() or not npm or not (ROOT/'frontend/node_modules').is_dir():
    sys.exit('Dependencies missing. Run bash scripts/setup.sh first (see docs/Delivery.md).')
if args.preview and not (ROOT/'frontend/dist/index.html').exists():
    sys.exit('Production build missing. Run npm run build in frontend first.')
for port in (5001,5173):
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: sock.bind(('127.0.0.1',port))
        except OSError: sys.exit(f'Port {port} is already in use. Stop the existing TripMind terminal first. No process was killed.')
env = os.environ.copy()
if args.sample: env['TRIP_PROVIDER']='sample'
commands = [([str(python),'-m','flask','--app','backend.app','run','--host','127.0.0.1','--port','5001'],ROOT),
            ([npm,'run','preview' if args.preview else 'dev','--','--port','5173','--strictPort'],ROOT/'frontend')]
children=[]
try:
    for command,cwd in commands:
        children.append(subprocess.Popen(command,cwd=cwd,env=env,start_new_session=(os.name!='nt')))
    print('TripMind: http://127.0.0.1:5173 — Ctrl+C stops both services.',flush=True)
    while all(child.poll() is None for child in children): time.sleep(.5)
    sys.exit(next((p.returncode for p in children if p.returncode),1))
except KeyboardInterrupt:
    pass
finally:
    import signal
    for child in children:
        if child.poll() is None:
            if os.name!='nt': os.killpg(child.pid,signal.SIGTERM)
            else: child.terminate()
    for child in children:
        try: child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if os.name!='nt': os.killpg(child.pid,signal.SIGKILL)
            else: child.kill()
