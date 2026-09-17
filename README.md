\# Simple URL Automata



A simple URL validator built using \*\*DFA and NFA\*\* as part of a Formal Languages and Automata Theory project.



The project takes a restricted form of an HTTP/HTTPS URL and checks whether it belongs to the defined language. Both automata process the same input, and their results are compared with a regular expression implementation.



\## What this project does



\- Validates URLs using a DFA

\- Validates the same URLs using an NFA

\- Cross-checks the result using a regular expression

\- Shows DFA and NFA execution traces

\- Generates DFA/NFA path visualizations

\- Generates transition tables

\- Tests valid and invalid URLs

\- Checks DFA/NFA equivalence



\## URL Format



The validator works with a deliberately restricted URL format:



&#x20;   scheme://domain(.label)\*.tld(/path-segment)\*/?



\### Supported Schemes



\- `http`

\- `https`



The scheme must be written in lowercase.



\### Domain Rules



Domain labels can contain letters, digits and hyphens.



A domain label:



\- Cannot start with a hyphen

\- Cannot end with a hyphen

\- Cannot contain consecutive hyphens



The domain must contain at least two components.



Examples:



&#x20;   example.com

&#x20;   www.google.com



\### Supported TLDs



The following TLDs are supported:



&#x20;   com

&#x20;   org

&#x20;   net

&#x20;   edu

&#x20;   ai



The final TLD must be lowercase.



\### Path Rules



Path segments can contain:



&#x20;   A-Z

&#x20;   a-z

&#x20;   0-9

&#x20;   \_

&#x20;   -



Empty path segments are not allowed.



For example:



&#x20;   https://example.com/test



is valid, while:



&#x20;   https://example.com//test



is rejected.



\## Examples



\### Valid URL



&#x20;   https://www.google.com



Expected result:



&#x20;   DFA: ACCEPT

&#x20;   NFA: ACCEPT

&#x20;   Agreement: YES



\### Invalid URL



&#x20;   https://example.com//test



Expected result:



&#x20;   DFA: REJECT

&#x20;   NFA: REJECT

&#x20;   Agreement: YES



\## Project Structure



&#x20;   simple-url-automata/

&#x20;   │

&#x20;   ├── automata.py

&#x20;   ├── demo.py

&#x20;   ├── tests.py

&#x20;   ├── equivalence.py

&#x20;   ├── gen\_tables.py

&#x20;   ├── visualizer.py

&#x20;   │

&#x20;   ├── README.md

&#x20;   ├── TECHNICAL\_PACKAGE.md

&#x20;   │

&#x20;   ├── diagrams/

&#x20;   │   ├── dfa.mmd

&#x20;   │   ├── dfa\_preview.mmd

&#x20;   │   ├── dfa\_path.mmd

&#x20;   │   ├── dfa\_path.html

&#x20;   │   ├── nfa.mmd

&#x20;   │   ├── nfa\_path.mmd

&#x20;   │   └── nfa\_path.html

&#x20;   │

&#x20;   └── output/

&#x20;       ├── dfa\_transition\_table.txt

&#x20;       ├── nfa\_transition\_table.txt

&#x20;       ├── test\_output.txt

&#x20;       └── equivalence\_output.txt



\## Main Files



\### automata.py



Contains the DFA, NFA and regular expression implementation. This is the main source of the automaton logic.



\### demo.py



Provides the interactive command-line menu for validation, tracing and visualization.



\### visualizer.py



Generates Mermaid diagrams from the actual DFA/NFA execution path.



\### tests.py



Runs the test cases and checks the DFA, NFA and regex results against the expected results.



\### equivalence.py



Checks DFA/NFA equivalence using subset construction and product-state verification.



\### gen\_tables.py



Generates the DFA/NFA transition tables and structural diagrams.



\### TECHNICAL\_PACKAGE.md



Contains the detailed language specification, automaton design and verification details.



\## Requirements



The project uses the Python standard library, so no additional packages are required.



Python 3 is required.



\## Running the Project



Run the main program:



&#x20;   python demo.py



For trace mode:



&#x20;   python demo.py --trace



The menu provides the following options:



&#x20;   1. Validate URL

&#x20;   2. Show DFA Trace

&#x20;   3. Show NFA Trace

&#x20;   4. Visualize DFA Path

&#x20;   5. Visualize NFA Path

&#x20;   6. Exit



\## Testing



Run the test suite:



&#x20;   python tests.py



The current test suite contains:



&#x20;   79 test cases

&#x20;   30 valid

&#x20;   37 invalid

&#x20;   8 boundary

&#x20;   4 Unicode-regression



Result:



&#x20;   79 passed

&#x20;   0 failed



The test output is stored in:



&#x20;   output/test\_output.txt



\## DFA/NFA Equivalence



The project also checks whether the DFA and NFA recognize the same language.



Run:



&#x20;   python equivalence.py



The verification uses:



\- NFA to DFA subset construction

\- Product-state BFS



The current verification produced:



&#x20;   43 reachable subsets

&#x20;   8 accepting subsets

&#x20;   1,462 transitions explored



&#x20;   46 reachable DFA/NFA pairs

&#x20;   46/46 pairs checked

&#x20;   0 mismatches



The result is stored in:



&#x20;   output/equivalence\_output.txt



\## Transition Tables



The transition tables can be generated from the automaton implementation using:



&#x20;   python gen\_tables.py



The generated tables are stored in:



&#x20;   output/dfa\_transition\_table.txt

&#x20;   output/nfa\_transition\_table.txt



The structural DFA and NFA diagrams are also generated from the same implementation.



\## Visualization



The project can generate a visualization of the actual DFA or NFA execution path for a URL.



Run:



&#x20;   python demo.py



Then select:



&#x20;   4. Visualize DFA Path

&#x20;   5. Visualize NFA Path



The visualizer generates Mermaid state diagrams and HTML files in the `diagrams/` folder.



The diagrams are based on the actual execution path of the selected URL.



\## How the Validation Works



The same URL is processed by both automata.



&#x20;   URL

&#x20;    │

&#x20;    ├───────────────┐

&#x20;    │               │

&#x20;    ▼               ▼

&#x20;   DFA              NFA

&#x20;    │               │

&#x20;    ▼               ▼

&#x20;   ACCEPT/REJECT   ACCEPT/REJECT

&#x20;    │               │

&#x20;    └───────┬───────┘

&#x20;            ▼

&#x20;      Compare Results

&#x20;            │

&#x20;            ▼

&#x20;        Agreement



The regular expression implementation is also used as a cross-check during testing.



\## Limitations



This project validates a restricted URL language rather than the complete URL standard.



The following are not supported:



\- Port numbers

\- Userinfo/authentication

\- Query strings

\- Fragments

\- IPv4/IPv6 literal hosts

\- Percent-encoding

\- Internationalized/non-ASCII domain names

\- TLDs outside `com`, `org`, `net`, `edu` and `ai`



The automata perform syntax validation only.



They do not check:



\- Whether a domain exists

\- Whether a server is reachable

\- Whether a webpage exists

\- Whether a URL is safe or malicious



\## Purpose



This project was developed to apply concepts from \*\*Formal Languages and Automata Theory\*\* to a practical URL validation problem.



It demonstrates how the same defined language can be implemented using both a DFA and an NFA, tested against expected results, and checked for equivalence.



For the complete technical specification and design details, see:



&#x20;   TECHNICAL\_PACKAGE.md



\## Author



Formal Languages and Automata Theory Project



Built using Python, DFA, NFA and regular expressions.

