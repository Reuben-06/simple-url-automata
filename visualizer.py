import os
import html
import webbrowser

from automata import dfa_trace, nfa_trace, nfa_step, NFA_ACCEPTING


# ============================================================
# SHARED HELPERS
# ============================================================

def char_label(ch):
    labels = {
        ":": "COLON (:)",
        "/": "SLASH (/)",
        "\\": "BACKSLASH",
        " ": "SPACE",
        '"': "QUOTE",
        "_": "UNDERSCORE (_)",
        "-": "HYPHEN (-)",
        ".": "DOT (.)",
    }
    return labels.get(ch, ch)


def short_char(ch):
    if ch == " ":
        return "SPACE"
    if ch == "\t":
        return "TAB"
    if ch == "\n":
        return "\\n"
    return ch


# ============================================================
# DFA
# ============================================================

def dfa_id(state):
    if isinstance(state, tuple):
        return "DOM_" + "_".join(
            str(x).replace("-", "_").replace(" ", "_")
            for x in state[1:]
        )
    return str(state).replace("-", "_").replace(" ", "_")


def dfa_state_name(state):
    """
    Human-readable label + actual internal state.
    """

    if not isinstance(state, tuple):
        names = {
            "Q0": ("START", "Q0"),
            "H": ("SCHEME: h", "H"),
            "HT": ("SCHEME: ht", "HT"),
            "HTT": ("SCHEME: htt", "HTT"),
            "HTTP": ("SCHEME: http", "HTTP"),
            "HTTPS": ("SCHEME: https", "HTTPS"),
            "COLON": ("COLON", "COLON"),
            "SLASH1": ("SLASH 1", "SLASH1"),
            "SLASH2": ("DOMAIN START", "SLASH2"),
            "PATH_SEG_START": ("PATH START", "PATH_SEG_START"),
            "PATH_SEG": ("PATH SEGMENT", "PATH_SEG"),
            "DEAD": ("DEAD / REJECT", "DEAD"),
        }

        title, actual = names.get(
            str(state),
            (str(state), str(state))
        )

        return f"{title}\\n[{actual}]"

    _, status, trie_node, seen_dot = state

    dot_text = "dot seen" if seen_dot else "no dot"

    if status == "START":
        title = "DOMAIN LABEL START"

    elif status == "OK":
        if trie_node == "X":
            title = "DOMAIN LABEL"
        else:
            title = f"DOMAIN / TLD PREFIX {trie_node}"

    elif status == "HYP":
        title = "DOMAIN AFTER HYPHEN"

    else:
        title = "DOMAIN"

    actual = f"DOM,{status},{trie_node},{seen_dot}"

    return f"{title}\\n[{actual}]\\n{dot_text}"


def dfa_class(state):
    if isinstance(state, tuple):
        _, status, trie_node, _ = state

        if status == "HYP":
            return "warning"

        if status == "START":
            return "domainStart"

        if trie_node != "X":
            return "tld"

        return "domain"

    if state == "Q0":
        return "start"

    if state in {
        "H", "HT", "HTT", "HTTP", "HTTPS",
        "COLON", "SLASH1"
    }:
        return "protocol"

    if state == "SLASH2":
        return "domainStart"

    if state in {
        "PATH_SEG_START",
        "PATH_SEG"
    }:
        return "path"

    if state == "DEAD":
        return "reject"

    return "normal"


def generate_dfa_visual(url):
    accepted, steps = dfa_trace(url)

    lines = [
        "stateDiagram-v2",
        "    direction TB",
        "",
    ]

    states = []

    for frm, _, to in steps:
        states.extend([frm, to])

    if not states:
        states = ["Q0"]

    unique = []

    for state in states:
        if state not in unique:
            unique.append(state)

    # Declare states
    for state in unique:
        lines.append(
            f'    state "{dfa_state_name(state)}" as {dfa_id(state)}'
        )

    lines += [
        "",
        f"    [*] --> {dfa_id(unique[0])}",
        "",
    ]

    # Actual transitions for THIS URL
    for index, (frm, ch, to) in enumerate(steps, start=1):
        label = short_char(ch)

        lines.append(
            f"    {dfa_id(frm)} --> {dfa_id(to)}: "
            f"{index}. '{label}'"
        )

    final = steps[-1][2] if steps else "Q0"
    final_id = dfa_id(final)

    if accepted:
        lines += [
            "",
            f"    {final_id} --> ACCEPT",
            '    state "✓ ACCEPT\\nInput fully consumed" as ACCEPT',
        ]
    else:
        lines += [
            "",
            f"    {final_id} --> REJECT",
            '    state "✗ REJECT\\nInvalid transition / final state" as REJECT',
        ]

    # Styling
    lines += [
        "",
        "    classDef start fill:#e0f2fe,stroke:#0284c7,stroke-width:3px,color:#082f49",
        "    classDef protocol fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#0f172a",
        "    classDef domainStart fill:#fff7ed,stroke:#ea580c,stroke-width:3px,color:#7c2d12",
        "    classDef domain fill:#fffbeb,stroke:#d97706,stroke-width:2px,color:#78350f",
        "    classDef tld fill:#fef3c7,stroke:#b45309,stroke-width:3px,color:#78350f",
        "    classDef warning fill:#fef2f2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d",
        "    classDef path fill:#eef2ff,stroke:#4f46e5,stroke-width:2px,color:#312e81",
        "    classDef normal fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#0f172a",
        "    classDef accept fill:#dcfce7,stroke:#16a34a,stroke-width:4px,color:#14532d",
        "    classDef reject fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#7f1d1d",
        "",
    ]

    for state in unique:
        lines.append(
            f"    class {dfa_id(state)} {dfa_class(state)}"
        )

    lines.append(
        f"    class {'ACCEPT' if accepted else 'REJECT'} "
        f"{'accept' if accepted else 'reject'}"
    )

    return "\n".join(lines)


# ============================================================
# NFA
# ============================================================

def nfa_id(step, state):
    safe = "".join(
        c if c.isalnum() else "_"
        for c in str(state)
    )

    return f"N{step}_{safe}"


def nfa_state_name(state):
    """
    Show both descriptive label and actual NFA state.
    """

    names = {
        "q0": "START",
        "h": "SCHEME: h",
        "ht": "SCHEME: ht",
        "htt": "SCHEME: htt",
        "http": "SCHEME: http",
        "https": "SCHEME: https",
        "colon": "COLON",
        "slash1": "DOMAIN START",
        "g_start": "GENERIC LABEL START",
        "g_start_dot": "AFTER DOMAIN DOT",
        "G_OK": "GENERIC DOMAIN LABEL",
        "G_HYP": "DOMAIN AFTER HYPHEN",
        "PATH_SEG_START": "PATH START",
        "PATH_SEG_START_ACCEPTING": "PATH START / ACCEPTING",
        "PATH_SEG": "PATH SEGMENT",
    }

    if state in names:
        return f"{names[state]}\\n[{state}]"

    state_text = str(state)

    if state_text.startswith("T1_"):
        return f"FIRST-LABEL TLD CANDIDATE\\n[{state}]"

    if state_text.startswith("T"):
        return f"TLD CANDIDATE\\n[{state}]"

    return f"{state}\\n[{state}]"


def nfa_class(state):
    if state == "q0":
        return "start"

    if state in {
        "h", "ht", "htt", "http",
        "https", "colon"
    }:
        return "protocol"

    if state == "slash1":
        return "domainStart"

    if state in {
        "g_start",
        "g_start_dot",
        "G_OK",
        "G_HYP",
    }:
        return "domain"

    if str(state).startswith("T"):
        return "branch"

    if state in {
        "PATH_SEG_START",
        "PATH_SEG_START_ACCEPTING",
        "PATH_SEG",
    }:
        return "path"

    return "normal"


def generate_nfa_visual(url):
    accepted, history = nfa_trace(url)

    lines = [
        "stateDiagram-v2",
        "    direction TB",
        "",
    ]

    # Declare every state at every execution step.
    # This ensures the diagram is unique for EACH URL.
    for step, active_states in enumerate(history):

        if not active_states:
            lines.append(
                f'    state "NO ACTIVE STATES\\n[step {step}]" '
                f'as N{step}_EMPTY'
            )
            continue

        for state in sorted(active_states):

            label = (
                f"{nfa_state_name(state)}"
                f"\\nstep {step}"
            )

            lines.append(
                f'    state "{label}" as '
                f'{nfa_id(step, state)}'
            )

    lines.append("")

    if history and history[0]:
        first = sorted(history[0])[0]

        lines.append(
            f"    [*] --> {nfa_id(0, first)}"
        )

    lines.append("")

    # Actual NFA transitions for THIS URL
    for step in range(len(history) - 1):

        current = history[step]
        nxt = history[step + 1]

        ch = url[step]

        for source in sorted(current):

            destinations = (
                nfa_step(source, ch)
                .intersection(nxt)
            )

            for destination in sorted(destinations):

                lines.append(
                    f"    {nfa_id(step, source)} --> "
                    f"{nfa_id(step + 1, destination)}: "
                    f"{step + 1}. '{short_char(ch)}'"
                )

    lines.append("")

    if history:

        final = history[-1]
        final_step = len(history) - 1

        accepting = final.intersection(
            NFA_ACCEPTING
        )

        if accepting:

            for state in sorted(accepting):
                lines.append(
                    f"    {nfa_id(final_step, state)} --> ACCEPT"
                )

            lines.append(
                '    state "✓ ACCEPT\\nAt least one active state accepts" '
                'as ACCEPT'
            )

        elif final:

            for state in sorted(final):
                lines.append(
                    f"    {nfa_id(final_step, state)} --> REJECT"
                )

            lines.append(
                '    state "✗ REJECT\\nNo active accepting state" '
                'as REJECT'
            )

        else:

            lines.append(
                f"    N{final_step}_EMPTY --> REJECT"
            )

            lines.append(
                '    state "✗ REJECT\\nAll branches died" '
                'as REJECT'
            )

    lines += [
        "",
        "    classDef start fill:#ecfdf5,stroke:#059669,stroke-width:3px,color:#064e3b",
        "    classDef protocol fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#0f172a",
        "    classDef domainStart fill:#fff7ed,stroke:#ea580c,stroke-width:3px,color:#7c2d12",
        "    classDef domain fill:#fffbeb,stroke:#d97706,stroke-width:2px,color:#78350f",
        "    classDef branch fill:#fdf2f8,stroke:#db2777,stroke-width:3px,color:#831843",
        "    classDef path fill:#eef2ff,stroke:#4f46e5,stroke-width:2px,color:#312e81",
        "    classDef normal fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#0f172a",
        "    classDef accept fill:#dcfce7,stroke:#16a34a,stroke-width:4px,color:#14532d",
        "    classDef reject fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#7f1d1d",
        "",
    ]

    for step, active_states in enumerate(history):
        for state in active_states:
            lines.append(
                f"    class {nfa_id(step, state)} "
                f"{nfa_class(state)}"
            )

    lines.append(
        f"    class {'ACCEPT' if accepted else 'REJECT'} "
        f"{'accept' if accepted else 'reject'}"
    )

    return "\n".join(lines)


# ============================================================
# TRANSITION SUMMARY
# ============================================================

def build_dfa_transition_summary(url):
    accepted, steps = dfa_trace(url)

    rows = []

    for i, (frm, ch, to) in enumerate(steps, 1):

        rows.append(
            f"""
            <tr>
                <td>{i}</td>
                <td><code>{html.escape(short_char(ch))}</code></td>
                <td><code>{html.escape(str(frm))}</code></td>
                <td>→</td>
                <td><code>{html.escape(str(to))}</code></td>
            </tr>
            """
        )

    return "".join(rows), accepted


def build_nfa_transition_summary(url):
    accepted, history = nfa_trace(url)

    rows = []

    for step in range(len(history) - 1):

        ch = url[step]

        before = ", ".join(
            str(s) for s in sorted(history[step])
        ) or "∅"

        after = ", ".join(
            str(s) for s in sorted(history[step + 1])
        ) or "∅"

        rows.append(
            f"""
            <tr>
                <td>{step + 1}</td>
                <td><code>{html.escape(short_char(ch))}</code></td>
                <td><code>{{{html.escape(before)}}}</code></td>
                <td>→</td>
                <td><code>{{{html.escape(after)}}}</code></td>
            </tr>
            """
        )

    return "".join(rows), accepted


# ============================================================
# BROWSER DISPLAY
# ============================================================

def open_mermaid_diagram(
    mmd_filename,
    title,
    url,
    mode,
):

    with open(
        mmd_filename,
        "r",
        encoding="utf-8"
    ) as file:
        code = file.read()

    safe_code = (
        code
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )

    if mode == "DFA":
        transition_rows, accepted = (
            build_dfa_transition_summary(url)
        )

        description = (
            "One current state is followed at every step."
        )

        transition_heading = (
            "DFA Transition Trace"
        )

    else:
        transition_rows, accepted = (
            build_nfa_transition_summary(url)
        )

        description = (
            "The active-state set may contain multiple states "
            "when nondeterministic branching occurs."
        )

        transition_heading = (
            "NFA Active-State Transition Trace"
        )

    result_class = (
        "accepted" if accepted else "rejected"
    )

    result_text = (
        "ACCEPTED" if accepted else "REJECTED"
    )

    escaped_url = html.escape(url)

    html_page = f"""<!doctype html>
<html lang="en">

<head>

<meta charset="utf-8">

<meta
    name="viewport"
    content="width=device-width,initial-scale=1"
>

<title>{title}</title>

<script type="module">

import mermaid from
"https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";

mermaid.initialize({{
    startOnLoad: true,
    theme: "base",
    securityLevel: "loose",

    themeVariables: {{
        fontFamily: "Inter, Arial, sans-serif",
        fontSize: "16px",

        primaryColor: "#ffffff",
        primaryTextColor: "#0f172a",
        primaryBorderColor: "#64748b",

        lineColor: "#475569",

        secondaryColor: "#f8fafc",
        tertiaryColor: "#f1f5f9",

        background: "#f8fafc"
    }},

    state: {{
        useMaxWidth: false
    }}
}});

</script>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background: #f1f5f9;
    color: #0f172a;
    font-family:
        Inter,
        "Segoe UI",
        Arial,
        sans-serif;
}}

.page {{
    width: min(1500px, calc(100% - 40px));
    margin: auto;
    padding: 40px 0 60px;
}}

.topbar {{
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 28px;
}}

.eyebrow {{
    color: #64748b;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
}}

h1 {{
    margin: 6px 0 0;
    font-size: clamp(28px, 4vw, 48px);
    line-height: 1.05;
    letter-spacing: -.03em;
}}

.subtitle {{
    color: #64748b;
    margin-top: 10px;
    font-size: 15px;
}}

.result {{
    padding: 10px 16px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: .07em;
}}

.result.accepted {{
    background: #dcfce7;
    color: #166534;
}}

.result.rejected {{
    background: #fee2e2;
    color: #991b1b;
}}

.url-card {{
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 18px 20px;
    margin-bottom: 18px;
}}

.url-label {{
    font-size: 12px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: .08em;
    margin-bottom: 7px;
}}

.url {{
    font-family:
        "Cascadia Code",
        Consolas,
        monospace;

    font-size: 17px;
    overflow-wrap: anywhere;
}}

.workspace {{
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 32px;
    overflow: auto;
}}

.workspace-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 24px;
}}

.workspace-title {{
    font-weight: 700;
    font-size: 17px;
}}

.workspace-note {{
    font-size: 13px;
    color: #64748b;
}}

.mermaid {{
    display: flex;
    justify-content: center;
    min-width: max-content;
}}

.section {{
    margin-top: 22px;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    overflow: hidden;
}}

.section-header {{
    padding: 18px 22px;
    border-bottom: 1px solid #e2e8f0;
}}

.section-header h2 {{
    margin: 0;
    font-size: 17px;
}}

.section-header p {{
    margin: 5px 0 0;
    font-size: 13px;
    color: #64748b;
}}

.table-wrap {{
    overflow-x: auto;
}}

table {{
    width: 100%;
    border-collapse: collapse;
}}

th {{
    text-align: left;
    font-size: 11px;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: #64748b;
    background: #f8fafc;
}}

th,
td {{
    padding: 12px 16px;
    border-bottom: 1px solid #e2e8f0;
}}

td {{
    font-size: 13px;
}}

tr:last-child td {{
    border-bottom: none;
}}

code {{
    font-family:
        "Cascadia Code",
        Consolas,
        monospace;

    background: #f1f5f9;
    padding: 2px 5px;
    border-radius: 5px;
}}

.legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px 18px;
    margin-top: 20px;
    color: #475569;
    font-size: 12px;
}}

.legend span {{
    display: flex;
    align-items: center;
    gap: 7px;
}}

.dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
}}

.start-dot {{
    background: #0284c7;
}}

.protocol-dot {{
    background: #64748b;
}}

.domain-dot {{
    background: #d97706;
}}

.branch-dot {{
    background: #db2777;
}}

.path-dot {{
    background: #4f46e5;
}}

.accept-dot {{
    background: #16a34a;
}}

@media (max-width: 700px) {{

    .page {{
        width: min(100% - 18px, 1500px);
        padding-top: 22px;
    }}

    .topbar {{
        align-items: flex-start;
        flex-direction: column;
    }}

    .workspace {{
        padding: 18px;
    }}

}}

</style>

</head>

<body>

<div class="page">

    <div class="topbar">

        <div>

            <div class="eyebrow">
                URL Automata Visualizer
            </div>

            <h1>{title}</h1>

            <div class="subtitle">
                {description}
            </div>

        </div>

        <div class="result {result_class}">
            {result_text}
        </div>

    </div>

    <div class="url-card">

        <div class="url-label">
            Current input
        </div>

        <div class="url">
            {escaped_url}
        </div>

    </div>

    <div class="workspace">

        <div class="workspace-header">

            <div>

                <div class="workspace-title">
                    Actual Execution Path
                </div>

                <div class="workspace-note">
                    Every node and transition below was generated
                    from this URL's real execution trace.
                </div>

            </div>

        </div>

        <pre class="mermaid">{safe_code}</pre>

        <div class="legend">

            <span>
                <i class="dot start-dot"></i>
                Start
            </span>

            <span>
                <i class="dot protocol-dot"></i>
                Protocol
            </span>

            <span>
                <i class="dot domain-dot"></i>
                Domain / TLD
            </span>

            {
                '''
                <span>
                    <i class="dot branch-dot"></i>
                    NFA TLD branch
                </span>
                '''
                if mode == "NFA"
                else ""
            }

            <span>
                <i class="dot path-dot"></i>
                Path
            </span>

            <span>
                <i class="dot accept-dot"></i>
                Accepted
            </span>

        </div>

    </div>

    <div class="section">

        <div class="section-header">

            <h2>{transition_heading}</h2>

            <p>
                Actual internal transition states for this input.
            </p>

        </div>

        <div class="table-wrap">

            <table>

                <thead>

                    <tr>
                        <th>Step</th>
                        <th>Input</th>
                        <th>From / Active Before</th>
                        <th></th>
                        <th>To / Active After</th>
                    </tr>

                </thead>

                <tbody>
                    {transition_rows}
                </tbody>

            </table>

        </div>

    </div>

</div>

</body>

</html>
"""

    html_filename = (
        os.path.splitext(mmd_filename)[0]
        + ".html"
    )

    with open(
        html_filename,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(html_page)

    webbrowser.open(
        "file://" + os.path.abspath(html_filename)
    )

    return html_filename


# ============================================================
# SAVE / OPEN
# ============================================================

def save_dfa_visual(
    url,
    filename="diagrams/dfa_path.mmd"
):

    os.makedirs(
        os.path.dirname(filename) or ".",
        exist_ok=True
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            generate_dfa_visual(url)
        )

    return open_mermaid_diagram(
        filename,
        "DFA Execution",
        url,
        "DFA",
    )


def save_nfa_visual(
    url,
    filename="diagrams/nfa_path.mmd"
):

    os.makedirs(
        os.path.dirname(filename) or ".",
        exist_ok=True
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            generate_nfa_visual(url)
        )

    return open_mermaid_diagram(
        filename,
        "NFA Execution",
        url,
        "NFA",
    )