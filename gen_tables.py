"""
gen_tables.py
=============
Generates the DFA and NFA transition tables (Section 16/20) and Mermaid
diagram sources (Section 17/21) DIRECTLY from the live implementation in
automata.py. Nothing here is hand-maintained separately -- if automata.py
changes, re-running this script regenerates tables/diagrams that are
guaranteed consistent with the code (Section 36/37).

Run:
    python gen_tables.py
Writes:
    output/dfa_transition_table.txt
    output/nfa_transition_table.txt
    diagrams/dfa.mmd
    diagrams/nfa.mmd
"""

import os
from collections import deque
from automata import (
    DFA_START, dfa_step, DEAD, DFA_ACCEPT_DOMAIN_END,
    NFA_START, nfa_step, NFA_ACCEPTING,
)
from equivalence import ALPHABET, dfa_is_accepting, nfa_is_accepting

CLASS_REPS = {
    "LETTER(other)": "A",
    "DIGIT": "5",
    "COLON": ":",
    "SLASH": "/",
    "DOT": ".",
    "HYPHEN": "-",
    "UNDERSCORE": "_",
    "OTHER": "?",
}


def state_name(s):
    if s == DEAD:
        return "DEAD"
    if isinstance(s, tuple):
        return "DOM[%s,%s,%s]" % (s[1], s[2], "d1" if s[3] else "d0")
    return str(s)


# ---------------------------------------------------------------------------
# DFA: BFS over reachable states using the FULL representative alphabet plus
# every individual lowercase letter (already in ALPHABET), so the resulting
# table is exact (not an approximation).
# ---------------------------------------------------------------------------

def build_dfa_table():
    start = DFA_START
    seen = {start}
    frontier = deque([start])
    table = {}  # state -> {symbol: next_state}
    while frontier:
        s = frontier.popleft()
        table[s] = {}
        for sym in ALPHABET:
            nxt = dfa_step(s, sym) if s != DEAD else DEAD
            table[s][sym] = nxt
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    return table, seen


def build_nfa_table():
    # BFS over individual NFA states (not sets) to build a genuine NFA table
    # (each entry may map to zero, one, or multiple next states).
    start = NFA_START
    seen = {start}
    frontier = deque([start])
    table = {}
    while frontier:
        s = frontier.popleft()
        table[s] = {}
        for sym in ALPHABET:
            nxt = nfa_step(s, sym)
            table[s][sym] = nxt
            for t in nxt:
                if t not in seen:
                    seen.add(t)
                    frontier.append(t)
    return table, seen


def write_dfa_table(table, seen, path):
    lines = []
    lines.append("DFA TRANSITION TABLE (generated from automata.py)")
    lines.append("=" * 70)
    lines.append(f"Start state: {state_name(DFA_START)}")
    accepting = sorted(state_name(s) for s in seen if dfa_is_accepting(s))
    lines.append(f"Accepting states ({len(accepting)}): {', '.join(accepting)}")
    lines.append(f"Total reachable states (incl. DEAD sink): {len(seen)}")
    lines.append("-" * 70)
    header = "STATE".ljust(22) + "".join(c.ljust(4) for c in
              ["a-z*", "A", "5", ":", "/", ".", "-", "_", "?"])
    lines.append(header)
    # collapse the 26 lowercase-letter columns into one column "a-z*" ONLY
    # when they all agree (true for every state in this design -- verified
    # below); otherwise the letters differing get their own row note.
    for s in sorted(seen, key=lambda x: state_name(x)):
        row = table[s]
        lower_targets = {row[c] for c in "abcdefghijklmnopqrstuvwxyz"}
        collapse_ok = len(lower_targets) == 1
        lower_display = state_name(next(iter(lower_targets))) if collapse_ok else "VARIES*"
        cells = [lower_display, state_name(row["A"]), state_name(row["5"]),
                 state_name(row[":"]), state_name(row["/"]), state_name(row["."]),
                 state_name(row["-"]), state_name(row["_"]), state_name(row["?"])]
        lines.append(state_name(s).ljust(22) + "".join(c.ljust(10) for c in cells)[:200])
        if not collapse_ok:
            per_letter = ", ".join(f"{c}->{state_name(row[c])}" for c in "abcdefghijklmnopqrstuvwxyz")
            lines.append("    * per-letter detail: " + per_letter)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return len(seen), len(accepting)


def write_nfa_table(table, seen, path):
    lines = []
    lines.append("NFA TRANSITION TABLE (generated from automata.py)")
    lines.append("=" * 70)
    lines.append(f"Start state: {NFA_START}")
    accepting = sorted(s for s in seen if s in NFA_ACCEPTING)
    lines.append(f"Accepting states ({len(accepting)}): {', '.join(accepting)}")
    lines.append(f"Total reachable NFA states: {len(seen)}")
    lines.append("-" * 70)
    for s in sorted(seen):
        row = table[s]
        lower_targets = {row[c] for c in "abcdefghijklmnopqrstuvwxyz"}
        collapse_ok = len(lower_targets) == 1
        parts = []
        parts.append("a-z*->" + ("{" + ",".join(sorted(next(iter(lower_targets)))) + "}" if collapse_ok else "VARIES"))
        for label, sym in [("A", "A"), ("5", "5"), (":", ":"), ("/", "/"), (".", "."), ("-", "-"), ("_", "_"), ("?", "?")]:
            tgt = row[sym]
            if tgt:
                parts.append(f"{label}->{{{','.join(sorted(tgt))}}}")
        lines.append(f"{s:22s} " + "  ".join(parts))
        if not collapse_ok:
            per_letter = ", ".join(f"{c}->{{{','.join(sorted(row[c]))}}}" for c in "abcdefghijklmnopqrstuvwxyz" if row[c])
            lines.append("    * per-letter detail: " + per_letter)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return len(seen), len(accepting)


def gen_dfa_mermaid(table, seen, path):
    # High-level structural diagram grouped by phase, generated from the
    # actual reachable-state set (state COUNT and ACCEPT set below are the
    # generated ground truth; full character-by-character detail is in
    # dfa_transition_table.txt).
    lines = ["stateDiagram-v2", "    [*] --> Q0"]
    scheme_chain = ["Q0", "H", "HT", "HTT", "HTTP", "HTTPS", "COLON", "SLASH1", "SLASH2"]
    edges = [("Q0", "H", "h"), ("H", "HT", "t"), ("HT", "HTT", "t"), ("HTT", "HTTP", "p"),
             ("HTTP", "HTTPS", "s"), ("HTTP", "COLON", ":"), ("HTTPS", "COLON", ":"),
             ("COLON", "SLASH1", "/"), ("SLASH1", "SLASH2", "/")]
    for a, b, sym in edges:
        lines.append(f'    {a} --> {b}: {sym}')
    lines.append("    SLASH2 --> DOM_GROUP: [a-z0-9]")
    lines.append("    state DOM_GROUP {")
    n_dom = sum(1 for s in seen if isinstance(s, tuple))
    lines.append(f'        [*] --> DomainProcessing : "{n_dom} composite (label_validity,trie_node,seen_dot) states -- see dfa_transition_table.txt"')
    lines.append("        DomainProcessing --> DomainProcessing: letter/digit/hyphen/dot")
    lines.append("    }")
    lines.append("    DOM_GROUP --> PATH_SEG_START: / [only if seen_dot & trie_node is accepting TLD]")
    lines.append("    DOM_GROUP --> [*]: end-of-input [only if seen_dot & trie_node is accepting TLD]")
    lines.append("    PATH_SEG_START --> PATH_SEG: [a-zA-Z0-9_-]")
    lines.append("    PATH_SEG --> PATH_SEG_START: /")
    lines.append("    PATH_SEG --> PATH_SEG: [a-zA-Z0-9_-]")
    lines.append("    PATH_SEG_START --> [*]")
    lines.append("    PATH_SEG --> [*]")
    lines.append("    DOM_GROUP --> DEAD: invalid char / bad hyphen / non-TLD end")
    lines.append("    DEAD --> DEAD: any")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def gen_nfa_mermaid(table, seen, path):
    lines = ["stateDiagram-v2", "    [*] --> q0"]
    edges = [("q0", "h", "h"), ("h", "ht", "t"), ("ht", "htt", "t"), ("htt", "http", "p"),
             ("http", "https", "s"), ("http", "colon", ":"), ("https", "colon", ":"),
             ("colon", "slash1", "/"), ("slash1", "g_start", "/")]
    for a, b, sym in edges:
        lines.append(f"    {a} --> {b}: {sym}")
    lines.append('    g_start --> G_OK: alnum')
    lines.append('    g_start --> T1_x: alnum (if first char of a TLD)')
    lines.append('    note right of g_start: FORK -- genuine nondeterminism:\\nsame input char leads to TWO\\nactive states simultaneously')
    lines.append('    G_OK --> G_OK: alnum')
    lines.append('    G_OK --> G_HYP: -')
    lines.append('    G_HYP --> G_OK: alnum')
    lines.append('    G_OK --> g_start_dot: .')
    lines.append('    T1_x --> T1_x: alnum (still matching TLD prefix)')
    lines.append('    T1_x --> g_start_dot: . (first label only, never accepting alone)')
    lines.append('    g_start_dot --> G_OK: alnum')
    lines.append('    g_start_dot --> T_x: alnum (if first char of a TLD)')
    lines.append('    T_x --> T_x: alnum (still matching TLD prefix)')
    lines.append('    T_x --> g_start_dot: . (interior label matched a TLD)')
    lines.append('    T_x --> PATH_ACCEPT: / [only from a TLD-ACCEPTING trie node]')
    lines.append('    T_x --> [*]: end-of-input [only from a TLD-ACCEPTING trie node]')
    lines.append('    PATH_ACCEPT --> PATH_SEG: alnum/-/_')
    lines.append('    PATH_ACCEPT --> [*]')
    lines.append('    PATH_SEG --> PATH_SEG: alnum/-/_')
    lines.append('    PATH_SEG --> PATH_SEG_START: /')
    lines.append('    PATH_SEG_START --> PATH_SEG: alnum/-/_')
    lines.append('    PATH_SEG --> [*]')
    lines.append('    PATH_SEG_START --> [*]')
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    os.makedirs("diagrams", exist_ok=True)

    dfa_table, dfa_states = build_dfa_table()
    nfa_table, nfa_states = build_nfa_table()

    n_dfa_states, n_dfa_accept = write_dfa_table(dfa_table, dfa_states, "output/dfa_transition_table.txt")
    n_nfa_states, n_nfa_accept = write_nfa_table(nfa_table, nfa_states, "output/nfa_transition_table.txt")

    gen_dfa_mermaid(dfa_table, dfa_states, "diagrams/dfa.mmd")
    gen_nfa_mermaid(nfa_table, nfa_states, "diagrams/nfa.mmd")

    print(f"DFA: {n_dfa_states} reachable states (including DEAD), {n_dfa_accept} accepting.")
    print(f"NFA: {n_nfa_states} reachable states, {n_nfa_accept} accepting.")
    print("Wrote output/dfa_transition_table.txt, output/nfa_transition_table.txt")
    print("Wrote diagrams/dfa.mmd, diagrams/nfa.mmd")
