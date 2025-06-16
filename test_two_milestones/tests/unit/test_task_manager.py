import pytest
from main import Task, TaskManager


class TestTaskManager:
    """Test cases for the TaskManager class."""
    
    def test_task_manager_initialization(self):
        """Test TaskManager initializes with empty task list and correct next_id."""
        manager = TaskManager()
        assert manager.tasks == []
        assert manager.next_id == 1
        assert isinstance(manager.tasks, list)
    
    def test_add_task_single(self):
        """Test adding a single task."""
        manager = TaskManager()
        task = manager.add_task("First Task")
        
        assert task.id == 1
        assert task.title == "First Task"
        assert task.completed is False
        assert len(manager.tasks) == 1
        assert manager.next_id == 2
    
    def test_add_task_multiple(self):
        """Test adding multiple tasks."""
        manager = TaskManager()
        task1 = manager.add_task("Task 1")
        task2 = manager.add_task("Task 2")
        task3 = manager.add_task("Task 3")
        
        assert task1.id == 1
        assert task2.id == 2
        assert task3.id == 3
        assert len(manager.tasks) == 3
        assert manager.next_id == 4
    
    def test_add_task_empty_title(self):
        """Test adding a task with empty title."""
        manager = TaskManager()
        task = manager.add_task("")
        
        assert task.id == 1
        assert task.title == ""
        assert task.completed is False
        assert len(manager.tasks) == 1
    
    def test_list_tasks_empty(self):
        """Test listing tasks when no tasks exist."""
        manager = TaskManager()
        tasks = manager.list_tasks()
        
        assert tasks == []
        assert len(tasks) == 0
    
    def test_list_tasks_multiple(self):
        """Test listing multiple tasks."""
        manager = TaskManager()
        manager.add_task("Task 1")
        manager.add_task("Task 2")
        manager.add_task("Task 3")
        
        tasks = manager.list_tasks()
        assert len(tasks) == 3
        assert tasks[0].title == "Task 1"
        assert tasks[1].title == "Task 2"
        assert tasks[2].title == "Task 3"
    
    def test_complete_task_valid_id(self):
        """Test completing a task with valid ID."""
        manager = TaskManager()
        task = manager.add_task("Test Task")
        
        # Task should initially be incomplete
        assert task.completed is False
        
        # Complete the task
        result = manager.complete_task(1)
        assert result is True
        assert task.completed is True
    
    def test_complete_task_invalid_id(self):
        """Test completing a task with invalid ID."""
        manager = TaskManager()
        manager.add_task("Test Task")
        
        # Try to complete non-existent task
        result = manager.complete_task(999)
        assert result is False
    
    def test_complete_task_already_completed(self):
        """Test completing an already completed task."""
        manager = TaskManager()
        task = manager.add_task("Test Task")
        
        # Complete the task first time
        result1 = manager.complete_task(1)
        assert result1 is True
        assert task.completed is True
        
        # Try to complete again
        result2 = manager.complete_task(1)
        assert result2 is True  # Should still return True
        assert task.completed is True
    
    def test_complete_task_empty_list(self):
        """Test completing a task when task list is empty."""
        manager = TaskManager()
        result = manager.complete_task(1)
        assert result is False
    
    def test_complete_task_zero_id(self):
        """Test completing a task with ID 0."""
        manager = TaskManager()
        manager.add_task("Test Task")
        result = manager.complete_task(0)
        assert result is False
    
    def test_complete_task_negative_id(self):
        """Test completing a task with negative ID."""
        manager = TaskManager()
        manager.add_task("Test Task")
        result = manager.complete_task(-1)
        assert result is False
    
    def test_tasks_persist_in_manager(self):
        """Test that tasks persist in the manager after operations."""
        manager = TaskManager()
        
        # Add tasks
        task1 = manager.add_task("Task 1")
        task2 = manager.add_task("Task 2")
        
        # Complete one task
        manager.complete_task(1)
        
        # Verify both tasks still exist
        tasks = manager.list_tasks()
        assert len(tasks) == 2
        assert tasks[0].completed is True
        assert tasks[1].completed is False