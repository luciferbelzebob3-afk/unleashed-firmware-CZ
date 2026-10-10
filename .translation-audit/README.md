# Agent pro audit textu uzivatelskeho rozhrani

Nastroj tridi retezce v C/C++ souborech firmwaru na pravdepodobne UI texty, technicke retezce a nalezy vyzadujici rucni kontrolu. Je pouze analyzator: firmware neupravuje a nic automaticky nepreklada.

## Spusteni

Z korenove slozky repozitare:

```bash
python3 .translation-audit/classify_ui_strings.py --root . --out reports/ui-string-audit.md --json reports/ui-string-audit.json
```

Pouziva pouze standardni knihovnu Pythonu 3.

## Kategorie

- `UI_LIKELY`: rozpoznane GUI API na stejnem radku; stale je potreba overit tok dat.
- `UI_REVIEW`: v blizkem kontextu je GUI API.
- `POSSIBLE_UI_TEXT`: lidsky citelny text bez primeho dukazu vykresleni.
- `TECHNICAL_REVIEW`: identifikator, cesta, URL nebo formatovaci token.
- `TECHNICAL_OR_LOG`: text pobliz logovaciho nebo technickeho API.
- `COMMENT_OR_DOC`, `BUILD_OR_MACRO`: komentare nebo preprocesor.
- `UNCLASSIFIED`: nedostatek dukazu.

## Dulezita omezeni

Heuristiky nejsou dukazem, ze se retezec skutecne zobrazuje. Neprime vykreslovani, prekladove tabulky a texty sestavovane za behu mohou vyzadovat rucni dohledani. Zachovavej placeholdery jako `%s` a `%d`, escape sekvence, protokoly, nazvy souboru, ID a API. Pred sloucenim zmen prover diff a sestaveni firmwaru.
