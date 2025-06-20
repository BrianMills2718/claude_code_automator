from typing import List
from fastapi import APIRouter, HTTPException, status
from ..models.todo import Todo, TodoCreate, TodoUpdate
from ..services.todo_service import TodoService

router = APIRouter(prefix="/todos", tags=["todos"])
todo_service = TodoService()


def _raise_not_found() -> HTTPException:
    """Helper function to raise consistent not found errors."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Todo not found"
    )


@router.post("/", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate) -> Todo:
    return todo_service.create_todo(todo)


@router.get("/", response_model=List[Todo])
def get_todos() -> List[Todo]:
    return todo_service.get_all_todos()


@router.get("/{todo_id}", response_model=Todo)
def get_todo(todo_id: int) -> Todo:
    todo = todo_service.get_todo_by_id(todo_id)
    if todo is None:
        _raise_not_found()
    assert todo is not None
    return todo


@router.put("/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo_update: TodoUpdate) -> Todo:
    todo = todo_service.update_todo(todo_id, todo_update)
    if todo is None:
        _raise_not_found()
    assert todo is not None
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int) -> None:
    if not todo_service.delete_todo(todo_id):
        _raise_not_found()