"""
ast_nodes.py – AST node classes for the Intermediate Code Generator.

Five node types:
  Assign     – assignment statement  (target: str, value: ASTNode)
  BinaryOp   – binary operation      (op: str, left: ASTNode, right: ASTNode)
  UnaryOp    – unary minus            (op: str, operand: ASTNode)
  Number     – numeric literal        (value: str)
  Identifier – variable reference     (name: str)

Parentheses never appear as nodes; they only affect tree shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union


# A recursive type alias for any AST node.
ASTNode = Union["Assign", "BinaryOp", "UnaryOp", "Number", "Identifier"]


@dataclass
class Assign:
    """
    An assignment statement:  target = value
    """
    target: str      # the identifier on the left-hand side
    value:  ASTNode  # the expression on the right-hand side


@dataclass
class BinaryOp:
    """
    A binary arithmetic operation:  left op right
    op is one of  '+', '-', '*', '/'
    """
    op:    str
    left:  ASTNode
    right: ASTNode


@dataclass
class UnaryOp:
    """
    A unary minus:  -operand
    op is always '-'
    """
    op:      str
    operand: ASTNode


@dataclass
class Number:
    """
    A numeric literal.  value is the raw text as typed (e.g. '42' or '3.14').
    """
    value: str


@dataclass
class Identifier:
    """
    A variable reference.  name is the identifier text.
    """
    name: str
