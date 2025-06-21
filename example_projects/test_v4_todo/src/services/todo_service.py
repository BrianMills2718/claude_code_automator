from typing import List, Optional, Dict
from ..models.todo import Todo, TodoCreate, TodoUpdate


class TodoService:
    def __init__(self) -> None:
        self._todos: Dict[int, Todo] = {}
        self._next_id = 1

    def create_todo(self, todo_data: TodoCreate) -> Todo:
        todo = Todo(
            id=self._next_id,
            title=todo_data.title,
            description=todo_data.description,
            completed=todo_data.completed
        )
        self._todos[self._next_id] = todo
        self._next_id += 1
        return todo

    def get_all_todos(self) -> List[Todo]:
        return list(self._todos.values())

    def get_todo_by_id(self, todo_id: int) -> Optional[Todo]:
        return self._todos.get(todo_id)

    def update_todo(self, todo_id: int, todo_data: TodoUpdate) -> Optional[Todo]:
        if todo_id not in self._todos:
            return None
        
        todo = self._todos[todo_id]
        update_dict = todo_data.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            setattr(todo, field, value)
        
        return todo

    def delete_todo(self, todo_id: int) -> bool:
        if todo_id in self._todos:
            del self._todos[todo_id]
            return True
        return False