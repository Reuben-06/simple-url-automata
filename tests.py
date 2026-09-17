"""
tests.py
========
Comprehensive test suite. For EVERY test case we verify
    DFA(input) == NFA(input) == REGEX(input) == EXPECTED
Any mismatch is a hard failure (Sections 28-32).

Run:
    python tests.py
"""

from automata import validate_dfa, validate_nfa, validate_regex

# ---------------------------------------------------------------------------
# VALID cases
# ---------------------------------------------------------------------------
VALID = [
    "http://example.com",
    "https://example.com",
    "https://example.org",
    "https://example.net",
    "https://example.edu",
    "https://example.ai",
    "https://www.google.com",
    "https://en.wikipedia.org/wiki/Thikse_Monastery",
    "https://claude.ai/chat/c978ae8c-cb6f-42b7-bd9f-0f9f594f7a76",
    "https://www.python.org/downloads/",
    "https://sub.example.org",
    "https://a.b.c.example.com",
    "https://my-site.example.net",
    "https://my-site.example.net/products/item-42",
    "https://EXAMPLE.com",
    "https://ExAmPlE.org",
    "https://example123.com",
    "https://123example.com",
    "https://ab12-cd34.example.com",
    "https://example.com/",
    "https://example.com/wiki/Thikse_Monastery",
    "https://example.com/chat/session-123",
    "https://example.com/downloads/file_name",
    "https://example.com/products/item-42",
    "https://example.com/a/b/c/d",
    "https://example.com/a_b-c/123/",
    "https://com.example.org",           # 'com' as a valid *interior* label
    "https://net.com",
    "http://a.com",
    "https://a.com",
]

# ---------------------------------------------------------------------------
# INVALID cases
# ---------------------------------------------------------------------------
INVALID = [
    "ftp://example.com",                 # wrong scheme
    "htt://example.com",                 # malformed scheme
    "https//example.com",                # missing colon
    "https:/example.com",                # missing one slash
    "https:example.com",                 # missing //
    "https://",                          # missing domain entirely
    "https://.com",                      # empty first label
    "https://example.",                  # missing TLD
    "https://example",                   # missing TLD (no dot at all)
    "https://com",                       # bare TLD, only one label
    "https://example.xyz",               # unsupported TLD
    "https://example.co",                # unsupported TLD (not in set)
    "https://-example.com",              # leading hyphen
    "https://example-.com",              # trailing hyphen
    "https://ex--ample.com",             # consecutive hyphen
    "https://example.-com",              # TLD-adjacent leading hyphen on label
    "https://exa mple.com",              # space
    "https://example.com ",              # trailing space
    " https://example.com",              # leading space
    "https://example..com",              # empty interior label
    "https://example.com//test",         # empty path segment (//)
    "https://example.com/a//b",          # empty path segment mid-path
    "https://example.com/a b",           # space in path
    "https://example.com/a.b",           # dot not allowed in path segment
    "https://example.com?x=1",           # query string (excluded feature)
    "https://example.com#section",       # fragment (excluded feature)
    "https://user:pass@example.com",     # userinfo (excluded feature)
    "https://example.com:8080",          # port (excluded feature)
    "https://192.168.0.1",               # IPv4 (excluded feature)
    "https://[::1]",                     # IPv6 (excluded feature)
    "HTTPS://example.com",               # uppercase scheme (scheme is lowercase-only)
    "Https://example.com",
    "https://example.COM",               # uppercase TLD (TLD is lowercase-only)
    "https://example.Com",
    "",                                   # empty string
    "example.com",                        # missing scheme entirely
    "www.example.com",                    # missing scheme entirely
]

# ---------------------------------------------------------------------------
# BOUNDARY cases: pairs that differ by exactly one rule (Section 30)
# ---------------------------------------------------------------------------
BOUNDARY = [
    ("https://example.com", True),
    ("https://-example.com", False),
    ("https://example-.com", False),
    ("https://ex--ample.com", False),
    ("https://ex-ample.com", True),
    ("https://example.xyz", False),
    ("https://e.com", True),             # single-char label, minimal valid
    ("https://-.com", False),            # single-char label that's just a hyphen
]

# ---------------------------------------------------------------------------
# UNICODE regression (Section 31) -- language is ASCII-only, all must reject
# ---------------------------------------------------------------------------
UNICODE_CASES = [
    "https://\u00e9xample.com",          # https://éxample.com
    "https://\u4f8b\u5b50.com",          # https://例子.com  (example.com in Chinese)
    "https://example.com/\u00e9",        # https://example.com/é
    "https://exam\u0660ple.com",         # https://exam٠ple.com (Arabic-Indic digit zero)
]


def _run_group(name, cases_with_expected):
    total = 0
    passed = 0
    mismatches = []
    for url, expected in cases_with_expected:
        total += 1
        d = validate_dfa(url)
        n = validate_nfa(url)
        r = validate_regex(url)
        if d == n == r == expected:
            passed += 1
        else:
            mismatches.append((url, expected, d, n, r))
    return name, total, passed, mismatches


def run_all():
    groups = []
    groups.append(_run_group("VALID", [(u, True) for u in VALID]))
    groups.append(_run_group("INVALID", [(u, False) for u in INVALID]))
    groups.append(_run_group("BOUNDARY", BOUNDARY))
    groups.append(_run_group("UNICODE (all must reject)", [(u, False) for u in UNICODE_CASES]))

    total = sum(g[1] for g in groups)
    passed = sum(g[2] for g in groups)
    failed = total - passed

    dfa_nfa_mismatches = 0
    regex_mismatches = 0
    all_mismatches = []
    for name, t, p, mism in groups:
        for (url, expected, d, n, r) in mism:
            all_mismatches.append((name, url, expected, d, n, r))
            if d != n:
                dfa_nfa_mismatches += 1
            if r != d or r != n:
                regex_mismatches += 1

    lines = []
    lines.append("=" * 60)
    lines.append("URL AUTOMATA TEST SUITE - RESULTS")
    lines.append("=" * 60)
    for name, t, p, mism in groups:
        lines.append(f"{name:35s} total={t:3d}  passed={p:3d}  failed={t - p:3d}")
    lines.append("-" * 60)
    lines.append(f"Total tests: {total}")
    lines.append(f"Passed: {passed}")
    lines.append(f"Failed: {failed}")
    lines.append("")
    lines.append(f"DFA/NFA mismatches: {dfa_nfa_mismatches}")
    lines.append(f"Regex mismatches: {regex_mismatches}")
    if all_mismatches:
        lines.append("")
        lines.append("MISMATCH DETAILS:")
        for (name, url, expected, d, n, r) in all_mismatches:
            lines.append(f"  [{name}] {url!r} expected={expected} dfa={d} nfa={n} regex={r}")
    lines.append("=" * 60)
    report = "\n".join(lines)
    return report, failed == 0, {
        "total": total, "passed": passed, "failed": failed,
        "dfa_nfa_mismatches": dfa_nfa_mismatches,
        "regex_mismatches": regex_mismatches,
    }


if __name__ == "__main__":
    report, ok, stats = run_all()
    print(report)
    import os
    os.makedirs("output", exist_ok=True)
    with open("output/test_output.txt", "w") as f:
        f.write(report + "\n")
    raise SystemExit(0 if ok else 1)
