"""
Solution for task 13:
Search relevant data about datacenters in db
"""

import os
import json
import yaml
from openai import OpenAI

from conf.logger import LOG
from models import DBRequest, Answer
from task_service import send_answer
from common.db_connector import send_request
from common.prompts import GET_DATACENTERS

DB_API_URL = os.environ["TASK13_DB_API_URL"]
TASK_NAME = "database"
VERIFY_URL = os.environ["VERIFY_URL"]

MODEL = "gpt-4o"
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

PLACEHOLDER = "task_13_placeholder"

openai_client = OpenAI(api_key=OPENAI_API_KEY)


def _get_answer_query(question: str, tables_creation: list[str]) -> str:
    prompt = GET_DATACENTERS.replace(PLACEHOLDER, "\n".join(tables_creation))
    completions = openai_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
    )

    message = completions.choices[0].message
    LOG.debug("[TASK-13] Message from assistant: %s.", message)
    content = message.content
    LOG.debug("[TASK-13] Content: %s.", content)
    response = yaml.safe_load(content)
    return response[0]["query"]


def _get_datacenters_ids(datacenters_response: dict) -> list[str]:
    reply = datacenters_response["reply"]
    datacenter_ids = []
    for datacenter in reply:
        datacenter_ids.append(datacenter["dc_id"])
    LOG.debug("[TASK-13] Datacenters ids: %s.", datacenter_ids)
    return datacenter_ids


def run_query(query: str) -> dict:
    """Run query provided by user"""
    if (query is None) or (len(query) == 0):
        LOG.warning("[TASK-13] Received empty query.")
        return None
    LOG.info("[TASK-13] Send query '%s' to url: '%s'", query, DB_API_URL)
    response = send_request(DB_API_URL, DBRequest(task_id=TASK_NAME, query=query))
    if response is None:
        return None
    response_body = json.loads(response.text)
    return response_body


def answer_question(question: str, tables_creation: list[str]) -> dict:
    """Get query to answer to question"""
    LOG.info("[TASK-13] Start query preparation.")
    query = _get_answer_query(question, tables_creation)
    LOG.info("[TASK-13] Query to answer question: %s", query)
    datacenters_response = run_query(query)
    LOG.info("[TASK-13] Retrived datacenters information.")
    datacenters_ids = _get_datacenters_ids(datacenters_response)
    LOG.info("[TASK-13] Datacenters ids: %s", datacenters_ids)
    code, text = send_answer(
        Answer(task_id=TASK_NAME, answer_url=VERIFY_URL, answer_content=datacenters_ids)
    )
    return {"code": code, "text": text, "answer": datacenters_ids}
