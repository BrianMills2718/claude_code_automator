import os
import uvicorn
from fastapi import FastAPI
from src.api.todos import router as todos_router

app = FastAPI(title="Todo List API", version="1.0.0")

app.include_router(todos_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Todo List API"}


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    uvicorn.run("main:app", host=host, port=port, reload=reload)