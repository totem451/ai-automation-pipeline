import ast
import operator
from typing import Any

# Mapping of AST node types to safe arithmetic operators
SAFE_OPS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node: ast.AST) -> float:
    """Recursively evaluate an AST node using only safe numeric operations."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPS:
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        try:
            return SAFE_OPS[op_type](left, right)
        except ZeroDivisionError:
            raise ValueError("Division by zero is not allowed.")

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _eval_node(node.operand)
        return SAFE_OPS[op_type](operand)

    # Parenthesised expressions are just their inner node in the AST
    if isinstance(node, ast.Expr):
        return _eval_node(node.value)

    raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def calculate(expression: str) -> str:
    """Evaluate a math expression safely using the AST.

    Only numeric literals and the operators +, -, *, /, //, %, ** are allowed.
    No function calls, attribute access, or identifiers are permitted.

    Args:
        expression: A string containing a mathematical expression, e.g. "2 + 3 * 4".

    Returns:
        A string representation of the numeric result.

    Raises:
        ValueError: If the expression is invalid or contains unsafe constructs.
    """
    expression = expression.strip()
    if not expression:
        raise ValueError("Empty expression provided.")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid mathematical expression: {exc}") from exc

    result = _eval_node(tree.body)

    # Return integer representation when the result is a whole number
    if result == int(result):
        return str(int(result))
    return str(result)
