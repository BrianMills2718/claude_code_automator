"""Unit tests for calculator module."""

import pytest
from src.calculator import Calculator


class TestCalculator:
    """Test calculator operations."""

    def setup_method(self) -> None:
        """Set up test calculator instance."""
        self.calculator = Calculator()

    def test_add_integers(self) -> None:
        """Test adding two integers."""
        assert self.calculator.add(2, 3) == 5
        assert self.calculator.add(-1, 1) == 0
        assert self.calculator.add(0, 0) == 0

    def test_add_floats(self) -> None:
        """Test adding floating point numbers."""
        assert self.calculator.add(2.5, 3.5) == 6.0
        assert self.calculator.add(-1.5, 1.5) == 0.0
        assert abs(self.calculator.add(0.1, 0.2) - 0.3) < 1e-10

    def test_subtract_integers(self) -> None:
        """Test subtracting integers."""
        assert self.calculator.subtract(5, 3) == 2
        assert self.calculator.subtract(1, 1) == 0
        assert self.calculator.subtract(0, 5) == -5

    def test_subtract_floats(self) -> None:
        """Test subtracting floating point numbers."""
        assert self.calculator.subtract(5.5, 3.5) == 2.0
        assert self.calculator.subtract(1.0, 1.0) == 0.0

    def test_multiply_integers(self) -> None:
        """Test multiplying integers."""
        assert self.calculator.multiply(2, 3) == 6
        assert self.calculator.multiply(5, 0) == 0
        assert self.calculator.multiply(-2, 3) == -6
        assert self.calculator.multiply(-2, -3) == 6

    def test_multiply_floats(self) -> None:
        """Test multiplying floating point numbers."""
        assert self.calculator.multiply(2.5, 2.0) == 5.0
        assert self.calculator.multiply(0.1, 10) == 1.0

    def test_divide_integers(self) -> None:
        """Test dividing integers."""
        assert self.calculator.divide(6, 2) == 3
        assert self.calculator.divide(5, 2) == 2.5
        assert self.calculator.divide(-6, 2) == -3
        assert self.calculator.divide(6, -2) == -3

    def test_divide_floats(self) -> None:
        """Test dividing floating point numbers."""
        assert self.calculator.divide(7.5, 2.5) == 3.0
        assert self.calculator.divide(1.0, 4.0) == 0.25

    def test_divide_by_zero(self) -> None:
        """Test division by zero raises ValueError."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            self.calculator.divide(5, 0)

        with pytest.raises(ValueError, match="Cannot divide by zero"):
            self.calculator.divide(0, 0)
