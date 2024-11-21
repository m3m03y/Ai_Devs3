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

MODEL = "gpt-4o-mini"
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

PLACEHOLDER = "task_13_summary_placeholder"

openai_client = OpenAI(api_key=OPENAI_API_KEY)


def _get_details(question: str, summary: str) -> tuple[str, list[str], bool]:
    prompt = GET_DATACENTERS.replace(PLACEHOLDER, summary)
    LOG.debug("[TASK-13] Current prompt: %s.", prompt)
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
    summary = response[0]["summary"]
    queries = response[0]["queries"]
    is_answer = response[0]["isAnswer"]
    LOG.debug(
        "[TASK-13] Current knowledge:\nsummary=\n%s\nquery='%s'\nis_answer=%s",
        summary,
        queries,
        is_answer,
    )

    return summary, queries, is_answer


def _analyze_db_structure(question: str) -> str:
    is_answer = False
    summary = ""
    query = ""
    query_count = 1
    while (not is_answer) and (query_count < 10):
        summary, queries, is_answer = _get_details(question, summary)
        if is_answer:
            query = queries[0]["query"]
            LOG.debug(
                "[TASK-13] Query for answer found after %d queries.",
                query_count,
            )
            break

        for entry in queries:
            LOG.debug("[TASK-13] Current processed entry: '%s'.", entry)
            query = entry["query"]
            LOG.debug(
                "[TASK-13] Current processed query #%d: '%s'.", query_count, query
            )
            response = run_query(query)
            summary += f"\nQuery :{query} result:\n{response}\n"
            query_count += 1
    LOG.debug("[TASK-13] Final query: %s", query)
    return query


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
    LOG.debug("[TASK-13] Response from API: %s", json.dumps(response_body))
    return response_body


def answer_question(question: str) -> dict:
    """Get query to answer to question"""
    LOG.info("[TASK-13] Start query preparation.")
    query = _analyze_db_structure(question)
    LOG.info("[TASK-13] Query to answer question: %s", query)
    datacenters_response = run_query(query)
    LOG.info("[TASK-13] Retrived datacenters information.")
    datacenters_ids = _get_datacenters_ids(datacenters_response)
    LOG.info("[TASK-13] Datacenters ids: %s", datacenters_ids)
    code, text = send_answer(
        Answer(task_id=TASK_NAME, answer_url=VERIFY_URL, answer_content=datacenters_ids)
    )
    return {"code": code, "text": text, "answer": datacenters_ids}
