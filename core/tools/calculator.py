"""
Calculator Tool
Handles precise mathematical calculations
"""

import re
import ast
import operator
from typing import Dict
from .base import Tool, ToolResult


class CalculatorTool(Tool):
    """
    Safe calculator for mathematical expressions
    Delegates complex/large number calculations to Python
    """

    # Safe operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    def __init__(self):
        super().__init__(
            name="Calculator",
            description="Precise mathematical calculations (arithmetic, percentages, fractions)"
        )

    def can_handle(self, question: str) -> float:
        """
        Detect if question requires calculator
        Returns confidence 0-1
        """
        question_lower = question.lower()

        # Strong indicators (high confidence)
        strong_patterns = [
            r'\d{4,}\s*[×\*x]\s*\d{4,}',  # Large number multiplication
            r'\d+\s*÷\s*\d+',              # Division
            r'\d+\.\d+\s*[+\-×÷\*]',       # Decimals
            r'percentuale|percentage|%',    # Percentages
            r'frazione|fraction|\/\d+',    # Fractions
        ]

        for pattern in strong_patterns:
            if re.search(pattern, question):
                return 0.9  # High confidence

        # Medium indicators
        if re.search(r'\d+\s*[+\-×÷\*]\s*\d+', question):
            # Check if numbers are large or complex
            numbers = re.findall(r'\d+', question)
            if any(int(n) > 1000 for n in numbers if n.isdigit()):
                return 0.7  # Medium-high confidence

        # Weak indicators
        calc_keywords = ['calcola', 'calculate', 'quanto fa', 'how much', 'risultato']
        if any(kw in question_lower for kw in calc_keywords):
            if re.search(r'\d+', question):
                return 0.5  # Medium confidence

        return 0.0  # Cannot handle

    async def execute(self, expression: str = None, **kwargs) -> ToolResult:
        """
        Execute mathematical calculation

        Args:
            expression: Math expression to evaluate (e.g., "12847 * 9283")
        """
        if not expression:
            # Try to extract from question
            question = kwargs.get('question', '')
            expression = self._extract_expression(question)

        if not expression:
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error="No mathematical expression found"
            )

        try:
            # Sanitize and evaluate
            result = self._safe_eval(expression)

            self.update_stats(success=True)

            return ToolResult(
                success=True,
                output=result,
                confidence=1.0,  # Calculator is always confident
                metadata={"expression": expression}
            )

        except Exception as e:
            self.update_stats(success=False)

            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error=f"Calculation error: {str(e)}"
            )

    def _extract_expression(self, text: str) -> str:
        """Extract mathematical expression from text"""
        # Replace common symbols
        text = text.replace('×', '*').replace('÷', '/').replace('x', '*')

        # Find expression pattern
        pattern = r'(\d+\.?\d*)\s*([\+\-\*\/])\s*(\d+\.?\d*)'
        match = re.search(pattern, text)

        if match:
            return f"{match.group(1)} {match.group(2)} {match.group(3)}"

        return ""

    def _safe_eval(self, expr: str) -> float:
        """
        Safely evaluate mathematical expression
        Uses AST parsing to prevent code injection
        """
        try:
            # Parse expression
            node = ast.parse(expr, mode='eval').body

            def _eval_node(node):
                if isinstance(node, ast.Constant):  # Python 3.8+
                    return node.value
                elif isinstance(node, ast.Num):  # Python 3.7
                    return node.n
                elif isinstance(node, ast.BinOp):
                    op_type = type(node.op)
                    if op_type not in self.OPERATORS:
                        raise ValueError(f"Unsupported operator: {op_type}")
                    left = _eval_node(node.left)
                    right = _eval_node(node.right)
                    return self.OPERATORS[op_type](left, right)
                elif isinstance(node, ast.UnaryOp):
                    op_type = type(node.op)
                    if op_type not in self.OPERATORS:
                        raise ValueError(f"Unsupported operator: {op_type}")
                    operand = _eval_node(node.operand)
                    return self.OPERATORS[op_type](operand)
                else:
                    raise ValueError(f"Unsupported node type: {type(node)}")

            result = _eval_node(node)

            # Format result
            if isinstance(result, float) and result.is_integer():
                return int(result)
            return round(result, 2) if isinstance(result, float) else result

        except Exception as e:
            raise ValueError(f"Invalid expression: {expr}") from e
