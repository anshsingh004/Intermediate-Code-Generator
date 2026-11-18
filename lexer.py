"""
lexer.py – Tokeniser for the Intermediate Code Generator.

Public API
----------
tokenize(line: str, line_number: int) -> list[Token]
    Returns the full token list (including the trailing EOF) for one line of
    source text, or raises CompilerError with stage="Lexical".
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from errors import CompilerError


# ---------------------------------------------------------------------------
# Token types
# ---------------------------------------------------------------------------

TT_IDENTIFIER = "IDENTIFIER"
TT_NUMBER     = "NUMBER"
TT_PLUS       = "PLUS"
TT_MINUS      = "MINUS"
TT_MULTIPLY   = "MULTIPLY"
TT_DIVIDE     = "DIVIDE"
TT_ASSIGN     = "ASSIGN"
TT_LPAREN     = "LPAREN"
TT_RPAREN     = "RPAREN"
TT_EOF        = "EOF"


# ---------------------------------------------------------------------------
# Token dataclass
# ---------------------------------------------------------------------------

@dataclass
class Token:
    type:   str   # one of the TT_* constants
    value:  str   # raw text as it appeared in the source
    column: int   # 1-based position of the first character


# ---------------------------------------------------------------------------
# Master regular expression
# ---------------------------------------------------------------------------
# Groups are listed in priority order.  Whitespace is consumed but yields no
# token.  The NUMBER pattern requires at least one digit before and after the
# decimal point so that "3." and ".5" are rejected (they fall through to the
# MISMATCH group).

_TOKEN_RE = re.compile(
    r"(?P<NUMBER>[0-9]+(?:\.[0-9]+)?)"   # integer or decimal
    r"|(?P<IDENTIFIER>[A-Za-z_]\w*)"     # identifier
    r"|(?P<PLUS>\+)"
    r"|(?P<MINUS>-)"
    r"|(?P<MULTIPLY>\*)"
    r"|(?P<DIVIDE>/)"
    r"|(?P<ASSIGN>=)"
    r"|(?P<LPAREN>\()"
    r"|(?P<RPAREN>\))"
    r"|(?P<WHITESPACE>[ \t]+)"           # skip silently
    r"|(?P<MISMATCH>.)"                  # anything else → lexical error
)


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def tokenize(line: str, line_number: int) -> List[Token]:
    """
    Scan *line* and return a list of Token objects ending with EOF.

    Parameters
    ----------
    line        : one line of source text (no newline character).
    line_number : the 1-based line number within the whole input (used only
                  when constructing error objects).

    Raises
    ------
    CompilerError (stage="Lexical") on the first unrecognised character.
    """
    tokens: List[Token] = []

    for mo in _TOKEN_RE.finditer(line):
        kind   = mo.lastgroup          # name of the matched group
        value  = mo.group()
        column = mo.start() + 1        # convert 0-based offset → 1-based column

        if kind == "WHITESPACE":
            continue
        if kind == "MISMATCH":
            raise CompilerError(
                message=f"Unexpected character '{value}'",
                line=line_number,
                column=column,
                stage="Lexical",
            )

        tokens.append(Token(type=kind, value=value, column=column))

    # Always append EOF at the virtual column just past the end of the line.
    eof_column = len(line) + 1
    tokens.append(Token(type=TT_EOF, value="", column=eof_column))
    return tokens
