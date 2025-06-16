import pytest
from io import StringIO
import sys
from main import display_menu


class TestDisplayMenu:
    """Test cases for the display_menu function."""
    
    def test_display_menu_output(self):
        """Test that display_menu outputs the correct menu."""
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            display_menu()
            output = captured_output.getvalue()
            
            # Verify menu contents
            assert "=== Task Manager ===" in output
            assert "1. Add Task" in output
            assert "2. List Tasks" in output
            assert "3. Complete Task" in output
            assert "4. Exit" in output
            assert "===================" in output
            
            # Verify order
            lines = output.strip().split('\n')
            assert len(lines) == 6
            assert lines[0] == "=== Task Manager ==="
            assert lines[1] == "1. Add Task"
            assert lines[2] == "2. List Tasks"
            assert lines[3] == "3. Complete Task"
            assert lines[4] == "4. Exit"
            assert lines[5] == "==================="
            
        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__
    
    def test_display_menu_no_return_value(self):
        """Test that display_menu returns None."""
        # Suppress output
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            result = display_menu()
            assert result is None
        finally:
            sys.stdout = sys.__stdout__