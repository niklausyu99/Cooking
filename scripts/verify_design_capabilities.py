"""Verify pinned project skills and native Codex role conversions; no network required."""
from pathlib import Path
import hashlib
import json
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / 'design/capabilities/capabilities.lock.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    lock = json.loads(LOCK.read_text())
    failures = []
    config = tomllib.loads((ROOT / '.codex/config.toml').read_text())
    for skill in lock['skills']:
        folder = ROOT / skill['path']
        actual = {str(p.relative_to(folder)): digest(p)
                  for p in folder.rglob('*') if p.is_file()}
        if actual != skill['files']:
            failures.append(f"{skill['name']}: file tree or checksums differ")
        content = (folder / 'SKILL.md').read_text()
        match = re.search(r'^name:\s*[\"\']?([^\n\"\']+)', content, re.M)
        if not match or match.group(1).strip() != skill['name']:
            failures.append(f"{skill['name']}: metadata name mismatch")
    for agent in lock['agents']:
        target = ROOT / agent['path']
        source = ROOT / agent['source_copy']
        if digest(target) != agent['sha256'] or digest(source) != agent['source_sha256']:
            failures.append(f"{agent['name']}: conversion/source checksum mismatch")
        role = tomllib.loads(target.read_text())
        body = source.read_text().split('---', 2)[2].lstrip('\n')
        if role != {'developer_instructions': body}:
            failures.append(f"{agent['name']}: body not preserved or unsupported metadata leaked")
        registered = config.get('agents', {}).get(agent['name'], {})
        path = registered.get('config_file', '')
        if not path or (ROOT / '.codex' / path).resolve() != target.resolve():
            failures.append(f"{agent['name']}: registry mismatch")
    expected = {a['name'] for a in lock['agents']}
    if set(config.get('agents', {})) != expected:
        failures.append('Unexpected or missing agent registration')
    huashu = ROOT / '.agents/skills/huashu-design'
    for name in ['references', 'assets', 'scripts', 'demos']:
        if not (huashu / name).is_dir():
            failures.append(f'huashu-design/{name} missing')
    if failures:
        raise SystemExit('\n'.join(failures))
    print(f"PASS: {len(lock['skills'])} complete skill trees; "
          f"{len(lock['agents'])} native Codex role conversions; "
          "all checksums, metadata, registration paths, and full upstream agent bodies verified.")
    print('This verifies installation integrity, not live host discovery or subagent execution.')


if __name__ == '__main__':
    main()
