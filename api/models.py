"""Base models"""

from typing import Any
from pydantic import BaseModel


class Task(BaseModel):
    """Task definition"""

    task_url: str


class Answer(BaseModel):
    """Answer definition"""

    task_id: str
    answer_url: str
    answer_content: Any
