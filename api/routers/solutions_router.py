"""Endpoints with task solutions"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from solutions.captcha_solver import find_hidden_data

solutions_router = APIRouter()


@solutions_router.get("/robot-catcha")
def complete_task_1() -> JSONResponse:
    """Solve task 1"""
    flag, links = find_hidden_data()
    return JSONResponse(content={"flag": flag, "links": links})
