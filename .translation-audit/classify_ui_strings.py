#!/usr/bin/env python3
"""Heuristic audit of display-facing strings in Flipper Zero C/C++ sources.
Run from repository root:
 python3 .translation-audit/classify_ui_strings.py --root . --out reports/ui-string-audit.md --json reports/ui-string-audit.json
This script only reports findings; it never edits firmware or translations.
"""
import argparse, json, re
from pathlib import Path

EXTS = {".c", ".h", ".cc", ".cpp", ".hpp"}
SKIP_DIRS = {".git", "build", "dist", "vendor"}
UI_CALLS = re.compile(r"\b(?:submenu_add_item|submenu_set_header|dialog_ex_set_(?:header|text|left_button_text|right_button_text)|dialog_message_set_(?:header|text)|text_input_set_header_text|popup_set_header|popup_set_text|widget_add_(?:string_element|text_box_element|button_element)|canvas_draw_str(?:_aligned)?|button_menu_add_item|button_menu_set_header|variable_item_list_add|variable_item_set_current_value_text|text_box_set_text|byte_input_set_header_text)\b")
TECH_CALLS = re.compile(r"\b(?:FURI_LOG_[A-Z]+|FURI_LOG|furi_check|furi_crash|storage_common_(?:open|read|write))\b")
STRINGS = re.compile(r'"(?:\\.|[^"\\])*"')
HUMAN = re.compile(r"\b(?:read|save|load|delete|cancel|exit|settings|error|success|start|stop|back|next|yes|no|on|off|please|wait|failed|done|uloz|smaz|zrus|nastav|chyba|hotovo)\b", re.I)
TECH = re.compile(r"(?:https?://|www\.|\.c\b|\.h\b|/|^[A-Z][A-Z0-9_]{2,}$|^[a-z][a-z0-9_]{2,}$)")

def classify(lines, i, literal):
    line = lines[i]
    if re.match(r"^\s*(//|/\*|\*|\*/)", line):
        return "COMMENT_OR_DOC", "low", "comment line"
    if re.match(r"^\s*#", line):
        return "BUILD_OR_MACRO", "low", "preprocessor directive"
    context = "\n".join(lines[max(0, i-3):min(len(lines), i+4)])
    if TECH_CALLS.search(context) and not UI_CALLS.search(context):
        return "TECHNICAL_OR_LOG", "medium", "near logging/assertion/storage API"
    if UI_CALLS.search(line):
        return "UI_LIKELY", "high", "known GUI API on same line"
    if UI_CALLS.search(context):
        return "UI_REVIEW", "medium", "known GUI API nearby"
    if TECH.search(literal):
        return "TECHNICAL_REVIEW", "medium", "resembles identifier/path/URL/format token"
    if HUMAN.search(literal):
        return "POSSIBLE_UI_TEXT", "low", "human-language phrase without direct GUI evidence"
    return "UNCLASSIFIED", "low", "insufficient evidence"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="ui-string-audit.md")
    ap.add_argument("--json", default="")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    rows = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in EXTS:
            continue
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS or part == ".git" for part in rel.parts):
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        in_block = False
        for i, line in enumerate(lines):
            scan = line
            if in_block:
                if "*/" in scan:
                    scan = scan.split("*/", 1)[1]
                    in_block = False
                else:
                    continue
            if "/*" in scan:
                before, after = scan.split("/*", 1)
                if "*/" in after:
                    scan = before + after.split("*/", 1)[1]
                else:
                    scan, in_block = before, True
            if re.match(r"^\s*(//|#)", line):
                continue
            for m in STRINGS.finditer(scan):
                literal = m.group(0)[1:-1]
                if not literal.strip():
                    continue
                category, confidence, evidence = classify(lines, i, literal)
                rows.append({"category": category, "confidence": confidence,
                             "file": str(rel), "line": i+1, "literal": literal,
                             "evidence": evidence})
    order = {"UI_LIKELY":0, "UI_REVIEW":1, "POSSIBLE_UI_TEXT":2, "UNCLASSIFIED":3,
             "TECHNICAL_REVIEW":4, "TECHNICAL_OR_LOG":5, "COMMENT_OR_DOC":6, "BUILD_OR_MACRO":7}
    rows.sort(key=lambda r: (order.get(r["category"], 9), r["file"], r["line"]))
    counts = {}
    for r in rows:
        counts[r["category"]] = counts.get(r["category"], 0) + 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    md = ["# Audit retezcu firmwaru Flipper Zero", "",
          "> Heuristicky report, nikoli definitivni verdikt. Pred prekladem overit skutecne vykresleni.", "",
          "## Souhrn", "", "| Kategorie | Pocet |", "|---|---:|"]
    md += [f"| {k} | {v} |" for k, v in sorted(counts.items())]
    md += ["", "## Nalezy", "", "| Kategorie | Jistota | Soubor:radek | Retezec | Dukaz |",
           "|---|---|---|---|---|"]
    for r in rows:
        esc = lambda s: str(s).replace("|", "\\|").replace("\n", "\\\\n").replace("`", "\\`")
        md.append(f"| {r['category']} | {r['confidence']} | {esc(r['file'])}:{r['line']} | {esc(r['literal'])} | {esc(r['evidence'])} |")
    md += ["", "## Pravidla", "",
           "- UI_LIKELY: silny signal GUI API; presto overit vykresleni.",
           "- UI_REVIEW / POSSIBLE_UI_TEXT: rucne dohledat volani a tok dat.",
           "- TECHNICAL_REVIEW / TECHNICAL_OR_LOG: neprekladat automaticky.",
           "- UNCLASSIFIED: vyzaduje kontrolu kontextu.",
           "- Skript nic neupravuje a nic automaticky nepreklada.", ""]
    out.write_text("\n".join(md), encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Zpracovano retezcu:", len(rows))
    print("Kategorie:", counts)
    print("Report:", out)

if __name__ == "__main__":
    main()
