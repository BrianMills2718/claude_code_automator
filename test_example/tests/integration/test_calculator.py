"""Integration tests for calculator application."""

import subprocess
import sys
from pathlib import Path


class TestCalculatorIntegration:
    """Integration tests for the calculator main program."""
    
    def test_main_module_imports(self) -> None:
        """Test that main.py can be imported without errors."""
        # This test ensures all imports work correctly
        import main
        assert hasattr(main, 'main')
        assert hasattr(main, 'get_number')
        assert hasattr(main, 'get_operation')
        assert hasattr(main, 'perform_calculation')
    
    def test_perform_calculation_function(self) -> None:
        """Test the perform_calculation function with all operations."""
        from main import perform_calculation
        
        # Test addition
        assert perform_calculation(5, 3, '+') == 8
        
        # Test subtraction
        assert perform_calculation(5, 3, '-') == 2
        
        # Test multiplication
        assert perform_calculation(5, 3, '*') == 15
        
        # Test division
        assert perform_calculation(6, 3, '/') == 2
    
    def test_perform_calculation_division_by_zero(self) -> None:
        """Test that perform_calculation handles division by zero."""
        from main import perform_calculation
        import pytest
        
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            perform_calculation(5, 0, '/')
    
    def test_calculator_module_integration(self) -> None:
        """Test that main.py correctly uses calculator module functions."""
        from main import perform_calculation
        from src.calculator import add, subtract, multiply, divide
        
        # Verify main uses the same logic as calculator module
        a, b = 7, 3
        
        assert perform_calculation(a, b, '+') == add(a, b)
        assert perform_calculation(a, b, '-') == subtract(a, b)
        assert perform_calculation(a, b, '*') == multiply(a, b)
        assert perform_calculation(a, b, '/') == divide(a, b)
    
    def test_main_py_executable(self) -> None:
        """Test that main.py can be executed without syntax errors."""
        # This test runs main.py with --help flag (if it existed) or just imports it
        # Since our main.py doesn't have command line args, we'll just test the import
        project_root = Path(__file__).parent.parent.parent
        main_py = project_root / "main.py"
        
        # Test that the file exists and is executable
        assert main_py.exists(), "main.py should exist"
        
        # Test that Python can parse the file (no syntax errors)
        result = subprocess.run([
            sys.executable, "-m", "py_compile", str(main_py)
        ], capture_output=True, text=True, cwd=project_root)
        
        assert result.returncode == 0, f"main.py has syntax errors: {result.stderr}"