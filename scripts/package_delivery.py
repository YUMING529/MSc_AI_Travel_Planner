"""Build a source-only handoff from an explicit allowlist; never include local credentials."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
root=Path(__file__).resolve().parents[1]
files=[root/p for p in ['README.md','PROJECT_CONTEXT.md','.gitignore','Start-TripMind.command',
    'backend/.env.example','backend/requirements.txt','backend/requirements-lock.txt','backend/README.md',
    'frontend/package.json','frontend/package-lock.json','frontend/index.html','frontend/vite.config.js',
    'frontend/README.md','docs/Delivery.md','docs/Testing-2026-10-21.md','docs/Acceptance-2026-10-22.md']]
for pattern in ['backend/*.py','backend/*.json','backend/tests/*.py','frontend/src/**/*',
                'frontend/public/**/*','frontend/tests/*.js','scripts/*.py','scripts/*.sh']:
    files.extend(p for p in root.glob(pattern) if p.is_file())
dest=root/'dist/TripMind-source.zip'
dest.parent.mkdir(exist_ok=True)
with ZipFile(dest,'w',ZIP_DEFLATED) as bundle:
    for p in sorted(set(files)):
        if p.is_symlink() or not p.is_file(): continue
        if p.name=='.env' or '__pycache__' in p.parts: continue
        bundle.write(p,Path('TripMind')/p.relative_to(root))
print(dest)
