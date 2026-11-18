"""
syntax_parser.py – Recursive-descent parser for the Intermediate Code Generator.

Grammar (EBNF, one statement per call):

    statement  → IDENTIFIER '=' expression
               | expression
    expression → term ( ( '+' | '-' ) term )*
    term       → unary ( ( '*' | '/' ) unary )*
    unary      → '-' unary | primary
    primary    → NUMBER | IDENTIFIER | '(' expression ')'

Public API
----------
parse(tokens: list[Token], line_number: int) -> ASTNode
    Returns the root AST node for one line, or raises CompilerError
    with stage="Syntax".
"""

from __future__ import annotations

from typing import List, Optional

from lexer import Token, TT_IDENTIFIER, TT_NUMBER, TT_PLUS, TT_MINUS
from lexer import TT_MULTIPLY, TT_DIVIDE, TT_ASSIGN, TT_LPAREN, TT_RPAREN, TT_EOF
from ast_nodes import ASTNode, Assign, BinaryOp, UnaryOp, Number, Identifier
from errors import CompilerError


class Parser:
    """
    Stateful recursive-descent parser for a single line's token list.
    """

    def __init__(self, tokens: List[Token], line_number: int) -> None:
        self._tokens: List[Token] = tokens
        self._pos:    int         = 0
        self._line:   int         = line_number

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    def _peek(self) -> Token:
        """Return the current token without consuming it."""
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        """Consume and return the current token."""
        tok = self._tokens[self._pos]
        if tok.type != TT_EOF:
            self._pos += 1
        return tok

    def _check(self, *types: str) -> bool:
        """True if the current token's type is one of *types*."""
        return self._peek().type in types

    def _match(self, *types: str) -> Optional[Token]:
        """
        If the current token matches one of *types*, consume and return it.
        Otherwise return None.
        """
        if self._check(*types):
            return self._advance()
        return None

    def _expect(self, type_: str, description: str) -> Token:
        """
        Consume the current token if it has type *type_*.
        Raise a syntax error if it does not.

        *description* is the human-readable name used in the error message
        (e.g.  "')'"  or  "')'").
        """
        tok = self._peek()
        if tok.type == type_:
            return self._advance()
        found = self._describe(tok)
        raise CompilerError(
            message=f"Expected {description} but found {found}",
            line=self._line,
            column=tok.column,
            stage="Syntax",
        )

    @staticmethod
    def _describe(tok: Token) -> str:
        """Human-readable description of a token for error messages."""
        if tok.type == TT_EOF:
            return "end of line"
        return f"'{tok.value}'"

    # ------------------------------------------------------------------
    # Grammar rules (one method per rule)
    # ------------------------------------------------------------------

    def statement(self) -> ASTNode:
        """
        statement → IDENTIFIER '=' expression
                  | expression

        Two-token lookahead: if tokens[pos] is IDENTIFIER and
        tokens[pos+1] is ASSIGN, parse an assignment; otherwise parse a
        bare expression.
        """
        # Two-token look-ahead
        t0 = self._tokens[self._pos]
        t1 = self._tokens[self._pos + 1] if self._pos + 1 < len(self._tokens) else t0

        if t0.type == TT_IDENTIFIER and t1.type == TT_ASSIGN:
            # Assignment form
            name_tok = self._advance()   # consume IDENTIFIER
            self._advance()              # consume '='
            value = self.expression()
            node: ASTNode = Assign(target=name_tok.value, value=value)
        else:
            # Bare expression
            node = self.expression()

        # After parsing the statement the very next token must be EOF.
        nxt = self._peek()
        if nxt.type != TT_EOF:
            raise CompilerError(
                message=f"Unexpected token '{nxt.value}'",
                line=self._line,
                column=nxt.column,
                stage="Syntax",
            )

        return node

    def expression(self) -> ASTNode:
        """
        expression → term ( ( '+' | '-' ) term )*
        Left-associative.
        """
        node = self.term()
        while True:
            op_tok = self._match(TT_PLUS, TT_MINUS)
            if op_tok is None:
                break
            right = self.term()
            node = BinaryOp(op=op_tok.value, left=node, right=right)
        return node

    def term(self) -> ASTNode:
        """
        term → unary ( ( '*' | '/' ) unary )*
        Left-associative.
        """
        node = self.unary()
        while True:
            op_tok = self._match(TT_MULTIPLY, TT_DIVIDE)
            if op_tok is None:
                break
            right = self.unary()
            node = BinaryOp(op=op_tok.value, left=node, right=right)
        return node

    def unary(self) -> ASTNode:
        """
        unary → '-' unary | primary
        """
        op_tok = self._match(TT_MINUS)
        if op_tok is not None:
            operand = self.unary()
            return UnaryOp(op="-", operand=operand)
        return self.primary()

    def primary(self) -> ASTNode:
        """
        primary → NUMBER | IDENTIFIER | '(' expression ')'
        """
        tok = self._peek()

        if tok.type == TT_NUMBER:
            self._advance()
            return Number(value=tok.value)

        if tok.type == TT_IDENTIFIER:
            self._advance()
            return Identifier(name=tok.value)

        if tok.type == TT_LPAREN:
            self._advance()           # consume '('
            inner = self.expression()
            self._expect(TT_RPAREN, "')'")
            return inner              # parentheses affect shape, not nodes

        # Nothing matched – report a meaningful error.
        found = self._describe(tok)
        raise CompilerError(
            message=f"Expected expression but found {found}",
            line=self._line,
            column=tok.column,
            stage="Syntax",
        )


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def parse(tokens: List[Token], line_number: int) -> ASTNode:
    """
    Parse *tokens* (from one source line) and return the root AST node.

    Parameters
    ----------
    tokens      : token list as returned by lexer.tokenize(), including EOF.
    line_number : used only when constructing error objects.

    Raises
    ------
    CompilerError (stage="Syntax") on the first parse error.
    """
    parser = Parser(tokens, line_number)
    return parser.statement()
