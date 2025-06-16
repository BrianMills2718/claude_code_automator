import pytest
from main import Task


class TestTask:
    """Test cases for the Task class."""
    
    def test_task_creation_with_defaults(self):
        """Test creating a task with default completed status."""
        task = Task(1, "Test Task")
        assert task.id == 1
        assert task.title == "Test Task"
        assert task.completed is False
    
    def test_task_creation_with_completed_true(self):
        """Test creating a task with completed=True."""
        task = Task(2, "Completed Task", completed=True)
        assert task.id == 2
        assert task.title == "Completed Task"
        assert task.completed is True
    
    def test_task_creation_with_completed_false(self):
        """Test creating a task with explicit completed=False."""
        task = Task(3, "Incomplete Task", completed=False)
        assert task.id == 3
        assert task.title == "Incomplete Task"
        assert task.completed is False
    
    def test_task_with_empty_title(self):
        """Test creating a task with empty title."""
        task = Task(4, "")
        assert task.id == 4
        assert task.title == ""
        assert task.completed is False
    
    def test_task_with_special_characters(self):
        """Test creating a task with special characters in title."""
        special_title = "Test @#$%^&*() Task!"
        task = Task(5, special_title)
        assert task.id == 5
        assert task.title == special_title
        assert task.completed is False
    
    def test_task_with_very_long_title(self):
        """Test creating a task with a very long title."""
        long_title = "A" * 1000
        task = Task(6, long_title)
        assert task.id == 6
        assert task.title == long_title
        assert len(task.title) == 1000