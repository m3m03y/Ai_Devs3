"""Endpoints with task solutions"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from solutions.captcha_solver import find_hidden_data
from solutions.robot_dump import verification_process
from solutions.file_fixer import fix_file

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
        raise HTTPException(status_code=400, detail="Verification task failed.")
    return JSONResponse(content=verification_result)


@solutions_router.get("/file-fix")
def complete_task_3() -> JSONResponse:
    """Solve task 3"""
    fixinig_result = fix_file()
    if fixinig_result is None:
        raise HTTPException(status_code=400, detail="Fixing file failed.")
    return JSONResponse(content=fixinig_result)
