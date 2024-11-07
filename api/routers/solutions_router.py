"""Endpoints with task solutions"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from solutions.captcha_solver import find_hidden_data
from solutions.robot_dump import verification_process

solutions_router = APIRouter()


@solutions_router.get("/robot-catcha")
def complete_task_1() -> JSONResponse:
    """Solve task 1"""
    flag, links = find_hidden_data()
    return JSONResponse(content={"flag": flag, "links": links})


@solutions_router.get("/robot-dump")
def complete_task_2() -> JSONResponse:
    """Solve task 2"""
    verification_result = verification_process()
    if verification_result is None:
        raise HTTPException(status_code=404, detail="Verification task failed")
    return JSONResponse(content=verification_result)
