"""AiDevs task api client service"""
import json
import os
import requests

from utils import pretty_json
from models import Task, Answer
from logger import LOG

API_KEY=os.environ['API_KEY']

def get_task(task: Task) -> str:
    """Get task description"""
    LOG.info("Request to read description from url: %s", task.task_url)
    task = requests.get(task.task_url, timeout=30)
    return task.text

def send_answer(answer: Answer) -> tuple[int, str]:
    """Sends task answer to specified url

    Args:
        task (str): task id
        answer (_type_): full answer
        answer_url (str): answer url to which request is send

    Returns:
        tuple[int, str]: response status code and body
    """
    full_answer = {"task": answer.task_id, "apikey": API_KEY, "answer": answer.answer_content}
    answer_body = json.dumps(full_answer)
    LOG.info("TASK_SERVICE: Answer to task: %s\n%s", answer.task_id, pretty_json(full_answer))
    result = requests.post(answer.answer_url, data=answer_body, timeout=30)
    return result.status_code, result.text
