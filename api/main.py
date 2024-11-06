"""Main API Controller"""

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from task_service import get_task, send_answer
from models import Task, Answer

app = FastAPI()


@app.post("/task")
def get_task_descrition(task: Task) -> PlainTextResponse:
    """Get task description"""
    return PlainTextResponse(content=get_task(task), media_type="text/plain")


@app.post("/answer")
def read_item(answer: Answer) -> PlainTextResponse:
    """Send answer to api"""
    status_code, message = send_answer(answer)
    response_content = (
        f"Answer send successfully, response status code={status_code}\n"
        f"Message:\n"
        f"{message}"
    )
    return PlainTextResponse(content=response_content, media_type="text/plain")
