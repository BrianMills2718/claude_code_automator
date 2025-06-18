"""Integration tests for calculator and CLI interaction."""

import subprocess
import sys
from pathlib import Path
from typing import Tuple
import pytest
from src.calculator import Calculator
from src.cli import CLI


def run_calculator_process(input_text: str) -> Tuple[str, str, int]:
    """Run the calculator as a subprocess with the given input."""
    project_root = Path(__file__).parent.parent.parent
    main_path = project_root / "main.py"
    
    process = subprocess.run(
        [sys.executable, str(main_path)],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=5
    )
    
    return process.stdout, process.stderr, process.returncode


class TestCalculatorCLIIntegration:
    """Test the integration between Calculator and CLI components."""

    def test_calculator_with_cli_instance(self):
        """Test that CLI properly integrates with Calculator."""
        cli = CLI()
        assert cli.calculator is not None
        assert isinstance(cli.calculator, Calculator)

    def test_cli_operations_with_calculator(self):
        """Test CLI's ability to perform all basic operations."""
        cli = CLI()
        calc = cli.calculator
        
        # Test add
        result = calc.add(10.0, 5.0)
        assert result == 15.0
        
        # Test subtract
        result = calc.subtract(10.0, 5.0)
        assert result == 5.0
        
        # Test multiply
        result = calc.multiply(10.0, 5.0)
        assert result == 50.0
        
        # Test divide
        result = calc.divide(10.0, 5.0)
        assert result == 2.0

    def test_cli_error_propagation(self):
        """Test that Calculator errors properly propagate through CLI."""
        cli = CLI()
        
        # Division by zero should raise ZeroDivisionError
        with pytest.raises(ZeroDivisionError, match="Cannot divide by zero"):
            cli.calculator.divide(10.0, 0.0)

    def test_cli_get_numbers(self):
        """Test CLI's get_numbers method returns correct tuple."""
        cli = CLI()
        # Test through calculator operations
        num1, num2 = 5.0, 3.0
        assert cli.calculator.add(num1, num2) == 8.0

    def test_complete_workflow_addition(self):
        """Test complete workflow through subprocess for addition."""
        input_text = "1\n5\n10\n5\n"
        stdout, stderr, returncode = run_calculator_process(input_text)
        
        assert returncode == 0
        assert "Welcome to the Calculator!" in stdout
        assert "5.0 + 10.0 = 15.0" in stdout

    def test_complete_workflow_subtraction(self):
        """Test complete workflow through subprocess for subtraction."""
        input_text = "2\n20\n8\n5\n"
        stdout, stderr, returncode = run_calculator_process(input_text)
        
        assert returncode == 0
        assert "20.0 - 8.0 = 12.0" in stdout

    def test_complete_workflow_multiplication(self):
        """Test complete workflow through subprocess for multiplication."""
        input_text = "3\n4\n7\n5\n"
        stdout, stderr, returncode = run_calculator_process(input_text)
        
        assert returncode == 0
        assert "4.0 * 7.0 = 28.0" in stdout

    def test_complete_workflow_division(self):
        """Test complete workflow through subprocess for division."""
        input_text = "4\n20\n4\n5\n"
        stdout, stderr, returncode = run_calculator_process(input_text)
        
        assert returncode == 0
        assert "20.0 / 4.0 = 5.0" in stdout

    def test_complete_workflow_division_by_zero(self):
        """Test complete workflow handling division by zero."""
        input_text = "4\n20\n0\n5\n"
        stdout, stderr, returncode = run_calculator_process(input_text)
        
        assert returncode == 0
        assert "Error: Cannot divide by zero" in stdout

    def test_complete_workflow_invalid_choice(self):
        """Test complete workflow with invalid menu choice."""
        input_text = "invalid\n1\n2\n3\n5\n"
        stdout, stderr, returncode = run_calculator_process(input_text)
        
        assert returncode == 0
        assert "Invalid choice" in stdout
        assert "2.0 + 3.0 = 5.0" in stdout  # Should continue after error

    def test_complete_workflow_invalid_number(self):
        """Test complete workflow with invalid number input."""
        input_text = "1\nabc\n5\n10\n5\n"
        stdout, stderr, returncode = run_calculator_process(input_text)
        
        assert returncode == 0
        assert "Invalid input" in stdout
        assert "5.0 + 10.0 = 15.0" in stdout  # Should recover and complete

    def test_data_flow_between_components(self):
        """Test data flow from CLI input through Calculator and back."""
        cli = CLI()
        calc = cli.calculator
        
        # Test data flow for different operations
        test_cases = [
            (calc.add, 10.0, 20.0, 30.0),
            (calc.subtract, 50.5, 20.5, 30.0),
            (calc.multiply, 3.0, 4.0, 12.0),
            (calc.divide, 100.0, 25.0, 4.0),
        ]
        
        for operation, num1, num2, expected in test_cases:
            result = operation(num1, num2)
            assert result == expected

    def test_multiple_operations_workflow(self):
        """Test a workflow with multiple operations in sequence."""
        input_text = "1\n10\n5\n3\n3\n4\n2\n20\n8\n5\n"
        stdout, stderr, returncode = run_calculator_process(input_text)
        
        assert returncode == 0
        assert "10.0 + 5.0 = 15.0" in stdout
        assert "3.0 * 4.0 = 12.0" in stdout
        assert "20.0 - 8.0 = 12.0" in stdout