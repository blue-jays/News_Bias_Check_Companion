#!/usr/bin/env python3
"""
Repo scaffolder for MLOps-style projects.
Reads a YAML manifest (structure.yml) and creates folders/files.

Usage:
  pip install pyyaml
  python scaffold.py
  python scaffold.py --dry-run       # preview actions
  python scaffold.py --force         # overwrite existing files
"""
from __future__ import annotations
import argparse
import sys, re
from pathlib import Path
import yaml

# --- Helper: brace expansion like {raw,processed} ---
def brace_expand(pattern: str) -> list[str]:
    parts = [pattern]
    rgx = re.compile(r"\{([^{}]+)\}")
    out = []
    while parts:
        s = parts.pop()
        m = rgx.search(s)
        if not m:
            out.append(s)
            continue
        opts = m.group(1).split(",")
        for opt in opts:
            parts.append(s[:m.start()] + opt + s[m.end():])
    return sorted(set(out))

# --- Core creation helpers ---
def ensure_dir(path: Path, dry: bool, logs: list[str]):
    if path.exists():
        logs.append(f"= exists  📁 {path}")
        return
    if not dry:
        path.mkdir(parents=True, exist_ok=True)
    logs.append(f"+ created 📁 {path}")

def write_file(path: Path, content: str | None, force: bool, dry: bool, logs: list[str]):
    if path.exists() and not force:
        logs.append(f"= exists  📄 {path}")
        return
    if not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content or "")
    logs.append(f"+ created 📄 {path}")

def load_manifest(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "entries" not in data:
        raise ValueError("Manifest must be a mapping with an 'entries' list.")
    return data

# --- Main logic ---
def main():
    ap = argparse.ArgumentParser(description="Scaffold repo from YAML manifest.")
    ap.add_argument("--manifest", "-m", default="structure.yml")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    manifest_path = Path.cwd().parent / args.manifest
    if not manifest_path.exists():
        sys.exit(f"❌ Manifest not found: {manifest_path}")

    data = load_manifest(manifest_path)
    # 🔹 Start creating folders one directory above current working directory
    target_root = data.get("project_root", ".")
    if target_root == ".":
        base_dir = Path.cwd().parent        # one directory up
    else:
        base_dir = Path.cwd().parent / target_root


    logs: list[str] = []
    for entry in data["entries"]:
        if not isinstance(entry, dict):
            raise ValueError(f"Each entry must be a dict, got: {entry}")
        if "dir" in entry:
            for p in brace_expand(entry["dir"]):
                ensure_dir(base_dir / p, args.dry_run, logs)
        elif "file" in entry:
            content = entry.get("content")
            mode = entry.get("mode")
            for p in brace_expand(entry["file"]):
                fpath = base_dir / p
                write_file(fpath, content, args.force, args.dry_run, logs)
                if mode and not args.dry_run:
                    try:
                        fpath.chmod(int(mode, 8))
                    except Exception as e:
                        logs.append(f"! chmod failed for {fpath}: {e}")
        else:
            raise ValueError(f"Entry must have 'dir' or 'file': {entry}")

    print("\n".join(logs))

if __name__ == "__main__":
    main()
