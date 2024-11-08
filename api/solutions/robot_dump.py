"""
Solution for task 2:
Use robot memory dump to learn verification proccess.
"""

import os
import json
from http import HTTPStatus
import requests
from openai import OpenAI
from conf.logger import LOG
from common.prompts import DUMP_ANALYSIS

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
VERIFY_URL = os.environ["TASK2_URL"]
DUMP_URL = os.environ["TASK2_DUMP_URL"]
TIMEOUT = 20
PLACEHOLDER = "#task_2_page"

client = OpenAI(api_key=OPENAI_API_KEY)


def get_question() -> tuple[int, str]:
    """Get verification task"""
    initial_msg = {"text": "READY", "msgID": "0"}
    request_body = json.dumps(initial_msg)
    task_response = requests.post(VERIFY_URL, timeout=TIMEOUT, data=request_body)
    LOG.info("Task description: %s", task_response.text)
    if task_response.status_code != HTTPStatus.OK:
        LOG.error(
            "Could not read task description, status code: %s",
            task_response.status_code,
        )
        return None, None
    try:
        response_body = json.loads(task_response.text)
        msg_id, text = response_body["msgID"], response_body["text"]
        return msg_id, text
    except json.decoder.JSONDecodeError:
        LOG.error("Cannot decode task description: %s", task_response.text)
        return None


def answer_question(question: str) -> str:
    """Ask AI to answer question based on dump data"""
    robot_dump = requests.get(DUMP_URL, timeout=TIMEOUT)
    if robot_dump.status_code != HTTPStatus.OK:
        LOG.error("Could not read robot dump")
        return None
    prompt = DUMP_ANALYSIS.replace(PLACEHOLDER, robot_dump.text)
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"Question={question}",
            },
        ],
    )
    message = completion.choices[0].message
    LOG.debug("Response from assistant: %s", message)
    content = message.content
    LOG.info("Message content: %s", content)

    try:
        response = json.loads(content)
        answer = response["text"]
        LOG.info("Answer from the model: %s", answer)
        return answer
    except json.decoder.JSONDecodeError:
        LOG.error("Cannot decode model response: %s", content)
        return None


def verify(msg_id: int, answer: str) -> str:
    """Solve verification task"""
    answer_with_id = {"text": answer, "msgID": msg_id}
    answer_body = json.dumps(answer_with_id)
    verification_response = requests.post(VERIFY_URL, timeout=TIMEOUT, data=answer_body)
    if verification_response.status_code != HTTPStatus.OK:
        LOG.error("Task resolution failed")
        return None
    LOG.info("Verification response: %s", verification_response.text)
    try:
        return json.loads(verification_response.text)
    except json.decoder.JSONDecodeError:
        LOG.error("Cannot decode verification response")
        return None


def verification_process() -> dict:
    """Read flag"""
    msg_id, question = get_question()
    if (msg_id is None) or (question is None):
        LOG.error("Task cannot be solved")
        return None
    answer = answer_question(question)
    if answer is None:
        LOG.error("No answer returned")
        return None
    verification_response = verify(msg_id, answer)
    if verification_response is None:
        LOG.error("Verification failed")
        return None
    flag = verification_response["text"]
    return {"flag": flag, "question": question, "answer": answer}
