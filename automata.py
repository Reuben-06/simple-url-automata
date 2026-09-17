"""
automata.py
===========
Authoritative DFA and NFA implementation for the FROZEN URL LANGUAGE
described in TECHNICAL_PACKAGE.md.

This module is the single source of truth for the automata. All other
files (gen_tables.py, demo.py, tests.py) import from this module and do
not re-implement or duplicate any transition logic.

ASCII-ONLY LANGUAGE
--------------------
The language is explicitly ASCII-only. We never use Python's Unicode-aware
str.isalpha()/str.isdigit(); instead we use explicit ASCII range checks.
"""

from itertools import product

# ---------------------------------------------------------------------------
# 1. ALPHABET / CHARACTER CLASSIFICATION  (Section 12 / Section 9)
# ---------------------------------------------------------------------------

def is_upper(c):
    return 'A' <= c <= 'Z'

def is_lower(c):
    return 'a' <= c <= 'z'

def is_letter(c):
    return is_upper(c) or is_lower(c)

def is_digit(c):
    return '0' <= c <= '9'

def is_alnum(c):
    return is_letter(c) or is_digit(c)

# Character classes used in transition tables (Section 12 alphabet).
# Every character of the (finite) implementation alphabet maps to exactly
# one class name; anything else is OTHER (always invalid / dead).
def char_class(c):
    if is_letter(c):
        return 'LETTER'
    if is_digit(c):
        return 'DIGIT'
    if c == '-':
        return 'HYPHEN'
    if c == '.':
        return 'DOT'
    if c == '/':
        return 'SLASH'
    if c == ':':
        return 'COLON'
    if c == '_':
        return 'UNDERSCORE'
    return 'OTHER'

DEAD = 'DEAD'  # explicit sink / dead state used by both automata

# ---------------------------------------------------------------------------
# 2. FROZEN LANGUAGE PARAMETERS
# ---------------------------------------------------------------------------

# Finite, explicitly selected TLD set (Section 6). Chosen to be small enough
# to keep the automata manageable while covering every example URL named in
# the assignment brief (google.com, wikipedia.org, python.org, claude.ai).
TLD_SET = ["com", "org", "net", "edu", "ai"]

# Sanity: all TLDs must have distinct first letters so the trie used for
# TLD matching is a simple set of disjoint chains (keeps the automaton small
# and easy to verify by hand). This is asserted, not assumed.
assert len({t[0] for t in TLD_SET}) == len(TLD_SET), "TLD set must have distinct first letters"

# ---------------------------------------------------------------------------
# 3. TLD TRIE  (shared by both DFA-state encoding and NFA states)
# ---------------------------------------------------------------------------
# trie[node][char] -> node ; node 0 is the root.
# accepting_trie_nodes = set of nodes that correspond to a *complete* TLD.

def build_tld_trie(tld_set):
    trie = {0: {}}
    accepting = set()
    next_id = 1
    for tld in tld_set:
        node = 0
        for ch in tld:
            if ch in trie[node]:
                node = trie[node][ch]
            else:
                new_node = next_id
                next_id += 1
                trie[new_node] = {}
                trie[node][ch] = new_node
                node = new_node
        accepting.add(node)
    return trie, accepting, next_id  # next_id == number of trie nodes

TLD_TRIE, TLD_ACCEPT_NODES, TLD_NODE_COUNT = build_tld_trie(TLD_SET)
TLD_NONE = 'X'  # sentinel: "no longer a candidate TLD prefix" for this label


# ===========================================================================
# 4. DFA
# ===========================================================================
#
# The DFA state is a SINGLE value at all times (genuinely deterministic).
# During domain processing that single value is a composite/product state
# (label_validity, trie_node, seen_dot) -- this is standard product-DFA
# construction, still one active state, never a set of states.
#
# Scheme states (Section 15):
#   Q0 -> H -> HT -> HTT -> HTTP -> (S ->) COLON -> SLASH1 -> DOMAIN...
#
# Domain state tuple: ('DOM', label_validity, trie_node, seen_dot)
#   label_validity in {'START','OK','HYP'}
#   trie_node in {0..TLD_NODE_COUNT-1, TLD_NONE}
#   seen_dot in {False, True}   (True once at least one '.' consumed)
#
# Path states (Section 6, Section 15):
#   ('PATH_SEG_START', ...) / ('PATH_SEG', ...) tracked with a boolean
#   "just_saw_slash" folded into distinct state names below.

DFA_START = 'Q0'

def dfa_step(state, c):
    """delta_D(state, c) -> next state (DEAD if no valid transition)."""
    cls = char_class(c)

    # ---- scheme ----
    if state == 'Q0':
        return 'H' if c == 'h' else DEAD
    if state == 'H':
        return 'HT' if c == 't' else DEAD
    if state == 'HT':
        return 'HTT' if c == 't' else DEAD
    if state == 'HTT':
        return 'HTTP' if c == 'p' else DEAD
    if state == 'HTTP':
        if c == 's':
            return 'HTTPS'
        if c == ':':
            return 'COLON'
        return DEAD
    if state == 'HTTPS':
        return 'COLON' if c == ':' else DEAD
    if state == 'COLON':
        return 'SLASH1' if c == '/' else DEAD
    if state == 'SLASH1':
        return 'SLASH2' if c == '/' else DEAD
    if state == 'SLASH2':
        # first character of the first domain label
        return _dfa_domain_first_char(c)

    # ---- domain ----
    if isinstance(state, tuple) and state[0] == 'DOM':
        return _dfa_domain_step(state, c)

    # ---- path ----
    if state == 'PATH_SEG_START':
        return _dfa_path_char(c, fresh=True)
    if state == 'PATH_SEG':
        if cls == 'SLASH':
            return 'PATH_SEG_START'
        return _dfa_path_char(c, fresh=False)

    return DEAD


def _dfa_domain_first_char(c):
    if not is_alnum(c):
        return DEAD
    trie_node = TLD_TRIE[0].get(c, TLD_NONE)
    return ('DOM', 'OK', trie_node, False)


def _dfa_domain_step(state, c):
    _, validity, trie_node, seen_dot = state
    cls = char_class(c)

    if cls in ('LETTER', 'DIGIT'):
        new_trie = TLD_NONE
        if trie_node != TLD_NONE and trie_node in TLD_TRIE and c in TLD_TRIE[trie_node]:
            new_trie = TLD_TRIE[trie_node][c]
        return ('DOM', 'OK', new_trie, seen_dot)

    if cls == 'HYPHEN':
        if validity == 'START':
            return DEAD  # leading hyphen
        if validity == 'HYP':
            return DEAD  # consecutive hyphen
        # a hyphen can never be part of a TLD in our TLD set
        return ('DOM', 'HYP', TLD_NONE, seen_dot)

    if cls == 'DOT':
        if validity in ('START', 'HYP'):
            return DEAD  # empty label or trailing-hyphen label before dot
        # start a new label; TLD tracking resets
        return ('DOM', 'START', 0, True)

    if cls == 'SLASH':
        if validity == 'OK' and seen_dot and trie_node in TLD_ACCEPT_NODES:
            return 'PATH_SEG_START'
        return DEAD

    return DEAD  # anything else ends domain processing invalidly


def _dfa_path_char(c, fresh):
    if is_alnum(c) or c in ('-', '_'):
        return 'PATH_SEG'
    return DEAD


DFA_ACCEPT_DOMAIN_END = lambda state: (
    isinstance(state, tuple) and state[0] == 'DOM' and
    state[1] == 'OK' and state[3] is True and state[2] in TLD_ACCEPT_NODES
)


def validate_dfa(url):
    """Section 24: validate_dfa(url) -> bool"""
    state = DFA_START
    for c in url:
        if state == DEAD:
            return False
        state = dfa_step(state, c)
    if state == DEAD:
        return False
    if state == 'PATH_SEG_START' or state == 'PATH_SEG':
        return True  # domain complete, optional path fully consumed
    return DFA_ACCEPT_DOMAIN_END(state)


def dfa_trace(url):
    """Returns (accepted: bool, trace: list[(from_state, char, to_state)])."""
    state = DFA_START
    steps = []
    for c in url:
        if state == DEAD:
            steps.append((state, c, DEAD))
            break
        nxt = dfa_step(state, c)
        steps.append((state, c, nxt))
        state = nxt
    accepted = validate_dfa(url)
    return accepted, steps


# ===========================================================================
# 5. NFA
# ===========================================================================
#
# The NFA maintains a SET of active states and genuinely branches.
# Genuine nondeterminism (Section 18): at the START of every domain label,
# on the very first character, the NFA forks into two parallel state
# families for that label:
#   (a) a TLD-CANDIDATE path walking the shared TLD trie (states 'T<node>')
#   (b) a GENERIC-LABEL path that ignores TLD matching entirely for this
#       label ('G_OK' / 'G_HYP')
# Both families stay active simultaneously; a domain only ends successfully
# through the TLD-candidate family reaching an accepting trie node, while
# the generic family exists purely to allow non-TLD-shaped labels
# (e.g. "wikipedia", "www", "en") to be valid *interior* labels.
#
# No epsilon transitions are required for this language, so none are used
# (Section 19: "If epsilon transitions are unnecessary, prefer avoiding
# them.").

NFA_START = 'q0'

# States: q0,h,ht,htt,http,https,colon,slash1  (scheme, deterministic here
# but still expressed as NFA transitions returning frozensets of size 1)
# domain: 'G_START','G_OK','G_HYP' (generic-label family, shared across all
#          labels; no per-label duplication needed since it carries no TLD
#          memory) and 'T<node>' for node in trie (candidate family)
# path: 'PATH_SEG_START','PATH_SEG'

def _tld_state(node):
    return 'T%d' % node


NFA_TRIE_STATES = {_tld_state(n) for n in TLD_TRIE}
NFA_DOMAIN_SEEN_DOT_MARKER = 'DOTSEEN'  # auxiliary state, see below


def nfa_step(state, c):
    """delta_N(state, c) -> frozenset of next states (possibly empty)."""
    cls = char_class(c)
    out = set()

    if state == 'q0':
        if c == 'h':
            out.add('h')
    elif state == 'h':
        if c == 't':
            out.add('ht')
    elif state == 'ht':
        if c == 't':
            out.add('htt')
    elif state == 'htt':
        if c == 'p':
            out.add('http')
    elif state == 'http':
        if c == 's':
            out.add('https')
        if c == ':':
            out.add('colon')
    elif state == 'https':
        if c == ':':
            out.add('colon')
    elif state == 'colon':
        if c == '/':
            out.add('slash1')
    elif state == 'slash1':
        if c == '/':
            out.add('g_start')  # entering domain: label-start fork happens here

    elif state == 'g_start':
        # First character of the FIRST domain label. seen_dot is still
        # False here, so even if this label spells a complete TLD
        # (e.g. the single label "com") it must NOT be treated as an
        # accepting domain -- the grammar requires LABEL "." ... "." TLD,
        # i.e. at least two components. We therefore fork into the
        # ordinary generic-label family plus a SEPARATE "T1_" trie family
        # (distinct from the post-dot "T_" family) that can continue
        # matching and can hand off to a later label via '.', but can
        # never itself be an accepting state.
        if is_alnum(c):
            out.add('G_OK')
            node = TLD_TRIE[0].get(c)
            if node is not None:
                out.add('T1_%d' % node)

    elif state == 'G_OK':
        if is_alnum(c):
            out.add('G_OK')
        elif c == '-':
            out.add('G_HYP')
        elif c == '.':
            out.add('g_start_dot')  # new label, dot has been seen at least once
        # NOTE: a '/' here would end the domain on a label that never
        # matched a TLD -- that is invalid per the grammar, so the generic
        # family deliberately produces NO transition on '/' (this branch
        # simply dies, which is exactly what a non-TLD-terminated domain
        # must do).
    elif state == 'G_HYP':
        if is_alnum(c):
            out.add('G_OK')
        # '-' -> dead (consecutive hyphen), '.' -> dead (trailing hyphen), handled by no transition

    elif state == 'g_start_dot':
        if is_alnum(c):
            out.add('G_OK')
            node = TLD_TRIE[0].get(c)
            if node is not None:
                out.add(_tld_state(node))

    elif state.startswith('T1_'):
        # First-label trie-candidate family: can extend, or (only via '.')
        # hand off into a fresh label -- but can NEVER accept directly,
        # since a domain consisting of a single label is invalid.
        node = int(state[3:])
        if is_alnum(c):
            nxt = TLD_TRIE.get(node, {}).get(c)
            if nxt is not None:
                out.add('T1_%d' % nxt)
        elif c == '.':
            out.add('g_start_dot')  # whether or not `node` completes a TLD,
            # this was only the first label; either way we move on to the
            # next label with seen_dot now true. (If the first label did
            # NOT fully spell a TLD this transition is harmless since the
            # generic family already covers that path; if it DID spell a
            # TLD, e.g. "com.example.org", it is a perfectly valid interior
            # label and processing must continue.)
        # '-' and '/' produce no transition: a hyphen can't continue a TLD,
        # and '/' here would mean "single label + path", which is invalid.

    elif state.startswith('T') and state != 'PATH_SEG_START':
        node = int(state[1:])
        if is_alnum(c):
            nxt = TLD_TRIE.get(node, {}).get(c)
            if nxt is not None:
                out.add(_tld_state(nxt))
            # falling off the trie simply drops this branch (no transition)
        elif c == '-':
            pass  # a hyphen can never continue a TLD -> branch dies
        elif c == '.':
            if node in TLD_ACCEPT_NODES:
                out.add('g_start_dot')  # this label matched a TLD but there IS another dot,
                                          # so it was only an interior label; restart fresh
        elif c == '/':
            if node in TLD_ACCEPT_NODES:
                out.add('PATH_SEG_START_ACCEPTING')

    elif state == 'PATH_SEG_START' or state == 'PATH_SEG_START_ACCEPTING':
        if is_alnum(c) or c in ('-', '_'):
            out.add('PATH_SEG')
    elif state == 'PATH_SEG':
        if is_alnum(c) or c in ('-', '_'):
            out.add('PATH_SEG')
        elif c == '/':
            out.add('PATH_SEG_START')

    return frozenset(out)


# Accepting states of the NFA (Section 25 point 7: "accept if at least one
# active state is accepting"):
#   - T<node> where node is a completed-TLD trie node: the string ends
#     immediately after the domain (no trailing '/'), e.g. "https://a.com"
#   - PATH_SEG_START_ACCEPTING: the string ends right after "domain/"
#     (trailing slash, empty path -- allowed, PATH ::= (...)* "/"? )
#   - PATH_SEG_START / PATH_SEG: the string ends inside/after a path segment
NFA_ACCEPTING = frozenset(
    {_tld_state(n) for n in TLD_ACCEPT_NODES} |
    {'PATH_SEG_START_ACCEPTING', 'PATH_SEG_START', 'PATH_SEG'}
)


def nfa_run_active_states(url):
    """Runs the NFA and returns (list_of_active_state_sets, final_active_set)."""
    active = frozenset({NFA_START})
    history = [active]
    for c in url:
        nxt = set()
        for s in active:
            nxt |= nfa_step(s, c)
        active = frozenset(nxt)
        history.append(active)
        if not active:
            break
    return history, active


def validate_nfa(url):
    """Section 25: validate_nfa(url) -> bool.

    Accepts if, after consuming the *entire* input, at least one active
    state is an accepting state. A bare accepting domain-end state
    (PATH_SEG_START_ACCEPTING) accepts with no path. PATH_SEG_START /
    PATH_SEG accept because they can only be reached downstream of an
    accepting domain-end transition (the generic-only family never reaches
    them, see nfa_step).
    """
    _, final_active = nfa_run_active_states(url)
    if not url:
        return False
    return len(final_active & NFA_ACCEPTING) > 0


def nfa_trace(url):
    history, final_active = nfa_run_active_states(url)
    accepted = validate_nfa(url)
    return accepted, history


# ===========================================================================
# 6. REGEX CROSS-CHECK (Section 13) -- independent specification, never used
#    internally by the DFA/NFA validators above.
# ===========================================================================
import re

_LABEL = r'[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*'
_TLD_ALT = '|'.join(sorted(TLD_SET, key=len, reverse=True))
_SEGMENT = r'[A-Za-z0-9_-]+'
URL_REGEX = re.compile(
    r'^(?:http|https)://' +
    _LABEL + r'(?:\.' + _LABEL + r')*\.(?:' + _TLD_ALT + r')' +
    r'(?:/' + _SEGMENT + r')*/?$'
)


def validate_regex(url):
    return bool(URL_REGEX.match(url))
