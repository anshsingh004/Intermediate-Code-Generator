"""
errors.py – Shared exception class for the Intermediate Code Generator.
"""


class CompilerError(Exception):
    """
    Raised by the lexer and parser when they encounter invalid input.

    Attributes
    ----------
    message : str   – human-readable description of what went wrong
    line    : int   – 1-based line number in the original source text
    column  : int   – 1-based column number within that line
    stage   : str   – "Lexical" or "Syntax"
    """

    def __init__(self, message: str, line: int, column: int, stage: str) -> None:
        self.message = message
        self.line = line
        self.column = column
        self.stage = stage
        super().__init__(str(self))

    def __str__(self) -> str:
        return (
            f"{self.stage} Error at line {self.line}, column {self.column}: "
            f"{self.message}"
        )
