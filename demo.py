"""
demo.py
=======
Interactive URL automata demo.

Options:
1. Validate URL
2. Show DFA trace
3. Show NFA trace
4. Visualize DFA path
5. Visualize NFA path
6. Exit
"""

import sys

from automata import (
    validate_dfa,
    validate_nfa,
    dfa_trace,
    nfa_trace,
)

from visualizer import (
    save_dfa_visual,
    save_nfa_visual,
)


def print_dfa_trace(url):
    accepted, steps = dfa_trace(url)

    print("\nDFA TRACE")
    print("---------")

    for frm, ch, to in steps:
        print(f"  {frm} --{ch!r}--> {to}")

    print(f"\nResult: {'ACCEPT' if accepted else 'REJECT'}")


def print_nfa_trace(url):
    accepted, history = nfa_trace(url)

    print("\nNFA TRACE")
    print("---------")

    if history:
        print(
            f"  {{{', '.join(sorted(history[0]))}}}"
        )

    for i in range(1, len(history)):
        ch = url[i - 1]
        states = history[i]

        if states:
            label = "{" + ", ".join(sorted(states)) + "}"
        else:
            label = "{}  (dead branch)"

        print(f"  --{ch!r}--> {label}")

    print(f"\nResult: {'ACCEPT' if accepted else 'REJECT'}")


def validate_url():
    url = input("\nEnter URL: ").strip()

    if not url:
        print("URL cannot be empty.")
        return

    dfa_result = validate_dfa(url)
    nfa_result = validate_nfa(url)

    print("\n" + "=" * 40)
    print(f"URL: {url}")
    print("=" * 40)

    print(f"DFA: {'ACCEPT' if dfa_result else 'REJECT'}")
    print(f"NFA: {'ACCEPT' if nfa_result else 'REJECT'}")

    if dfa_result == nfa_result:
        print("Agreement: YES")
    else:
        print("Agreement: NO")


def visualize_dfa():
    url = input("\nEnter URL for DFA visualization: ").strip()

    if not url:
        print("URL cannot be empty.")
        return

    print("\nGenerating DFA visualization...")

    try:
        filename = save_dfa_visual(url)
        print(f"DFA visualization created: {filename}")
        print("Opening it in your browser...")
    except Exception as e:
        print(f"\nCould not generate DFA visualization.")
        print(f"Error: {e}")


def visualize_nfa():
    url = input("\nEnter URL for NFA visualization: ").strip()

    if not url:
        print("URL cannot be empty.")
        return

    print("\nGenerating NFA visualization...")

    try:
        filename = save_nfa_visual(url)
        print(f"NFA visualization created: {filename}")
        print("Opening it in your browser...")
    except Exception as e:
        print(f"\nCould not generate NFA visualization.")
        print(f"Error: {e}")


def show_menu():
    print("\n")
    print("=" * 50)
    print("             URL AUTOMATA VALIDATOR")
    print("=" * 50)
    print()
    print("  1. Validate URL")
    print("  2. Show DFA Trace")
    print("  3. Show NFA Trace")
    print("  4. Visualize DFA Path")
    print("  5. Visualize NFA Path")
    print("  6. Exit")
    print()
    print("=" * 50)


def main():
    trace_mode = "--trace" in sys.argv

    while True:
        show_menu()

        choice = input("Choose an option: ").strip()

        if choice == "1":
            validate_url()

        elif choice == "2":
            url = input("\nEnter URL: ").strip()

            if url:
                print_dfa_trace(url)

        elif choice == "3":
            url = input("\nEnter URL: ").strip()

            if url:
                print_nfa_trace(url)

        elif choice == "4":
            visualize_dfa()

        elif choice == "5":
            visualize_nfa()

        elif choice == "6":
            print("\nGoodbye.")
            break

        else:
            print("\nInvalid option. Please choose 1-6.")


if __name__ == "__main__":
    main()