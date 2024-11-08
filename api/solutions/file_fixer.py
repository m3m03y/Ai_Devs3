"""
Solution for task 3:
Fix configuration file
"""

import os
import json
from http import HTTPStatus
import numexpr
import requests
from openai import OpenAI
from conf.logger import LOG
from common.prompts import FIX_FILE
from models import Answer
from task_service import send_answer

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
AIDEVS_API_KEY = os.environ["API_KEY"]
FILE_URL = os.environ["TASK3_FILE_URL"]
VERIFY_URL = os.environ["TASK3_VERIFY_URL"]
PROJECT_DIR = os.environ["PROJECT_DIR"]
FILENAME = "task3.json"
TIMEOUT = 60
PLACEHOLDER = "#task_3_test_data"

client = OpenAI(api_key=OPENAI_API_KEY)


def _download_file() -> str:
    """Download configuration file"""
    file_response = requests.get(FILE_URL, timeout=TIMEOUT)
    if file_response.status_code != HTTPStatus.OK:
        LOG.error(
            "[TASK-3] Cannot download file, status code: %d", file_response.status_code
        )
        return None
    file_content = file_response.text
    LOG.info("[TASK-3] Downloaded file length: %d", len(file_content))
    return file_content


def _get_file() -> dict:
    """Read configuration file"""
    temp_dir = os.fspath(f"{PROJECT_DIR}/tmp")
    if not os.path.isdir(temp_dir):
        try:
            os.mkdir(temp_dir)
        except FileExistsError:
            LOG.error("[TASK-3] File or directory: %s already exists", temp_dir)
            return None
        except FileNotFoundError:
            LOG.error("[TASK-3] Parent directory: %s does not exists", PROJECT_DIR)
            return None
    file_path = os.fspath(f"{temp_dir}/{FILENAME}")
    if not os.path.isfile(file_path):
        file_content = _download_file()
        with open(file_path, "w", encoding="UTF-8") as file:
            file.write(file_content)
    else:
        with open(file_path, "r", encoding="UTF-8") as file:
            file_content = file.read()
    try:
        return json.loads(file_content)
    except json.decoder.JSONDecodeError:
        LOG.error("[TASK-3] Cannot decode file as json")
        return None


def _fix_calculations(test_data: list) -> list:
    """Correct all answers for calculation questions"""
    for entry in test_data:
        question = entry["question"]
        answer = entry["answer"]
        expected_answer = numexpr.evaluate(question).item()
        if expected_answer != answer:
            entry["answer"] = expected_answer
            LOG.info(
                "[TASK-3] Correct answer for: %s, previous value=%d, new value=%d",
                question,
                answer,
                expected_answer,
            )
    return test_data


def _get_open_questions_with_positions(test_data: list) -> tuple[list, dict]:
    """Find all open questions"""
    open_questions = []
    positions = {}
    for idx, entry in enumerate(test_data):
        if "test" in entry:
            LOG.info("[TASK-3] Open question detected at position: %d", idx)
            test = entry["test"]
            q = test["q"]
            open_questions.append(q)
            positions[q] = idx
    LOG.debug("[TASK-3] Open questions positions: %s", positions)
    return open_questions, positions


def _get_question_answers(questions: list):
    """Sent questions to an assistant"""
    prompt = FIX_FILE.replace(PLACEHOLDER, str(questions))
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
        ],
    )
    message = completion.choices[0].message
    LOG.debug("[TASK-3] Response from assistant: %s", message)
    content = message.content
    LOG.info("[TASK-3] Message content: %s", content)

    try:
        response = json.loads(content)
        LOG.info("[TASK-3] Answer from the model: %s", response)
        return response
    except json.decoder.JSONDecodeError:
        LOG.error("[TASK-3] Cannot decode model response: %s", content)
        return None


def _build_correct_data(file_content: dict, answers: dict, positions: dict):
    """Format a result response"""
    answers_with_question_list = answers["questions"]
    for entry in answers_with_question_list:
        q = entry["q"]
        idx = positions[q]
        answer = entry["a"]
        file_content["test-data"][idx]["test"]["a"] = answer
        LOG.info(
            "[TASK-3] Updated entry at index: %d, new entry = %s",
            idx,
            file_content["test-data"][idx],
        )

    file_content["apikey"] = AIDEVS_API_KEY

    temp_dir = os.fspath(f"{PROJECT_DIR}/tmp")
    file_path = os.fspath(f"{temp_dir}/fixed.json")

    with open(file_path, "w", encoding="UTF-8") as file:
        file.write(json.dumps(file_content))
    return file_content


def fix_file() -> dict:
    """Fix configuration file"""
    file_content = _get_file()
    test_data = file_content["test-data"]
    LOG.info("[TASK-3] Test data loaded, example data: %s", json.dumps(test_data[0]))
    test_data = _fix_calculations(test_data)
    file_content["test-data"] = test_data
    open_questions, positions = _get_open_questions_with_positions(test_data)
    LOG.info("[TASK-3] Open questions: %s", open_questions)
    answers = _get_question_answers(open_questions)
    result = _build_correct_data(file_content, answers, positions)
    code, text = send_answer(
        Answer(task_id="JSON", answer_url=VERIFY_URL, answer_content=result)
    )
    return {"code": code, "text": text}
