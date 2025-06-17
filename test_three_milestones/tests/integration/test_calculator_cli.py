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

    def test_cli_perform_operation_all_operations(self):
        """Test CLI's ability to perform all basic operations."""
        cli = CLI()
        
        # Test add
        result = cli._perform_operation('add', 10, 5)
        assert result == 15
        
        # Test subtract
        result = cli._perform_operation('subtract', 10, 5)
        assert result == 5
        
        # Test multiply
        result = cli._perform_operation('multiply', 10, 5)
        assert result == 50
        
        # Test divide
        result = cli._perform_operation('divide', 10, 5)
        assert result == 2.0

    def test_cli_error_propagation(self):
        """Test that Calculator errors properly propagate through CLI."""
        cli = CLI()
        
        # Division by zero should raise ValueError
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            cli._perform_operation('divide', 10, 0)

    def test_cli_number_parsing(self):
        """Test CLI's number parsing integration."""
        cli = CLI()
        
        # The _get_number method requires input, so we'll test _perform_operation
        # with different number types
        
        # Integer operations
        assert cli._perform_operation('add', 5, 3) == 8
        
        # Float operations
        assert cli._perform_operation('add', 5.5, 3.5) == 9.0
        
        # Mixed operations
        assert cli._perform_operation('multiply', 2, 3.5) == 7.0

    def test_complete_workflow_addition(self):
        """Test complete workflow through subprocess for addition."""
        input_text = "add\n5\n10\nquit\n"
        stdout, stderr, returncode = run_calculator_process(input_text)
        
        assert returncode == 0
        assert "Welcome to the Calculator!" in stdout
        assert "Result: 15" in stdout

    def test_complete_workflow_subtraction(self):
        """Test complete workflow through subprocess for subtraction."""
        input_text = "subtract\n20\n8\nquit\n"
        stdout, stderr, returncode = run_calculator_process(input_text)
        
        assert returncode == 0
        assert "Result: 12" in stdout

    def test_complete_workflow_multiplication(self):
        """Test complete workflow through subprocess for multiplication."""
        input_text = "multiply\n4\n7\nquit\n"
        stdout, stderr, returncode = run_calculator_process(input_text)
        
        assert returncode == 0
        assert "Result: 28" in stdout

    def test_complete_workflow_division(self):
        """Test complete workflow through subprocess for division."""
        input_text = "divide\n20\n4\nquit\n"
        stdout, stderr, returncode = run_calculator_process(input_text)
        
        assert returncode == 0
        assert "Result: 5" in stdout

    def test_complete_workflow_division_by_zero(self):
        """Test complete workflow handling division by zero."""
        input_text = "divide\n20\n0\nquit\n"
        stdout, stderr, returncode = run_calculator_process(input_text)
        
        assert returncode == 0
        assert "Error: Cannot divide by zero" in stdout

    def test_complete_workflow_invalid_operation(self):
        """Test complete workflow with invalid operation."""
        input_text = "invalid\nadd\n2\n3\nquit\n"
        stdout, stderr, returncode = run_calculator_process(input_text)
        
        assert returncode == 0
        assert "Invalid operation" in stdout
        assert "Result: 5" in stdout  # Should continue after error

    def test_complete_workflow_invalid_number(self):
        """Test complete workflow with invalid number input."""
        input_text = "add\nabc\n5\n10\nquit\n"
        stdout, stderr, returncode = run_calculator_process(input_text)
        
        assert returncode == 0
        assert "Invalid number" in stdout
        assert "Result: 15" in stdout  # Should recover and complete

    def test_data_flow_between_components(self):
        """Test data flow from CLI input through Calculator and back."""
        cli = CLI()
        
        # Simulate the data flow for different number types
        test_cases = [
            ('add', 10, 20, 30),
            ('subtract', 50.5, 20.5, 30.0),
            ('multiply', 3, 4, 12),
            ('divide', 100, 25, 4.0),
        ]
        
        for operation, num1, num2, expected in test_cases:
            result = cli._perform_operation(operation, num1, num2)
            assert result == expected

    def test_multiple_operations_workflow(self):
        """Test a workflow with multiple operations in sequence."""
        input_text = "add\n10\n5\nmultiply\n3\n4\nsubtract\n20\n8\nquit\n"
        stdout, stderr, returncode = run_calculator_process(input_text)
        
        assert returncode == 0
        assert "Result: 15" in stdout
        assert "Result: 12" in stdout  # 3 * 4
        assert "Result: 12" in stdout  # 20 - 8 (both happen to be 12)