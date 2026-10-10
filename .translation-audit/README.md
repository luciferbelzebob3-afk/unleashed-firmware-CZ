# AST agent pro audit UI retezcu a toku dat

Analyzator pouziva Tree-sitter AST pro C/C++, jednoduche sledovani hodnot promennych a interproceduralni shrnuti parametru wrapper funkci. Je report-only: nemeni zdrojaky, firmware ani preklady.

## Spusteni

```bash
python -m pip install tree-sitter tree-sitter-c tree-sitter-cpp
python .translation-audit/classify_ui_strings.py --root . --out reports/ui-dataflow-audit.md --json reports/ui-dataflow-audit.json
```

## Kategorie nalezu

- `UI_DATAFLOW_SINK`: retezec nebo alias se dostal do rozpoznaneho GUI API.
- `UI_INTERPROCEDURAL_FLOW`: argument tece do parametru wrapper funkce, jehoz parametricky souhrn dosahuje GUI sinku.
- `UNRESOLVED_STRING_LITERAL`: citelny literal bez nalezene cesty k rozpoznanemu GUI API; vyzaduje dohledani.

## Co je sledovano

AST volani GUI API, prime retezce, jednoduche lokalni prirazeni a aliasy, nektere souborove konstanty a propagace parametru wrapperu do pevneho bodu. Report obsahuje soubor, radek, funkci, sink, index argumentu, retezec, dukaz a doporucenou rucni kontrolu.

## Limity

Tohle jeste neni plnohodnotna formalni whole-program data-flow analyza. Neprovede uplnou kompilacni expanzi maker ani spolehlive nemodeluje pointer/heap aliasy, pole a struktury, vetveni a slucovani cest, callbacky, RTOS tasky, dynamicky generovane retezce, resource tabulky a vsechny projektove GUI wrappery. Volani sinku je silny staticky dukaz, ale nemusi znamenat, ze se text za behu skutecne vykresli. Nezname retezce se nesmeji automaticky prekladat bez potvrzeni toku do UI.

CI overi syntaxi Python skriptu, spusti analyzu a ulozi Markdown/JSON artefakty na 14 dni. Nez se vysledky pouziji k prekladu, zkontroluj stav workflow a report.
