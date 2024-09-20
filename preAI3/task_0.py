"""Test task"""

import json
import logging
import requests

TASK = "POLIGON"
TASK_URL = "https://poligon.aidevs.pl/dane.txt"
ANSWER_URL = "https://poligon.aidevs.pl/verify"
API_URL = "http://api.aidevs.local/"

logging.basicConfig(level=logging.INFO)


def get_description() -> str:
    """Get the task description as plain text"""
    task_json = json.dumps({"task_url": TASK_URL})
    task = requests.post(API_URL + "get-task", data=task_json, timeout=30)
    logging.info("Description=%s", task.text)
    return task.text


def solve_task(task: str):
    """Solving task logick"""
    answer_list = task.splitlines()
    logging.info("Processed answer: %s", answer_list)
    return answer_list


def send_answer(answer_content):
    """Send the answer"""
    answer_json = json.dumps(
        {"task_id": TASK, "answer_url": ANSWER_URL, "answer_content": answer_content}
    )
    response = requests.post(API_URL + "send-answer", data=answer_json, timeout=30)
    logging.info("Answer sent resulted in following response:\n%s", response.text)

if __name__ == "__main__":
    task_description = get_description()
    answer = solve_task(task_description)
    send_answer(answer)
