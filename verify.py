"""
verify.py – Terminal verification of all spec section-8 test cases.
Run from inside the Intermediate-Code-Generator/ directory.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from errors import CompilerError
from lexer import tokenize
from syntax_parser import parse
from code_generator import generate

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"

results = []

def run_case(label: str, source: str, *, expect_error: str | None = None,
             expect_tac: list[str] | None = None):
    """Run one test case and print result."""
    raw_lines = source.splitlines()
    numbered = [(i+1, t) for i, t in enumerate(raw_lines) if t.strip()]

    asts = []
    err_msg = None
    for lineno, text in numbered:
        try:
            tokens = tokenize(text, lineno)
            ast = parse(tokens, lineno)
            asts.append(ast)
        except CompilerError as e:
            err_msg = str(e)
            break

    if expect_error:
        ok = err_msg is not None and expect_error.lower() in err_msg.lower()
        status = PASS if ok else FAIL
        detail = err_msg or "(no error)"
        print(f"[{status}] {label}")
        if not ok:
            print(f"       expected error containing: {expect_error!r}")
            print(f"       got: {detail}")
        results.append(ok)
        return

    if err_msg:
        print(f"[{FAIL}] {label}")
        print(f"       unexpected error: {err_msg}")
        results.append(False)
        return

    tac, quads, trips = generate(asts)

    if expect_tac is not None:
        ok = tac == expect_tac
        status = PASS if ok else FAIL
        print(f"[{status}] {label}")
        if not ok:
            print(f"       expected TAC: {expect_tac}")
            print(f"       got TAC:      {tac}")
        results.append(ok)
    else:
        print(f"[{PASS}] {label}  TAC={tac}")
        results.append(True)


# ---------------------------------------------------------------------------
# Section 8 test cases
# ---------------------------------------------------------------------------

run_case(
    "Example 1: x = a + b * c - d / e",
    "x = a + b * c - d / e",
    expect_tac=[
        "t1 = b * c",
        "t2 = a + t1",
        "t3 = d / e",
        "t4 = t2 - t3",
        "x = t4",
    ],
)

run_case(
    "Example 2: y = -a * (b + c)",
    "y = -a * (b + c)",
    expect_tac=[
        "t1 = uminus a",
        "t2 = b + c",
        "t3 = t1 * t2",
        "y = t3",
    ],
)

run_case(
    "Left-assoc: x = a - b - c",
    "x = a - b - c",
    expect_tac=["t1 = a - b", "t2 = t1 - c", "x = t2"],
)

run_case(
    "Left subtree first: x = (a + b) * (c + d)",
    "x = (a + b) * (c + d)",
    expect_tac=["t1 = a + b", "t2 = c + d", "t3 = t1 * t2", "x = t3"],
)

run_case(
    "No temporaries: x = 5",
    "x = 5",
    expect_tac=["x = 5"],
)

run_case(
    "Bare expression: a + b",
    "a + b",
    expect_tac=["t1 = a + b"],
)

run_case(
    "Two lines (p=a+b, q=p*2)",
    "p = a + b\nq = p * 2",
    expect_tac=["t1 = a + b", "p = t1", "t2 = p * 2", "q = t2"],
)

run_case(
    "Name collision: t1 = a + b * c",
    "t1 = a + b * c",
    expect_tac=["t2 = b * c", "t3 = a + t2", "t1 = t3"],
)

run_case(
    "Blank lines between statements",
    "p = a + b\n\n\nq = p * 2",
    expect_tac=["t1 = a + b", "p = t1", "t2 = p * 2", "q = t2"],
)

run_case(
    "Error: x = a + * b",
    "x = a + * b",
    expect_error="Expected expression but found '*'",
)

run_case(
    "Error: x = (a + b",
    "x = (a + b",
    expect_error="Expected ')' but found end of line",
)

run_case(
    "Error: x = a b",
    "x = a b",
    expect_error="Unexpected token 'b'",
)

run_case(
    "Error: x = a +",
    "x = a +",
    expect_error="Expected expression but found end of line",
)

run_case(
    "Error: 5 = x",
    "5 = x",
    expect_error="Unexpected token '='",
)

run_case(
    "Error: x = y = 5",
    "x = y = 5",
    expect_error="Unexpected token '='",
)

run_case(
    "Error: x = 5 @ 3  (lexical @)",
    "x = 5 @ 3",
    expect_error="Unexpected character '@'",
)

run_case(
    "Error: x = a;  (lexical ;)",
    "x = a;",
    expect_error="Unexpected character ';'",
)

run_case(
    "Empty input (no non-blank lines)",
    "   \n\n  ",
    # No asts → no instructions → tac == []
    expect_tac=[],
)

# ---------------------------------------------------------------------------
print()
total = len(results)
passed = sum(results)
print(f"Results: {passed}/{total} passed")
if passed == total:
    print("All tests PASSED!")
else:
    print(f"{total - passed} test(s) FAILED.")
