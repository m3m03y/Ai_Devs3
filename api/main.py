"""Main API Controller"""

from http import HTTPStatus
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from routers.task_router import task_router
from routers.solutions_router import solutions_router

from common.exceptions import AiDevsApiException, AiAssistantException

app = FastAPI()

app.include_router(task_router)
app.include_router(solutions_router)


@app.exception_handler(AiDevsApiException)
async def ai_devs_exception_handler(_request: Request, exc: AiDevsApiException):
    """Handles all issues related with Ai Devs Api"""
    return JSONResponse(
        status_code=HTTPStatus.BAD_GATEWAY,
        content={
            "message": f"Could not get response from AiDevs api:{exc.message}",
            "code": exc.code,
        },
    )


@app.exception_handler(AiAssistantException)
async def ai_assistant_exception_handler(_request: Request, exc: AiAssistantException):
    """Handles all issues with ai connection"""
    return JSONResponse(
        status_code=HTTPStatus.BAD_GATEWAY,
        content={
            "message": f"Could not get response from Ai assistant: {exc.message}.",
            "code": exc.code,
        },
    )
