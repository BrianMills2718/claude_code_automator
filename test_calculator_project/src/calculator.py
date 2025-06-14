"""Calculator module with basic arithmetic operations."""

from typing import Union


Number = Union[int, float]


class Calculator:
    """Calculator with basic arithmetic operations."""

    @staticmethod
    def add(a: Number, b: Number) -> Number:
        """Add two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            Sum of a and b
        """
        return a + b

    @staticmethod
    def subtract(a: Number, b: Number) -> Number:
        """Subtract b from a.

        Args:
            a: Number to subtract from
            b: Number to subtract

        Returns:
            Difference of a - b
        """
        return a - b

    @staticmethod
    def multiply(a: Number, b: Number) -> Number:
        """Multiply two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            Product of a * b
        """
        return a * b

    @staticmethod
    def divide(a: Number, b: Number) -> Number:
        """Divide a by b.

        Args:
            a: Dividend
            b: Divisor

        Returns:
            Quotient of a / b

        Raises:
            ValueError: If b is zero
        """
        if b == 0:
            raise ValueError(f"Cannot divide by zero: {a} / {b}")
        return a / b
