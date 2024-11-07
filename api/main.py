"""Main API Controller"""

from fastapi import FastAPI
from routers.task_router import task_router
from routers.solutions_router import solutions_router

app = FastAPI()

app.include_router(task_router)
app.include_router(solutions_router)
