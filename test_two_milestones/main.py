import json
from pathlib import Path
from typing import List, Dict, Any


class Task:
    """Simple task with id, title, and completion status."""
    
    def __init__(self, task_id: int, title: str, completed: bool = False):
        self.id = task_id
        self.title = title
        self.completed = completed


class TaskManager:
    """Manages tasks in memory."""
    
    def __init__(self) -> None:
        self.tasks: List[Task] = []
        self.next_id: int = 1
    
    def add_task(self, title: str) -> Task:
        """Add a new task and return it."""
        task = Task(self.next_id, title)
        self.tasks.append(task)
        self.next_id += 1
        return task
    
    def list_tasks(self) -> List[Task]:
        """Return all tasks."""
        return self.tasks
    
    def complete_task(self, task_id: int) -> bool:
        """Mark a task as completed. Returns True if successful, False if not found."""
        for task in self.tasks:
            if task.id == task_id:
                task.completed = True
                return True
        return False


def display_menu() -> None:
    """Display the main menu."""
    print("\n=== Task Manager ===")
    print("1. Add Task")
    print("2. List Tasks")
    print("3. Complete Task")
    print("4. Exit")
    print("===================")


def main() -> None:
    """Main application loop."""
    task_manager = TaskManager()
    
    print("Welcome to Task Manager CLI!")
    
    while True:
        display_menu()
        
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                # Add Task
                title = input("Enter task title: ").strip()
                if title:
                    task = task_manager.add_task(title)
                    print(f"\n✓ Task added successfully! (ID: {task.id})")
                else:
                    print("\n✗ Task title cannot be empty!")
            
            elif choice == "2":
                # List Tasks
                tasks = task_manager.list_tasks()
                if not tasks:
                    print("\nNo tasks found.")
                else:
                    print("\n=== Your Tasks ===")
                    for task in tasks:
                        status = "✓" if task.completed else "○"
                        print(f"{status} [{task.id}] {task.title}")
                    print("==================")
            
            elif choice == "3":
                # Complete Task
                try:
                    task_id = int(input("Enter task ID to complete: ").strip())
                    if task_manager.complete_task(task_id):
                        print(f"\n✓ Task {task_id} marked as completed!")
                    else:
                        print(f"\n✗ Task with ID {task_id} not found!")
                except ValueError:
                    print("\n✗ Invalid task ID! Please enter a number.")
            
            elif choice == "4":
                # Exit
                print("\nThank you for using Task Manager. Goodbye!")
                break
            
            else:
                print("\n✗ Invalid choice! Please select 1-4.")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted. Exiting...")
            break
        except Exception as e:
            print(f"\n✗ An error occurred: {e}")


if __name__ == "__main__":
    main()