# TECHNICAL_PACKAGE.md

> **This package is the verified technical source of truth for the
> project.** A later report-writing Claude session must not redesign the
> automata, change the grammar or accepted language, invent test results,
> invent state counts, invent equivalence results, introduce unsupported
> features, or claim complete URL validation. Any proposed improvement
> belongs under §32 Future Scope, never in the current implementation
> description.
>
> Every number in this document was produced by actually executing
> `tests.py`, `equivalence.py`, and `gen_tables.py` against the code in
> `automata.py` in this same project. Nothing here is estimated or
> fabricated. If you re-run the three scripts and get different numbers,
> the code changed — trust the fresh execution, not this document.

---

## 1. Project objective
Demonstrate, for a genuine real-world validation problem, how DFA and NFA
formalisms can both model the *same* regular language, verify (not just
assert) that they do, implement and test both, and critically compare
their suitability — with URL validation as the vehicle, not the point.

## 2. Real-world problem
Many systems (form inputs, chat links, crawlers, allow-lists) need a fast
syntactic check of "does this string look like a well-formed web URL"
before doing anything more expensive (DNS lookup, HTTP request, security
scanning). This project builds that syntactic gate for a defined,
realistic subset of `http`/`https` URLs.

## 3. Candidate specifications considered

| # | Candidate | Realism | Regularity | Est. DFA states | Nondeterminism opportunity | Verdict |
|---|---|---|---|---|---|---|
| A | Fixed single domain only (e.g. `https://example.com` literally, no variation) | Low — unusable for real URLs | Trivially regular | ~25 (all literal keyword-matching) | None (purely literal string matching) | Rejected: too trivial, no genuine domain/path structure to reason about, poor demonstration of automata theory. |
| B | Full RFC 3986 URI grammar (scheme, userinfo, host incl. IPv4/IPv6/reg-name, port, path, query, fragment, percent-encoding) | High | Regular in principle but very large | Hundreds+ | Real, but drowned in incidental complexity | Rejected: violates the assignment's own "avoid unnecessary complexity" guidance and the lesson from the previous overly-broad/overly-narrow attempt; would take the project into "URL-parser software project" territory rather than automata theory. |
| C (chosen) | `http`/`https` scheme + case-insensitive multi-label domain with hyphen rules + finite explicit TLD set + optional restricted path | High for the stated scope | Regular, manageable | ~40–50 (verified: 45) | Genuine — TLD matching against a finite candidate set naturally forks into "generic label" vs "TLD-candidate" paths | **Selected.** Realistic enough to accept every example URL named in the assignment brief, small enough to fully specify, test, and diagram, and it contains a natural, non-contrived source of nondeterminism. |

Candidate C was selected because it is the only one that is simultaneously
realistic, fully regular, small enough to verify exhaustively, and
contains *genuine* (not manufactured) nondeterminism suitable for
contrasting DFA vs NFA execution.

## 4. Final frozen specification

```
URL    ::= SCHEME "://" DOMAIN PATH?
SCHEME ::= "http" | "https"                      (lowercase only)
DOMAIN ::= LABEL ("." LABEL)* "." TLD             (>= 2 components)
LABEL  ::= ALNUM+ ("-" ALNUM+)*                   (case-insensitive)
TLD    ::= "com" | "org" | "net" | "edu" | "ai"   (lowercase only, finite set)
PATH   ::= ("/" SEGMENT)* "/"?
SEGMENT::= (ALNUM | "_" | "-")+
ALNUM  ::= [A-Za-z0-9]
```

## 5. Input
A single string, taken as-is (no trimming, no normalization, no
lower-casing). The automata consume it character by character.

## 6. Constraints
- ASCII only; every character must be classified as LETTER, DIGIT,
  HYPHEN, DOT, SLASH, COLON, UNDERSCORE, or OTHER (Section 12 alphabet).
  OTHER is never accepted anywhere.
- Scheme and TLD are **lowercase-only**. Domain labels are
  case-insensitive. Path segments are case-insensitive.
- No leading, trailing, or consecutive hyphens within a domain label.
- Domain must have at least two components (a bare TLD such as `com` is
  invalid; `com.example.org` is valid because `com` there is an interior
  label, not the final TLD).
- Path segments may not be empty (`//` is rejected).
- The entire input must be consumed for acceptance (no partial matches).

## 7. Assumptions
- The TLD set `{com, org, net, edu, ai}` is a deliberately small,
  explicitly documented stand-in for the real, much larger TLD universe.
  It was chosen specifically because it covers every example URL named in
  the assignment brief (`google.com`, `wikipedia.org`, `python.org`,
  `claude.ai`) while keeping the TLD-matching sub-automaton small (a
  5-branch trie of 15 nodes with no shared prefixes, since `c`, `o`, `n`,
  `e`, `a` are all distinct first letters).
- "Realistic" is scoped to plain `http(s)` links with a hostname and a
  simple path — the single most common real-world case — not the full
  URI standard.

## 8. Limitations (deliberately excluded features)
Port numbers, userinfo/authentication, query strings, fragments, IPv4/IPv6
literals, percent-encoding, internationalized domain names, and any TLD
outside the 5-item set. These are scope limitations of the *chosen
language*, not limitations of finite automata as a formalism — a larger
(but still regular) grammar could express all of them; see §32.

## 9. Alphabet
```
UPPER      = A-Z
LOWER      = a-z
DIGIT      = 0-9
HYPHEN     = -
UNDERSCORE = _
DOT        = .
SLASH      = /
COLON      = :
OTHER      = any character not covered above (always invalid)
```
Implemented in `automata.py` via explicit ASCII range checks
(`'A' <= c <= 'Z'`, etc.) — never via `str.isalpha()`/`str.isdigit()`,
which are Unicode-aware in Python and would silently accept non-ASCII
letters/digits.

## 10. Formal grammar
See §4 above (the frozen specification). `automata.py`'s `URL_REGEX`
(§11) is an independent transcription of exactly this grammar, used only
as a cross-check, never as part of the DFA/NFA execution path.

## 11. Regular expression (independent cross-check only)
```
^(?:http|https)://
  [A-Za-z0-9]+(?:-[A-Za-z0-9]+)*
  (?:\.[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)*
  \.(?:com|org|net|edu|ai)
  (?:/[A-Za-z0-9_-]+)*/?$
```
This is compiled in `automata.py` as `URL_REGEX` / `validate_regex()`. It
is used *only* as a third, independent check in the test suite — the DFA
and NFA validators never call it and never call each other.

## 12. DFA formal definition
`M_D = (Q_D, Σ, δ_D, q0, F_D)`

- **Σ**: the 8 character classes of §9 (implemented over the concrete
  ASCII alphabet).
- **q0** = `Q0`.
- **Q_D**: all states reachable from `q0` under δ_D. Verified by
  exhaustive BFS in `gen_tables.py`: **45 reachable states**, including
  one explicit dead/sink state `DEAD`.
- **F_D**: states from which the DFA accepts if input ends there —
  `PATH_SEG_START`, `PATH_SEG`, and every domain-composite state
  `('DOM', 'OK', trie_node, True)` where `trie_node` is one of the 5
  TLD-accepting trie nodes. Verified count: **7 accepting states**.
- **δ_D**: implemented as `dfa_step(state, c)` in `automata.py`; total
  transition function (every state × every class has exactly one
  destination, `DEAD` where no valid transition exists — verified by
  construction, since `dfa_step` always returns a value, never raises).

## 13. DFA state descriptions
| Group | States | Meaning |
|---|---|---|
| Scheme | `Q0,H,HT,HTT,HTTP,HTTPS,COLON,SLASH1,SLASH2` | Matching the literal keyword `http`/`https://` character by character. |
| Domain | `('DOM', validity, trie_node, seen_dot)` | `validity` ∈ {START,OK,HYP} tracks hyphen legality of the *current* label; `trie_node` tracks how far the current label matches a candidate TLD (or `'X'` if it has diverged from every TLD); `seen_dot` records whether at least one `.` has been consumed (needed because a bare TLD alone, e.g. `com`, must be rejected). |
| Path | `PATH_SEG_START, PATH_SEG` | Start of a path segment / inside a path segment. |
| Sink | `DEAD` | Absorbing reject state. |

## 14. DFA transition table
Generated directly from the implementation: see
`output/dfa_transition_table.txt` (45 states; lowercase-letter columns are
collapsed to `a-z*` wherever every one of the 26 letters behaves
identically, with a `* per-letter detail` line spelled out wherever they
don't — i.e. wherever TLD-trie branching makes a specific letter behave
differently from the rest).

## 15. DFA diagram source
`diagrams/dfa.mmd` (Mermaid `stateDiagram-v2`). The scheme-matching chain
and path-handling states are drawn explicitly; the 45−9(scheme)−2(path)−1(dead)
≈ domain-composite states are grouped into one `DOM_GROUP` composite region
(the full per-state, per-character detail for that region is the generated
transition table in §14, which is the authoritative source — the diagram
is a structural summary of it, not a replacement for it).

## 16. NFA formal definition
`M_N = (Q_N, Σ, δ_N, q0, F_N)`

- **q0** = `q0` (start of scheme matching).
- **Q_N**: all states reachable from `q0` under δ_N. Verified: **43
  reachable states**.
- **F_N**: `PATH_SEG`, `PATH_SEG_START`, `PATH_SEG_START_ACCEPTING`, and
  every TLD-trie state `T<n>` (post-dot family) where `n` is a
  TLD-accepting node. Verified count: **8 accepting states**.
- **δ_N**: `nfa_step(state, c) -> frozenset(states)`, genuinely returning
  zero, one, or multiple destination states. No epsilon transitions are
  used or needed for this language.

## 17. NFA state descriptions
| Group | States | Meaning |
|---|---|---|
| Scheme | `q0,h,ht,htt,http,https,colon,slash1` | Same literal keyword matching as the DFA (deterministic here — nondeterminism appears only where the language itself is genuinely ambiguous, at label starts). |
| Domain — generic family | `g_start, G_OK, G_HYP, g_start_dot` | Tracks a label purely for hyphen-legality, ignoring TLD identity. |
| Domain — first-label TLD-candidate family | `T1_<node>` | Tracks the *first* label's progress through the TLD trie. Can hand off to the next label via `.`, but can **never** accept directly (a lone label can't be a full domain). |
| Domain — interior-label TLD-candidate family | `T<node>` | Tracks a *post-dot* label's progress through the TLD trie; reaching an accepting node here is what allows the domain to end. |
| Path | `PATH_SEG_START, PATH_SEG, PATH_SEG_START_ACCEPTING` | Same role as the DFA's path states; the `_ACCEPTING` variant marks "just finished a valid domain with a trailing `/`". |

**Genuine nondeterminism.** At the first character of every label, the
NFA is simultaneously in the generic-label state *and* (if that character
starts any TLD) a TLD-candidate state — e.g. reading `c` after `slash1`
puts the NFA in `{G_OK, T1_?}` at once. This is not manufactured: it
reflects the real ambiguity in the language — the automaton cannot know,
from a single character, whether this label is going to end up being the
domain's TLD or an ordinary label, so it must track both possibilities in
parallel. Verified example trace (`https://a.com`):
```
{g_start} --a--> {G_OK, T1_13}
                 --.--> {g_start_dot}
                 --c--> {G_OK, T1}
                 --o--> {G_OK, T2}
                 --m--> {G_OK, T3}      (T3 is accepting -> ACCEPT)
```

## 18. NFA transition table
`output/nfa_transition_table.txt` (43 states; each row lists, per
character class, the *set* of destination states — visibly of size 0, 1,
or 2 for this automaton).

## 19. NFA diagram source
`diagrams/nfa.mmd`. The label-start fork is drawn explicitly and annotated
as the genuine-nondeterminism point; the TLD trie families are summarized
(full detail in §18's generated table).

## 20. Implementation overview
Single authoritative module `automata.py` containing: ASCII character
classification, the TLD trie builder, `dfa_step`/`validate_dfa`/`dfa_trace`,
`nfa_step`/`validate_nfa`/`nfa_trace`, and the independent `validate_regex`
cross-check. `gen_tables.py`, `tests.py`, `equivalence.py`, and `demo.py`
all import from this one module — there is exactly one implementation of
each automaton in the project.

## 21. Testing methodology
`tests.py` checks, for every case, `DFA(u) == NFA(u) == REGEX(u) ==
EXPECTED`; any single disagreement fails that case. Results are written to
`output/test_output.txt` from an actual run, not hand-typed.

## 22. Test categories
Valid (30 cases: both schemes, all 5 TLDs, subdomains, digits, internal
hyphens, uppercase letters, paths, underscores, trailing slash, a
UUID-shaped path segment, realistic assignment-brief URLs), Invalid (37
cases: wrong/malformed scheme, missing `://`, missing domain/TLD,
unsupported TLD, leading/trailing/consecutive hyphens, spaces, malformed
path, every explicitly excluded feature — query, fragment, userinfo,
port, IPv4, IPv6 — and uppercase scheme/TLD), Boundary (8 minimal-diff
pairs), Unicode regression (4 cases, all must reject).

## 23. Actual test results (from an executed run)
```
VALID                               total= 30  passed= 30  failed=  0
INVALID                             total= 37  passed= 37  failed=  0
BOUNDARY                            total=  8  passed=  8  failed=  0
UNICODE (all must reject)           total=  4  passed=  4  failed=  0
------------------------------------------------------------
Total tests: 79
Passed: 79
Failed: 0

DFA/NFA mismatches: 0
Regex mismatches: 0
```
Full output: `output/test_output.txt`.

## 24. Unicode results
All 4 ASCII-regression cases (`éxample.com`, `例子.com`, `example.com/é`,
`exam٠ple.com`) were rejected by DFA, NFA, and regex alike — confirming
the language is genuinely ASCII-only and that no Python Unicode-aware
string method leaked into the classification logic.

## 25. Regex cross-check
0 mismatches across all 79 test cases (see §23). The regex was never used
inside `validate_dfa`/`validate_nfa` — both automata process input
independently, character by character, through their own state machines.

## 26. Subset construction (NFA → DFA′)
Executed in `equivalence.py`, starting from `{q0}`:
```
Individual NFA states encountered: 43
Reachable subsets (states of DFA'): 43
Accepting subsets: 8
Transitions explored (|subsets| x |alphabet|): 1462
```
(Alphabet used for this exploration: 34 representative symbols — see §27.)
Full output: `output/equivalence_output.txt`.

## 27. DFA/NFA equivalence verification
Two independent checks, both actually executed:

**Empirical** — the full 79-case test suite (§23): 0 DFA/NFA
disagreements.

**Structural** — exhaustive BFS over reachable
`(DFA state, NFA active-state set)` pairs, starting from
`(Q0, {q0})`, using a 34-symbol representative alphabet (every individual
lowercase letter — since scheme keywords and TLD-trie branching are
letter-specific — plus one representative uppercase letter, one
representative digit, the 5 structural symbols `: / . - _`, and one
representative "any other character" symbol; uppercase letters and digits
are provably interchangeable within their class because neither the
scheme keywords nor any TLD contains a digit or ever matches an uppercase
letter in this implementation).
```
Reachable (DFA-state, NFA-active-set) pairs: 46
Pairs checked for accept-status agreement: 46
Mismatches found: 0
```
**What this establishes**: because both automata are finite-state and the
alphabet was constructed so every character within a class provokes
identical transitions in both machines, checking all 46 reachable pairs
is checking every input class the automata can ever distinguish between —
not merely 79 hand-picked examples. This is the stronger, structural claim
Section 34 requires; the 79-case suite is the empirical complement, not
the sole evidence.

## 28. Complexity analysis
**DFA**: single active state at all times; each input character costs
O(1) (a dictionary/branch lookup), so validating a string of length *n*
costs O(n) time and O(1) additional memory (one current-state value,
which is a small fixed-size tuple in the domain phase). 45 reachable
states in total.

**NFA**: as implemented (explicit active-state-set simulation, no subset
precomputation), each character costs O(|active set|) work, and the
active set can be up to size 2 for this language (never more, because the
grammar only ever forks two ways — generic vs one TLD candidate — at a
label start), so validating a string of length *n* still costs O(n) time
in practice, with a small constant-factor overhead versus the DFA and
O(1)-bounded (≤2) memory for the active set. If nondeterminism were richer
(e.g. many overlapping keyword prefixes) NFA memory could grow with the
branching factor; that does not happen here because the TLD set's first
letters are all distinct.

Neither automaton is universally faster or smaller for this problem: the
DFA is a single, larger, pre-flattened machine (45 states) with strictly
O(1)-per-character work and no active-set bookkeeping; the NFA is smaller
in raw component states before flattening but pays a (here, tiny) runtime
cost for simulating branching.

## 29. Critical DFA vs NFA comparison
| Aspect | DFA | NFA |
|---|---|---|
| Design | One explicit product state per (label-validity, TLD-trie-progress, seen-dot) combination must be pre-computed; more upfront design effort. | States map directly onto the grammar's natural alternatives (generic label vs TLD candidate); design mirrors the grammar closely. |
| State count (this project) | 45 | 43 (raw NFA states) / 43 reachable subsets after subset construction |
| Transition structure | Fully deterministic: exactly one destination per (state, class). | Genuinely branching at label starts (2-way); mostly deterministic elsewhere. |
| Execution model | One current state; O(1) work per character. | Active *set* of ≤2 states; O(|set|) work per character. |
| Memory during execution | Fixed, minimal (one tuple). | Fixed, minimal (set of ≤2 items) — negligible for this language, but this would NOT hold if branching factor were larger. |
| Implementation | Slightly more code to enumerate/compose the product state, but each transition is a simple lookup. | Slightly less state-composition logic, but every step must union several destination sets. |
| Maintainability | Adding a new orthogonal feature (e.g. a case-insensitive-TLD flag) means re-deriving the product state space by hand. | Adding new alternatives (e.g. a new TLD) is a one-line addition to the trie; the fork structure absorbs it naturally. |
| Modification cost for a larger TLD set | Grows the flattened state count directly and linearly with trie size (verified: 15 trie nodes contributed roughly half of the DFA's 45 states). | Grows the NFA's raw state count identically, but the *implementation* code barely changes — only the trie, not the transition function. |
| Practical deployment | Directly executable, predictable worst-case latency, no runtime branching logic — the natural choice for a production validator called many times. | Needs either a subset-construction pass ahead of time (recovering DFA-like performance) or per-call active-set simulation (small constant overhead here, but no such guarantee in general). |

**Which is more suitable for *modelling* this problem?** The NFA — its
structure follows the grammar directly, and the label-start fork is a
natural, legible representation of the real ambiguity ("is this the TLD
or not?") without having to hand-flatten it into a product state.

**Which is more suitable for *direct execution*?** The DFA — O(1)
guaranteed work per character, no active-set bookkeeping, and (for this
specific, TLD-set-bounded language) it isn't even meaningfully larger
than the NFA (45 vs 43 states). For a production URL-validation gate
called on every request, the DFA (or the subset-construction DFA′ derived
from the NFA, which the project also builds and verifies in §26) is the
right choice.

## 30. Practical application
```
User/System Input
        |
URL Validation Module  (validate_dfa / validate_nfa from automata.py)
        |
   ACCEPT / REJECT  (syntax only)
        |
Application Logic (e.g., proceed to DNS resolution / HTTP request /
                    reject and show a form error)
```
The automata provide **syntactic** validation only. They establish
nothing about whether a domain exists or resolves, whether a server is
reachable, whether a page exists at that path, or whether a URL is
malicious or trustworthy — those require separate mechanisms entirely
outside the scope of finite automata (DNS lookups, HTTP requests,
reputation/threat-intel services).

## 31. Limitations
See §8. Additionally: TLD set is intentionally small (5 entries) and does
not represent the real TLD universe; extending it is a Future Scope item,
not a defect in the current, explicitly-scoped implementation.

## 32. Future scope
- Expand the TLD set (mechanically: extend `TLD_SET` in `automata.py`;
  the trie builder and both automata already generalize to any TLD list
  with distinct first letters without further code changes — a shared
  first letter would require additional trie-branching logic not
  currently implemented).
- Add optional port numbers (`:\d+`), which is regular and could be
  inserted as an optional sub-machine between DOMAIN and PATH.
- Add query strings and fragments (both regular, straightforward
  extensions to the grammar and both automata).
- Add IPv4 literal hosts as an alternative to DOMAIN (regular).
- IPv6 literals and percent-encoding are regular in principle but would
  meaningfully increase state count and are left as future work.
- Internationalized domain names (Unicode/IDN) would require either a
  Punycode-normalization preprocessing step (outside the automaton) or a
  substantially larger alphabet — a deliberate non-goal here, per §9.
Any such extension requires updating the formal grammar first, then
rebuilding and re-verifying every downstream artifact (regex, DFA, NFA,
tables, diagrams, tests) — never patching the code without updating the
specification, per the project's source-of-truth rule.

## 33. Live demonstration procedure
1. `python demo.py` → enter `https://www.google.com` → both ACCEPT.
2. Enter `https://en.wikipedia.org/wiki/Thikse_Monastery` (or
   `https://claude.ai/chat/c978ae8c-cb6f-42b7-bd9f-0f9f594f7a76`) → both
   ACCEPT, demonstrating a realistic path.
3. Enter `https://ex--ample.com` (consecutive hyphen) → both REJECT.
4. `python tests.py` → show the real 79/79 pass output.
5. `python demo.py --trace` on `https://a.com` → point at the NFA trace
   line `{G_OK, T1} → {G_OK, T2} → {G_OK, T3}` and contrast it with the
   DFA trace's single state per line — this is the clearest live
   illustration of "DFA: one active state" vs "NFA: possibly many."

## 34. Presentation talking points
- The URL is the application; the automata are the deliverable.
- The language was frozen *before* building the automata, and every
  downstream artifact (grammar, regex, DFA, NFA, tables, diagrams, tests)
  was built to match it — not the other way around.
- The NFA's nondeterminism is genuine, not decorative: it comes directly
  from the fact that, one character into a label, the automaton cannot
  yet know whether that label will turn out to be the TLD.
- Equivalence was checked two ways: empirically (79 curated cases) and
  structurally (exhaustive 46-pair reachable-state exploration) — the
  stronger structural claim is what actually proves language equality,
  not the example count.
- DFA and NFA came out close in size for this language (45 vs 43 states)
  specifically because the TLD set's first letters are all distinct,
  keeping branching factor low; a differently-chosen TLD set with shared
  prefixes would widen the gap.

## 35. Likely professor questions and technically correct answers
- **"Why isn't this NFA using epsilon transitions?"** — The language
  doesn't need them; every fork in this grammar happens on an actual
  input character (the first letter of a label), so epsilon transitions
  would only add unneeded machinery (Section 19 explicitly recommends
  avoiding them when unnecessary).
- **"How do you know the DFA and NFA are equivalent, not just 'pass the
  same tests'?"** — The product-state BFS in §27/§29 exhaustively checks
  every state pair the two machines can reach under a representative
  alphabet engineered so no character is behaviorally distinguishable
  from another in its class; that is a structural argument, not a
  sampling argument.
- **"Why exclude ports/query strings/IPs?"** — Explicit scope decision
  (§8) to keep the automata small enough to fully specify, diagram, and
  verify by hand within the assignment's scope; each is itself regular
  and is listed as straightforward Future Scope (§32).
- **"Isn't 'com' a valid TLD by itself as a domain?"** — No: the grammar
  requires `LABEL "." TLD`, i.e. at least two components; a bare `com` is
  syntactically a single label with no TLD suffix, and both automata
  reject it (verified: `https://com` → REJECT; `https://com.example.org`
  → ACCEPT, because there `com` is a valid *interior* label, not the
  whole domain).
- **"Why does the DFA have almost as many states as the raw NFA?"** —
  Because the TLD set's 5 members all start with different letters, the
  TLD trie doesn't need to be duplicated/expanded for the DFA's product
  construction the way it would if TLDs shared prefixes; the "flattening
  cost" of going from NFA to DFA is small for this particular language.

## 36. Verified source files
`automata.py`, `tests.py`, `equivalence.py`, `gen_tables.py`, `demo.py`,
`diagrams/dfa.mmd`, `diagrams/nfa.mmd`,
`output/dfa_transition_table.txt`, `output/nfa_transition_table.txt`,
`output/test_output.txt`, `output/equivalence_output.txt` — all present
in this project directory and all produced by actually running the
scripts listed, on the date this package was generated.
