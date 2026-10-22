#!/usr/bin/env python3
"""Release consistency check and changelog extraction.

Usage:
    python3 tools/release_notes.py v0.3.0            # check, print the notes
    python3 tools/release_notes.py v0.3.0 -o notes.md

Checks that CHANGELOG.md has a "## [X.Y.Z]" section for the tag and that
.claude-plugin/plugin.json and marketplace.json carry the same version, then writes
that changelog section (without its heading) as the release notes. Exit 1 with a
clear message when anything is inconsistent. Standard library only.
"""
import json, re, sys

ROOT = __file__.rsplit("/tools/", 1)[0] if "/tools/" in __file__ else "."


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(2)
    tag = args[0]
    version = tag[1:] if tag.startswith("v") else tag
    if not re.fullmatch(r"\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?", version):
        sys.exit(f"tag '{tag}' is not vX.Y.Z")
    problems = []
    for f in ("plugin.json", "marketplace.json"):
        path = f"{ROOT}/.claude-plugin/{f}"
        d = json.load(open(path, encoding="utf-8"))
        v = d.get("version") or d.get("metadata", {}).get("version")
        if v != version:
            problems.append(f"{path} has version {v!r}, tag says {version!r}")
        if f == "marketplace.json":
            for p in d.get("plugins", []):
                if p.get("version") != version:
                    problems.append(f"{path} plugin '{p.get('name')}' has version {p.get('version')!r}")
    log = open(f"{ROOT}/CHANGELOG.md", encoding="utf-8").read()
    m = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)", log, flags=re.M | re.S)
    if not m:
        problems.append(f"CHANGELOG.md has no '## [{version}]' section (move the Unreleased entries under one)")
    if problems:
        sys.exit("release check failed:\n  " + "\n  ".join(problems))
    notes = m.group(1).strip() + "\n"
    if "-o" in args:
        open(args[args.index("-o") + 1], "w", encoding="utf-8").write(notes)
    else:
        print(notes, end="")
    print(f"release check ok for {tag}", file=sys.stderr)


if __name__ == "__main__":
    main()
