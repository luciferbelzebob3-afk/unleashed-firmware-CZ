#!/usr/bin/env python3
"""Heuristic inventory of likely English strings in firmware source; never edits source files."""
import csv, re, sys
from pathlib import Path

EXTS = {".c", ".h", ".cpp", ".hpp", ".cc", ".hh", ".json", ".txt", ".md", ".yaml", ".yml", ".js", ".ts", ".tsx", ".py", ".xml", ".html", ".css"}
SKIP = {".git", "build", "dist", "node_modules", "__pycache__", ".venv"}
QUOTED = re.compile(r'"((?:\\.|[^"\\]){2,})"|\'((?:\\.|[^\'\\]){2,})\'')
WORDS = re.compile(r"\b(?:the|and|or|please|press|hold|select|back|next|cancel|save|delete|open|close|settings|error|warning|failed|success|loading|connected|disconnected|unknown|none|yes|no|on|off|start|stop|name|value|read|write|scan|device|file|folder|battery|signal|frequency|protocol|channel|retry|update|install|remove|enable|disable|confirm|enter|choose|available|not|found|invalid|waiting|ready|done|information|about|menu|search|clear|reset|format|storage|memory|application|version|password|username|network|duration|timeout|temperature|voltage|current|power|minutes|seconds|hours|days|true|false)\b", re.I)

def main():
    rows = []
    for root in sys.argv[1:]:
        base = Path(root)
        if not base.exists(): continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in EXTS or any(x in SKIP for x in p.parts): continue
            try: lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError: continue
            for n, line in enumerate(lines, 1):
                for m in QUOTED.finditer(line):
                    value = (m.group(1) if m.group(1) is not None else m.group(2)).strip()
                    if len(value) < 3 or not WORDS.search(value): continue
                    if value.startswith(("http://", "https://", "application/", "image/")): continue
                    if value.count("%") >= 3 or ("{" in value and "}" in value and not re.search(r"\s", value)): continue
                    rows.append((str(p), n, value.replace("\n", " ")[:500], line.strip()[:700]))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    with open("report.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["file", "line", "candidate_string", "source_line"]); w.writerows(rows)
    print(f"Roots={','.join(sys.argv[1:])}; candidates={len(rows)}")

if __name__ == "__main__": main()
