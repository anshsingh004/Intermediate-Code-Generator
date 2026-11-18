"""
code_generator.py – AST → Three-Address Code, Quadruples, Triples.

Public API
----------
generate(asts: list[ASTNode]) -> tuple[list[str], list[list], list[list]]

    Parameters
    ----------
    asts : one AST per source line, in order.

    Returns
    -------
    tac        : list of TAC strings, one per instruction.
    quadruples : list of rows [index, op, arg1, arg2, result].
    triples    : list of rows [index, op, arg1, arg2].
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from ast_nodes import ASTNode, Assign, BinaryOp, UnaryOp, Number, Identifier


# ---------------------------------------------------------------------------
# Instruction record
# ---------------------------------------------------------------------------

@dataclass
class Instruction:
    op:     str   # '+', '-', '*', '/', 'uminus', '='
    arg1:   str   # always present
    arg2:   str   # empty string for uminus and copy (=)
    result: str   # destination temporary or variable name


# ---------------------------------------------------------------------------
# Helper: collect every identifier name from a list of ASTs
# ---------------------------------------------------------------------------

def _collect_identifiers(asts: List[ASTNode]) -> Set[str]:
    """
    Walk every AST and return the set of all identifier names found.
    This is used to avoid generating temporaries with the same name as a
    user-defined variable.
    """
    names: Set[str] = set()

    def walk(node: ASTNode) -> None:
        if isinstance(node, Identifier):
            names.add(node.name)
        elif isinstance(node, Assign):
            names.add(node.target)
            walk(node.value)
        elif isinstance(node, BinaryOp):
            walk(node.left)
            walk(node.right)
        elif isinstance(node, UnaryOp):
            walk(node.operand)
        # Number has no identifiers

    for ast in asts:
        walk(ast)
    return names


# ---------------------------------------------------------------------------
# Code generator (stateful – one instance per generate() call)
# ---------------------------------------------------------------------------

class _Generator:
    def __init__(self, reserved: Set[str]) -> None:
        self._reserved:   Set[str]        = reserved   # user identifier names
        self._counter:    int             = 0          # next temporary index to try
        self._instructions: List[Instruction] = []

    # ------------------------------------------------------------------
    # Temporary allocation
    # ------------------------------------------------------------------

    def _new_temp(self) -> str:
        """
        Return the next unused temporary name, skipping any name that
        collides with a user-defined identifier.
        """
        while True:
            self._counter += 1
            name = f"t{self._counter}"
            if name not in self._reserved:
                return name

    # ------------------------------------------------------------------
    # Instruction emission
    # ------------------------------------------------------------------

    def _emit(self, op: str, arg1: str, arg2: str, result: str) -> None:
        self._instructions.append(Instruction(op=op, arg1=arg1, arg2=arg2, result=result))

    # ------------------------------------------------------------------
    # Tree walk (post-order, returns the operand string for the node)
    # ------------------------------------------------------------------

    def _visit(self, node: ASTNode) -> str:
        """
        Recursively generate instructions for *node* and return the
        string operand (variable name, number text, or temporary name)
        that holds the node's value.
        """
        if isinstance(node, Number):
            return node.value                     # no instruction needed

        if isinstance(node, Identifier):
            return node.name                      # no instruction needed

        if isinstance(node, UnaryOp):
            x = self._visit(node.operand)
            t = self._new_temp()
            self._emit("uminus", x, "", t)
            return t

        if isinstance(node, BinaryOp):
            left  = self._visit(node.left)        # left child first (spec 5.5)
            right = self._visit(node.right)
            t = self._new_temp()
            self._emit(node.op, left, right, t)
            return t

        if isinstance(node, Assign):
            v = self._visit(node.value)
            # Always emit the copy instruction (textbook style).
            self._emit("=", v, "", node.target)
            return node.target                    # result is the variable itself

        raise TypeError(f"Unknown AST node type: {type(node)}")   # pragma: no cover

    def process(self, asts: List[ASTNode]) -> None:
        for ast in asts:
            self._visit(ast)

    @property
    def instructions(self) -> List[Instruction]:
        return self._instructions


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def _build_tac(instructions: List[Instruction]) -> List[str]:
    """
    Convert instruction list to Three-Address Code strings.

      binary : result = arg1 op arg2       e.g. "t1 = b * c"
      uminus : result = uminus arg1        e.g. "t1 = uminus a"
      copy   : result = arg1               e.g. "x = t3"
    """
    lines: List[str] = []
    for ins in instructions:
        if ins.op == "=":
            lines.append(f"{ins.result} = {ins.arg1}")
        elif ins.op == "uminus":
            lines.append(f"{ins.result} = uminus {ins.arg1}")
        else:
            lines.append(f"{ins.result} = {ins.arg1} {ins.op} {ins.arg2}")
    return lines


def _build_quadruples(instructions: List[Instruction]) -> List[List]:
    """
    Return rows of [index, op, arg1, arg2, result].
    Empty fields are represented as the empty string "".
    """
    rows: List[List] = []
    for idx, ins in enumerate(instructions):
        rows.append([idx, ins.op, ins.arg1, ins.arg2, ins.result])
    return rows


def _build_triples(instructions: List[Instruction]) -> List[List]:
    """
    Return rows of [index, op, arg1, arg2].

    Rules:
    - Build a map: temporary_name → instruction_index (the index of the
      instruction that *produced* that temporary).
    - For each instruction, replace any operand that is a temporary name
      with "(index)" of its producer.
    - uminus: arg2 is blank.
    - Assignment is special: row is  =, target_variable, (index-or-value).
      (Opposite orientation from the quadruple.)
    """
    # Map: temp_name → instruction index that produced it.
    temp_producer: Dict[str, int] = {}
    for idx, ins in enumerate(instructions):
        # Only temporaries (starts with 't' followed by digits) are tracked,
        # but to be safe we track any result that is NOT a plain user var.
        # Actually, per the spec we track every result that could be a temp.
        # We use a simple heuristic: the result is a temporary if it starts
        # with 't' and the rest are digits AND was not a user assignment target.
        # Cleaner: track every result unconditionally; the replacement step
        # only fires when the operand is in this map.
        if ins.op != "=":           # copy instructions store into user vars
            temp_producer[ins.result] = idx
        # For copy instructions the result is a user var – we do NOT track it
        # because the triple for the assignment row refers to it by name.

    def resolve(operand: str) -> str:
        """Replace a temporary name with (index) if it was produced by an earlier instruction."""
        if operand in temp_producer:
            return f"({temp_producer[operand]})"
        return operand

    rows: List[List] = []
    for idx, ins in enumerate(instructions):
        if ins.op == "=":
            # Assignment triple: op='=', arg1=target, arg2=resolved(value)
            a1 = ins.result          # target variable
            a2 = resolve(ins.arg1)   # the value (may be a temp ref)
            rows.append([idx, ins.op, a1, a2])
        elif ins.op == "uminus":
            a1 = resolve(ins.arg1)
            rows.append([idx, ins.op, a1, ""])
        else:
            a1 = resolve(ins.arg1)
            a2 = resolve(ins.arg2)
            rows.append([idx, ins.op, a1, a2])

    return rows


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def generate(
    asts: List[ASTNode],
) -> Tuple[List[str], List[List], List[List]]:
    """
    Generate TAC, quadruples and triples from a list of AST nodes.

    Parameters
    ----------
    asts : one AST per source line, in order.

    Returns
    -------
    (tac, quadruples, triples)
      tac        – list of TAC text lines
      quadruples – list of rows [index, op, arg1, arg2, result]
      triples    – list of rows [index, op, arg1, arg2]
    """
    reserved = _collect_identifiers(asts)

    gen = _Generator(reserved)
    gen.process(asts)
    instructions = gen.instructions

    tac        = _build_tac(instructions)
    quadruples = _build_quadruples(instructions)
    triples    = _build_triples(instructions)

    return tac, quadruples, triples
