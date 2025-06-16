# Task Manager CLI

## Project Overview
A command-line task manager with persistence

## Success Criteria
- Add, list, and complete tasks
- Tasks persist between runs
- Clear user interface

## Milestones

### Milestone 1: Basic task operations
- Create Task class with id, title, completed status
- Implement add_task(), list_tasks(), complete_task()
- Store tasks in memory (list)
- CLI menu with options: Add, List, Complete, Exit
- main.py runs successfully

### Milestone 2: Add persistence to task manager
- Save tasks to tasks.json file
- Load tasks on startup
- Auto-save after each operation
- Handle file errors gracefully
- Preserve task IDs between sessions
- Ensure main.py still runs with all features