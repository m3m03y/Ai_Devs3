"""Main API Controller"""

from fastapi import FastAPI
from task_service import get_task, send_answer
from models import Task, Answer

app = FastAPI()

@app.post("/get-task")
def get_task_descrition(task: Task):
    """Get task description"""
    return get_task(task)


@app.post("/send-answer")
def read_item(answer: Answer):
    """Send answer to api"""
    return send_answer(answer)
