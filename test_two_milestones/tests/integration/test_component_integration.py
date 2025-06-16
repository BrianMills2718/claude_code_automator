import sys
from pathlib import Path
import pytest

# Add the project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from main import Task, TaskManager


def test_task_manager_workflow():
    """Test the complete interaction between Task and TaskManager components."""
    manager = TaskManager()
    
    # Initially empty
    assert manager.list_tasks() == []
    assert manager.next_id == 1
    
    # Add first task
    task1 = manager.add_task("First task")
    assert isinstance(task1, Task)
    assert task1.id == 1
    assert task1.title == "First task"
    assert task1.completed is False
    assert manager.next_id == 2
    
    # Add second task
    task2 = manager.add_task("Second task")
    assert task2.id == 2
    assert task2.title == "Second task"
    assert task2.completed is False
    assert manager.next_id == 3
    
    # List tasks
    tasks = manager.list_tasks()
    assert len(tasks) == 2
    assert tasks[0] is task1
    assert tasks[1] is task2
    
    # Complete first task
    success = manager.complete_task(1)
    assert success is True
    assert task1.completed is True
    assert task2.completed is False
    
    # Try to complete non-existent task
    success = manager.complete_task(999)
    assert success is False
    
    # Verify task states
    tasks = manager.list_tasks()
    assert tasks[0].completed is True
    assert tasks[1].completed is False


def test_task_id_persistence():
    """Test that task IDs increment properly across multiple additions."""
    manager = TaskManager()
    
    # Add 5 tasks
    task_ids = []
    for i in range(5):
        task = manager.add_task(f"Task {i+1}")
        task_ids.append(task.id)
    
    # Verify IDs are sequential
    assert task_ids == [1, 2, 3, 4, 5]
    assert manager.next_id == 6
    
    # Complete some tasks
    manager.complete_task(2)
    manager.complete_task(4)
    
    # Add more tasks - IDs should continue from 6
    task6 = manager.add_task("Task 6")
    assert task6.id == 6
    assert manager.next_id == 7


def test_empty_title_handling():
    """Test how the system handles empty or whitespace-only titles."""
    manager = TaskManager()
    
    # The TaskManager itself doesn't validate titles
    # It's the CLI that prevents empty titles
    task = manager.add_task("")
    assert task.title == ""
    assert task.id == 1
    
    # Test with whitespace
    task2 = manager.add_task("   ")
    assert task2.title == "   "
    assert task2.id == 2


def test_task_references():
    """Test that task objects are properly referenced in the manager."""
    manager = TaskManager()
    
    # Add a task
    task = manager.add_task("Test task")
    
    # Get the task from list
    tasks = manager.list_tasks()
    retrieved_task = tasks[0]
    
    # They should be the same object
    assert task is retrieved_task
    
    # Modifying one should affect the other
    task.title = "Modified title"
    assert retrieved_task.title == "Modified title"
    
    # Completing through manager should affect original reference
    manager.complete_task(task.id)
    assert task.completed is True
    assert retrieved_task.completed is True


def test_multiple_completions():
    """Test completing the same task multiple times."""
    manager = TaskManager()
    
    task = manager.add_task("Test task")
    assert task.completed is False
    
    # First completion
    success = manager.complete_task(task.id)
    assert success is True
    assert task.completed is True
    
    # Second completion - should still succeed
    success = manager.complete_task(task.id)
    assert success is True
    assert task.completed is True


def test_task_ordering():
    """Test that tasks maintain their order."""
    manager = TaskManager()
    
    # Add tasks in specific order
    titles = ["Alpha", "Beta", "Gamma", "Delta"]
    for title in titles:
        manager.add_task(title)
    
    # Retrieve tasks
    tasks = manager.list_tasks()
    retrieved_titles = [task.title for task in tasks]
    
    # Order should be preserved
    assert retrieved_titles == titles
    
    # Complete some tasks - order should still be preserved
    manager.complete_task(2)  # Complete "Beta"
    manager.complete_task(4)  # Complete "Delta"
    
    tasks = manager.list_tasks()
    retrieved_titles = [task.title for task in tasks]
    assert retrieved_titles == titles