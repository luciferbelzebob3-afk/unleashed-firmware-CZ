#!/usr/bin/env python3
"""Conservative AST-backed UI string flow audit. Report-only; never edits firmware."""
import argparse,json,re,sys
from pathlib import Path
from collections import defaultdict
try:
 from tree_sitter import Language,Parser
 import tree_sitter_c,tree_sitter_cpp
except ImportError:
 sys.exit("Install: pip install tree-sitter tree-sitter-c tree-sitter-cpp")
EXTS={".c",".h",".cc",".cpp",".hpp"}; SKIP={".git","build","dist","vendor","submodules"}
SINKS={"canvas_draw_str","canvas_draw_str_aligned","canvas_draw_str_with_max_width","submenu_set_header","submenu_add_item","dialog_ex_set_header","dialog_ex_set_text","dialog_ex_set_left_button_text","dialog_ex_set_right_button_text","dialog_message_set_header","dialog_message_set_text","text_input_set_header_text","popup_set_header","popup_set_text","widget_add_string_element","widget_add_text_box_element","widget_add_button_element","button_menu_add_item","button_menu_set_header","variable_item_set_current_value_text","text_box_set_text","byte_input_set_header_text","header_set_text","string_set","furi_string_set"}
STR={"string_literal","concatenated_string"}; HUMAN=re.compile(r"[A-Za-z]{2,}(?:[ '-][A-Za-z]{2,}){0,8}")
def walk(n):
 stack=[n]
 while stack:
  current=stack.pop()
  yield current
  stack.extend(reversed(current.children))
def textof(n,d): return d[n.start_byte:n.end_byte].decode("utf-8","replace")
def identifiers(n,d): return [textof(x,d) for x in walk(n) if x.type=="identifier"]
def fname(n,d):
 x=n.child_by_field_name("declarator"); z=identifiers(x,d) if x else []
 return z[-1] if z else "<unknown>"
def arguments(n):
 x=n.child_by_field_name("arguments"); return list(x.named_children) if x else []
def main():
 p=argparse.ArgumentParser(); p.add_argument("--root",default="."); p.add_argument("--out",default="reports/ui-dataflow-audit.md"); p.add_argument("--json",default="reports/ui-dataflow-audit.json"); a=p.parse_args()
 root=Path(a.root).resolve(); files=[]; funcs=defaultdict(list); literals=[]; constants={}
 for file in root.rglob("*"):
  if not file.is_file() or file.suffix.lower() not in EXTS or any(x in SKIP for x in file.parts): continue
  try: data=file.read_bytes()
  except OSError: continue
  lang=tree_sitter_c.language() if file.suffix.lower() in {".c",".h"} else tree_sitter_cpp.language()
  tree=Parser(Language(lang)).parse(data); rel=str(file.relative_to(root)); files.append((rel,data,tree))
  for n in walk(tree.root_node):
   if n.type=="function_definition":
    dec=n.child_by_field_name("declarator"); params=[]
    if dec:
     for q in walk(dec):
      if q.type=="parameter_declaration":
       names=identifiers(q,data)
       if names: params.append(names[-1])
    funcs[fname(n,data)].append({"file":rel,"data":data,"params":params,"body":n.child_by_field_name("body")})
   elif n.type in STR: literals.append({"file":rel,"line":n.start_point.row+1,"literal":textof(n,data)})
  for n in walk(tree.root_node):
   if n.type=="declaration":
    s=textof(n,data)
    if re.search(r"\b(?:const|static)\b",s):
     m=re.search(r'([A-Za-z_]\w*)\s*=\s*("(?:\\.|[^"\\])*")',s)
     if m: constants[m.group(1)]=m.group(2)
 # Infer which function parameters flow into GUI sinks, then propagate summaries through wrapper calls.
 summary=defaultdict(set); edges=defaultdict(list)
 for name,defs in funcs.items():
  for f in defs:
   if f["body"] is None: continue
   for n in walk(f["body"]):
    if n.type!="call_expression": continue
    x=n.child_by_field_name("function"); callee=textof(x,f["data"]).split("::")[-1] if x else ""; args=arguments(n)
    if callee in SINKS:
     for i,arg in enumerate(args):
      for j,param in enumerate(f["params"]):
       if re.search(r"\b"+re.escape(param)+r"\b",textof(arg,f["data"])): summary[name].add(j)
    if callee: edges[name].append((callee,n,f))
 changed=True
 while changed:
  changed=False
  for caller,es in edges.items():
   for callee,n,f in es:
    aa=arguments(n)
    for i in summary.get(callee,set()):
     if i>=len(aa): continue
     val=textof(aa[i],f["data"])
     for j,param in enumerate(f["params"]):
      if re.search(r"\b"+re.escape(param)+r"\b",val) and j not in summary[caller]: summary[caller].add(j); changed=True
 rows=[]; reached=set()
 for rel,data,tree in files:
  for fn in walk(tree.root_node):
   if fn.type!="function_definition": continue
   name=fname(fn,data); body=fn.child_by_field_name("body")
   if body is None: continue
   env=dict(constants); seq=sorted((x for x in walk(body) if x.type in {"init_declarator","assignment_expression","call_expression"}),key=lambda x:x.start_byte)
   for n in seq:
    if n.type in {"init_declarator","assignment_expression"}:
     left=n.child_by_field_name("declarator") or n.child_by_field_name("left"); right=n.child_by_field_name("value") or n.child_by_field_name("right")
     if left is not None and right is not None:
      ids=identifiers(left,data)
      if ids:
       key=ids[-1]; val=textof(right,data)
       if right.type in STR: env[key]=val
       elif val in env: env[key]=env[val]
       elif re.fullmatch(r"[A-Za-z_]\w*",val): env.pop(key,None)
     continue
    x=n.child_by_field_name("function"); callee=textof(x,data).split("::")[-1] if x else ""; aa=arguments(n)
    if callee in SINKS:
     for i,arg in enumerate(aa):
      vals=[textof(arg,data)] if arg.type in STR else []
      vals += [env[z] for z in identifiers(arg,data) if z in env]
      for val in dict.fromkeys(vals):
       rows.append({"category":"UI_DATAFLOW_SINK","confidence":"high","file":rel,"line":n.start_point.row+1,"function":name,"sink":callee,"argument":i,"literal":val,"evidence":"AST argument reaches known GUI sink via literal or simple alias","review":"Verify argument semantics and runtime path."})
       reached.add((rel,n.start_point.row+1,val))
    for i in summary.get(callee,set()):
     if i>=len(aa): continue
     arg=aa[i]; vals=[textof(arg,data)] if arg.type in STR else []
     vals += [env[z] for z in identifiers(arg,data) if z in env]
     for val in dict.fromkeys(vals):
      rows.append({"category":"UI_INTERPROCEDURAL_FLOW","confidence":"medium","file":rel,"line":n.start_point.row+1,"function":name,"sink":callee,"argument":i,"literal":val,"evidence":"Argument flows into wrapper parameter summarized as reaching GUI sink","review":"Inspect wrapper and conditional path."})
 for lit in literals:
  val=lit["literal"][1:-1]
  if HUMAN.search(val) and (lit["file"],lit["line"],lit["literal"]) not in reached:
   rows.append({"category":"UNRESOLVED_STRING_LITERAL","confidence":"low","file":lit["file"],"line":lit["line"],"function":"?","sink":"","argument":-1,"literal":lit["literal"],"evidence":"AST literal without recognized GUI data-flow path","review":"Check macros, resources, pointers, structs, callbacks, custom wrappers and dynamic strings."})
 unique={}
 for r in rows: unique[tuple(r.get(k) for k in ("category","file","line","function","sink","argument","literal"))]=r
 rows=sorted(unique.values(),key=lambda r:(r["category"],r["file"],r["line"])); counts=defaultdict(int)
 for r in rows: counts[r["category"]]+=1
 md=["# AST/data-flow audit UI retezcu","","Konzervativni staticka analyza; nenahrazuje plnou whole-program ani path-sensitive analyzu.","","## Souhrn","","| Kategorie | Pocet |","|---|---:|"]+[f"| {k} | {v} |" for k,v in sorted(counts.items())]
 md += ["","## Nalezy","","| Kategorie | Jistota | Soubor:radek | Funkce | Sink | Argument | Retezec | Dukaz | Dalsi kontrola |","|---|---|---|---|---|---:|---|---|---|"]
 for r in rows:
  vals=[r.get(k,"") for k in ("category","confidence","file","function","sink","argument","literal","evidence","review")]; vals[2]=f'{vals[2]}:{r["line"]}'
  md.append("| "+" | ".join(str(v).replace("|","\\|").replace("\n","\\\\n") for v in vals)+" |")
 md += ["","## Limity","",
 "- Tree-sitter AST parsovani C/C++ a sledovani jednoduchych lokalnich prirazeni/aliasu.",
 "- Interproceduralni shrnuti parametru wrapper funkci propagovana do pevneho bodu.",
 "- Plne aliasy pointeru/heapu, vetveni a slucovani cest, makra po expanzi, pole/struktury, callbacky, RTOS tasky, resource tabulky a vsechny vlastni GUI API nejsou plne modelovany.",
 "- UI_DATAFLOW_SINK je dukaz toku do rozpoznaneho API, ne absolutni dukaz viditelnosti za behu.",
 "- Report-only: zadne preklady ani upravy firmwaru.",""]
 Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text("\n".join(md),encoding="utf-8")
 Path(a.json).parent.mkdir(parents=True,exist_ok=True); Path(a.json).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
 print(f"files={len(files)} functions={sum(map(len,funcs.values()))} literals={len(literals)} findings={len(rows)}")
 print("categories="+json.dumps(dict(counts),ensure_ascii=False,sort_keys=True))
if __name__=="__main__": main()
