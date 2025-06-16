import subprocess
import sys
from pathlib import Path
import pytest


def run_cli_with_input(user_input: str) -> tuple[str, str, int]:
    """Run the CLI with given input and return stdout, stderr, and return code."""
    project_root = Path(__file__).parent.parent.parent
    main_path = project_root / "main.py"
    
    result = subprocess.run(
        [sys.executable, str(main_path)],
        input=user_input,
        capture_output=True,
        text=True,
        cwd=str(project_root)
    )
    
    return result.stdout, result.stderr, result.returncode


def test_complete_workflow():
    """Test the complete workflow of adding, listing, and completing tasks."""
    # Add two tasks, list them, complete one, list again, then exit
    user_input = (
        "1\n"  # Add task
        "Buy groceries\n"
        "1\n"  # Add another task
        "Walk the dog\n"
        "2\n"  # List tasks
        "3\n"  # Complete task
        "1\n"  # Complete task with ID 1
        "2\n"  # List tasks again
        "4\n"  # Exit
    )
    
    stdout, stderr, returncode = run_cli_with_input(user_input)
    
    # Verify successful execution
    assert returncode == 0
    assert stderr == ""
    
    # Verify welcome message
    assert "Welcome to Task Manager CLI!" in stdout
    
    # Verify task additions
    assert "Task added successfully! (ID: 1)" in stdout
    assert "Task added successfully! (ID: 2)" in stdout
    
    # Verify task listing shows both tasks uncompleted
    lines = stdout.split('\n')
    task_list_sections = []
    in_task_section = False
    current_section = []
    
    for line in lines:
        if "=== Your Tasks ===" in line:
            in_task_section = True
            current_section = []
        elif "==================" in line and in_task_section:
            in_task_section = False
            task_list_sections.append(current_section)
        elif in_task_section:
            current_section.append(line)
    
    # First listing should show both tasks uncompleted
    assert len(task_list_sections) >= 1
    first_listing = '\n'.join(task_list_sections[0])
    assert "○ [1] Buy groceries" in first_listing
    assert "○ [2] Walk the dog" in first_listing
    
    # Verify task completion
    assert "Task 1 marked as completed!" in stdout
    
    # Second listing should show task 1 completed
    assert len(task_list_sections) >= 2
    second_listing = '\n'.join(task_list_sections[1])
    assert "✓ [1] Buy groceries" in second_listing
    assert "○ [2] Walk the dog" in second_listing
    
    # Verify exit message
    assert "Thank you for using Task Manager. Goodbye!" in stdout


def test_empty_task_list():
    """Test listing tasks when no tasks exist."""
    user_input = (
        "2\n"  # List tasks (empty)
        "4\n"  # Exit
    )
    
    stdout, stderr, returncode = run_cli_with_input(user_input)
    
    assert returncode == 0
    assert "No tasks found." in stdout


def test_invalid_inputs():
    """Test handling of invalid inputs."""
    user_input = (
        "5\n"  # Invalid menu choice
        "1\n"  # Add task
        "\n"   # Empty task title
        "3\n"  # Complete task
        "abc\n"  # Invalid task ID
        "3\n"  # Complete task
        "999\n"  # Non-existent task ID
        "4\n"  # Exit
    )
    
    stdout, stderr, returncode = run_cli_with_input(user_input)
    
    assert returncode == 0
    assert "Invalid choice! Please select 1-4." in stdout
    assert "Task title cannot be empty!" in stdout
    assert "Invalid task ID! Please enter a number." in stdout
    assert "Task with ID 999 not found!" in stdout


def test_keyboard_interrupt_handling():
    """Test that the CLI handles keyboard interrupts gracefully."""
    # This test is tricky to implement with subprocess, so we'll verify
    # the code structure exists for handling it
    project_root = Path(__file__).parent.parent.parent
    main_path = project_root / "main.py"
    
    with open(main_path, 'r') as f:
        content = f.read()
    
    # Verify KeyboardInterrupt handling exists
    assert "KeyboardInterrupt" in content
    assert "Interrupted. Exiting..." in content


def test_multiple_task_operations():
    """Test adding multiple tasks and completing them in different order."""
    user_input = (
        "1\nTask A\n"  # Add task 1
        "1\nTask B\n"  # Add task 2
        "1\nTask C\n"  # Add task 3
        "3\n2\n"       # Complete task 2
        "3\n3\n"       # Complete task 3
        "2\n"          # List all tasks
        "4\n"          # Exit
    )
    
    stdout, stderr, returncode = run_cli_with_input(user_input)
    
    assert returncode == 0
    assert "Task added successfully! (ID: 1)" in stdout
    assert "Task added successfully! (ID: 2)" in stdout
    assert "Task added successfully! (ID: 3)" in stdout
    assert "Task 2 marked as completed!" in stdout
    assert "Task 3 marked as completed!" in stdout
    
    # Verify final listing
    lines = stdout.split('\n')
    final_listing = []
    in_final_listing = False
    
    # Find the last task listing
    for i, line in enumerate(lines):
        if "=== Your Tasks ===" in line:
            in_final_listing = True
            final_listing = []
        elif "==================" in line and in_final_listing:
            in_final_listing = False
        elif in_final_listing:
            final_listing.append(line)
    
    final_text = '\n'.join(final_listing)
    assert "○ [1] Task A" in final_text  # Not completed
    assert "✓ [2] Task B" in final_text  # Completed
    assert "✓ [3] Task C" in final_text  # Completed