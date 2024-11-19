"""
Solution for task 5:
Censor a given file
"""

import os
from http import HTTPStatus
import requests
from openai import OpenAI
from conf.logger import LOG
from common.prompts import CENSORE_FILE
from models import Answer
from task_service import send_answer

AIDEVS_API_KEY = os.environ["API_KEY"]
DATA_URL = os.environ["TASK5_DATA_URL"]
VERIFY_URL = os.environ["VERIFY_URL"]
TIMEOUT = 60
OLLAMA_URL = os.environ["OLLAMA_URL"]
MODEL = "llama3.2:3b"
# MODEL = "gpt-4o-mini"

client = OpenAI(base_url=OLLAMA_URL)

# OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
# client = OpenAI(api_key=OPENAI_API_KEY)


def _get_file() -> str:
    """Download data file"""
    file_response = requests.get(DATA_URL, timeout=TIMEOUT)
    if file_response.status_code != HTTPStatus.OK:
        LOG.error(
            "[TASK-5] Cannot download file, status code: %d", file_response.status_code
        )
        return None
    file_content = file_response.text
    LOG.info("[TASK-5] Downloaded file content: %s", file_content)
    return file_content


def _censore_file(file_content: str) -> str:
    """Censore data in file"""
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": CENSORE_FILE},
            {"role": "user", "content": file_content},
        ],
    )
    message = completion.choices[0].message
    LOG.debug("[TASK-5] Response from assistant: %s", message)
    content = message.content
    LOG.info("[TASK-5] Message content: %s", content)
    return content


def get_censored_file() -> dict:
    """Returns censored file"""
    file_data = _get_file()
    censored_text = _censore_file(file_data)
    code, text = send_answer(
        Answer(task_id="CENZURA", answer_url=VERIFY_URL, answer_content=censored_text)
    )
    return {"code": code, "text": text}
