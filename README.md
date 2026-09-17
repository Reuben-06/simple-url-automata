# URL Automata Project — DFA & NFA for Web URL Validation

## 1. Project title
Validation of a Defined Subset of Web URLs Using DFA and NFA

## 2. Objective
To demonstrate, for a real-world validation problem, how a DFA and an NFA
can both be designed to recognize the **same formal language**, to verify
that they actually do recognize the same language, and to critically
compare their suitability for this problem. The URL validator is the
*application*; the finite-automata design, implementation, testing, and
comparison are the academic core.

## 3. Problem definition
Decide, syntactically, whether a given string is a well-formed URL under
a **deliberately restricted, explicitly frozen subset** of real-world web
URL syntax (see `TECHNICAL_PACKAGE.md` §4 for the full frozen
specification). This is *syntactic* validation only — it never checks
whether a domain exists, resolves, or is safe.

## 4. Defined language (summary)
```
scheme://domain(.label)*.tld(/path-segment)*/?
```
- `scheme` = `http` or `https`, lowercase only
- `domain` labels: `[A-Za-z0-9]+(-[A-Za-z0-9]+)*` (case-insensitive, no
  leading/trailing/consecutive hyphens)
- `tld` (final label): one of `{com, org, net, edu, ai}`, **lowercase
  only**, and the domain must have at least 2 components
  (`label.tld`, not a bare TLD)
- `path` segments: `[A-Za-z0-9_-]+`, no empty segments (`//` rejected)
- ASCII-only. No ports, query strings, fragments, userinfo, IP
  addresses, or percent-encoding.

Full grammar, alphabet, and rationale: see `TECHNICAL_PACKAGE.md`.

## 5. Files
```
URL_Automata_Project/
├── automata.py       # single authoritative DFA + NFA + regex implementation
├── tests.py           # comprehensive test suite (valid/invalid/boundary/unicode)
├── equivalence.py      # subset construction + exhaustive product-state verification
├── gen_tables.py       # generates transition tables & diagrams FROM automata.py
├── demo.py             # interactive CLI + trace mode
├── README.md
├── TECHNICAL_PACKAGE.md
├── diagrams/
│   ├── dfa.mmd
│   └── nfa.mmd
└── output/
    ├── dfa_transition_table.txt
    ├── nfa_transition_table.txt
    ├── test_output.txt
    └── equivalence_output.txt
```

## 6. Installation requirements
None beyond a standard Python 3 interpreter (uses only the standard
library: `re`, `collections`, `itertools`).

## 7. How to run the demo
```bash
python demo.py
python demo.py --trace     # also print DFA/NFA state-by-state traces
```

## Visualization

Run:

    python demo.py

From the menu:

    4. Visualize DFA Path
    5. Visualize NFA Path

The selected URL is converted into a Mermaid state diagram and
automatically opened in the default web browser.

The generated visualization files are stored in:

    diagrams/dfa_path.mmd
    diagrams/nfa_path.mmd

## 8. How to test a single URL
Interactively via `demo.py`, or programmatically:
```python
from automata import validate_dfa, validate_nfa
validate_dfa("https://www.google.com")   # True
validate_nfa("https://www.google.com")   # True
```

## 9. How to run the complete test suite
```bash
python tests.py
```
Writes `output/test_output.txt` and exits non-zero on any failure.

## 10. How to generate transition tables / diagrams
```bash
python gen_tables.py
```
Regenerates `output/dfa_transition_table.txt`,
`output/nfa_transition_table.txt`, `diagrams/dfa.mmd`, `diagrams/nfa.mmd`
directly from the current `automata.py` — never hand-edit these outputs.

## 11. How to run equivalence verification
```bash
python equivalence.py
```
Performs NFA→DFA' subset construction and an exhaustive
product-state (DFA state × NFA active-set) BFS, reporting any mismatch.
Writes `output/equivalence_output.txt`.

## 12. How to use trace mode
Pass `--trace` to `demo.py`. Every URL entered will additionally print:
- the DFA's single-state, step-by-step trace, and
- the NFA's active-*set* history, visibly branching into multiple
  simultaneously-active states during TLD matching.

## 13. Expected output (example)
```
URL: https://www.google.com

DFA: ACCEPT
NFA: ACCEPT
Agreement: YES
```
```
URL: https://example.com//test

DFA: REJECT
NFA: REJECT
Agreement: YES
```

## 14. Limitations
This project validates only the explicitly frozen subset of URL syntax.
It deliberately excludes ports, query strings, fragments, userinfo,
IPv4/IPv6 literals, percent-encoding, and internationalized domain names.
See `TECHNICAL_PACKAGE.md` §8 for the full, documented list and the
reasoning behind each exclusion.
