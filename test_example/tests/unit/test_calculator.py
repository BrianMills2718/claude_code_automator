"""Unit tests for calculator module."""

import pytest
from src.calculator import add, subtract, multiply, divide


class TestAdd:
    """Test cases for addition function."""
    
    def test_add_positive_numbers(self) -> None:
        """Test adding positive numbers."""
        assert add(2, 3) == 5
        assert add(10, 15) == 25
    
    def test_add_negative_numbers(self) -> None:
        """Test adding negative numbers."""
        assert add(-2, -3) == -5
        assert add(-10, -15) == -25
    
    def test_add_mixed_numbers(self) -> None:
        """Test adding positive and negative numbers."""
        assert add(5, -3) == 2
        assert add(-5, 3) == -2
    
    def test_add_zero(self) -> None:
        """Test adding zero."""
        assert add(5, 0) == 5
        assert add(0, 5) == 5
        assert add(0, 0) == 0
    
    def test_add_floats(self) -> None:
        """Test adding floating point numbers."""
        assert add(2.5, 3.7) == pytest.approx(6.2)
        assert add(-1.5, 2.5) == pytest.approx(1.0)


class TestSubtract:
    """Test cases for subtraction function."""
    
    def test_subtract_positive_numbers(self) -> None:
        """Test subtracting positive numbers."""
        assert subtract(5, 3) == 2
        assert subtract(10, 4) == 6
    
    def test_subtract_negative_numbers(self) -> None:
        """Test subtracting negative numbers."""
        assert subtract(-5, -3) == -2
        assert subtract(-2, -8) == 6
    
    def test_subtract_mixed_numbers(self) -> None:
        """Test subtracting mixed positive and negative numbers."""
        assert subtract(5, -3) == 8
        assert subtract(-5, 3) == -8
    
    def test_subtract_zero(self) -> None:
        """Test subtracting zero."""
        assert subtract(5, 0) == 5
        assert subtract(0, 5) == -5
        assert subtract(0, 0) == 0
    
    def test_subtract_floats(self) -> None:
        """Test subtracting floating point numbers."""
        assert subtract(5.5, 2.3) == pytest.approx(3.2)
        assert subtract(-1.5, -2.5) == pytest.approx(1.0)


class TestMultiply:
    """Test cases for multiplication function."""
    
    def test_multiply_positive_numbers(self) -> None:
        """Test multiplying positive numbers."""
        assert multiply(3, 4) == 12
        assert multiply(5, 6) == 30
    
    def test_multiply_negative_numbers(self) -> None:
        """Test multiplying negative numbers."""
        assert multiply(-3, -4) == 12
        assert multiply(-2, -5) == 10
    
    def test_multiply_mixed_numbers(self) -> None:
        """Test multiplying positive and negative numbers."""
        assert multiply(3, -4) == -12
        assert multiply(-3, 4) == -12
    
    def test_multiply_by_zero(self) -> None:
        """Test multiplying by zero."""
        assert multiply(5, 0) == 0
        assert multiply(0, 5) == 0
        assert multiply(0, 0) == 0
    
    def test_multiply_by_one(self) -> None:
        """Test multiplying by one."""
        assert multiply(5, 1) == 5
        assert multiply(1, 5) == 5
        assert multiply(-5, 1) == -5
    
    def test_multiply_floats(self) -> None:
        """Test multiplying floating point numbers."""
        assert multiply(2.5, 4.0) == pytest.approx(10.0)
        assert multiply(-1.5, 2.0) == pytest.approx(-3.0)


class TestDivide:
    """Test cases for division function."""
    
    def test_divide_positive_numbers(self) -> None:
        """Test dividing positive numbers."""
        assert divide(10, 2) == 5
        assert divide(15, 3) == 5
    
    def test_divide_negative_numbers(self) -> None:
        """Test dividing negative numbers."""
        assert divide(-10, -2) == 5
        assert divide(-15, -3) == 5
    
    def test_divide_mixed_numbers(self) -> None:
        """Test dividing mixed positive and negative numbers."""
        assert divide(10, -2) == -5
        assert divide(-10, 2) == -5
    
    def test_divide_by_one(self) -> None:
        """Test dividing by one."""
        assert divide(5, 1) == 5
        assert divide(-5, 1) == -5
    
    def test_divide_zero_by_number(self) -> None:
        """Test dividing zero by a number."""
        assert divide(0, 5) == 0
        assert divide(0, -5) == 0
    
    def test_divide_by_zero_raises_error(self) -> None:
        """Test that dividing by zero raises ValueError."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(5, 0)
        
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(-5, 0)
        
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(0, 0)
    
    def test_divide_floats(self) -> None:
        """Test dividing floating point numbers."""
        assert divide(7.5, 2.5) == pytest.approx(3.0)
        assert divide(-4.5, 1.5) == pytest.approx(-3.0)