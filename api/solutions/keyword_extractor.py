"""
Solution for task 11:
Anylyse facts and raports, then extract the keywords
"""

import os
import json
from openai import OpenAI
from common.prompts import EXTRACT_KEYWORDS_FROM_FACT, EXTRACT_KEYWORDS_FROM_REPORT
from conf.logger import LOG
from task_service import send_answer
from models import Answer

RESOURCE_PATH = os.fspath(f"{os.environ["PROJECT_DIR"]}/resources/S03E01")
FACTS_PATH = os.fspath(f"{RESOURCE_PATH}/facts")
FACTS_FILE = os.fspath(f"{RESOURCE_PATH}/facts.json")
TEXT_FILE_EXTENSION = ".txt"

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
AIDEVS_API_KEY = os.environ["API_KEY"]
TASK_NAME = "dokumenty"
VERIFY_URL = os.environ["VERIFY_URL"]
FACTS_PLACEHOLDER = "task_11_facts"
REPORT_PLACEHOLDER = "task_11_report"
SECTOR_PLACEHOLDER = "task_11_sector"
TIMEOUT = 30

openai_client = OpenAI(api_key=OPENAI_API_KEY)


def _get_files_list(dirname: str) -> list[str]:
    files = []
    LOG.debug("[TASK-11] Search files in %s dir.", dirname)
    for file in os.listdir(dirname):
        file_path = os.fspath(f"{dirname}/{file}")
        _, ext = os.path.splitext(file_path)
        if os.path.isfile(file_path) and ext == TEXT_FILE_EXTENSION:
            files.append(file)
    LOG.debug("[TASK-11] Files: %s", files)
    return files


def _read_file(dirname: str, filename: str) -> str:
    full_path = os.fspath(f"{dirname}/{filename}")
    LOG.debug("[TASK-11] Read file: %s", full_path)
    if not os.path.isfile(full_path):
        raise ValueError("Cannot read file.")
    with open(full_path, "r", encoding="UTF-8") as file:
        return file.read()


def _extract_fact_keywords(fact: str) -> tuple[str, list[str]]:
    LOG.debug("[TASK-11] Process fact: %s", fact)
    prompt = EXTRACT_KEYWORDS_FROM_FACT.replace(FACTS_PLACEHOLDER, fact)

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "system", "content": prompt}]
    )
    message = completion.choices[0].message
    LOG.debug("[TASK-11] Response from assistant: %s", message)
    content = message.content
    LOG.debug("[TASK-11] Message content: %s", content)
    try:
        response = dict(json.loads(content))
        topic_name = response["topic-name"]
        keywords = response["keywords"]
        return topic_name, keywords
    except json.decoder.JSONDecodeError:
        LOG.error("[TASK-11] Cannot decode model: %s", content)
        return None


def _save_facts(facts: dict) -> None:
    filename = os.fspath(f"{RESOURCE_PATH}/facts.json")
    with open(filename, "w", encoding="UTF-8") as file:
        file.write(json.dumps(facts))


def _prepare_facts(fact_files: list[str]) -> dict:
    if os.path.isfile(FACTS_FILE):
        try:
            with open(FACTS_FILE, "r", encoding="UTF-8") as file:
                return json.loads(file.read())
        except json.decoder.JSONDecodeError:
            LOG.error("[TASK-11] Cannot get facts from file.")
            return None
    facts = {}
    for file in fact_files:
        fact = _read_file(FACTS_PATH, file)
        name, keywords = _extract_fact_keywords(fact)
        LOG.debug("[TASK-11] Keywords for file %s were extracted.", file)
        if name != "invalid":
            facts[name] = keywords
    LOG.debug("[TASK-11] Created facts dict: %s", json.dumps(facts))
    _save_facts(facts)
    return facts


def _extract_report_keywords(
    filename: str, report: str, facts: dict
) -> tuple[list[str], list[str]]:
    LOG.debug("[TASK-11] Process report: %s", report)
    prompt = EXTRACT_KEYWORDS_FROM_REPORT.replace(FACTS_PLACEHOLDER, json.dumps(facts))
    prompt = prompt.replace(REPORT_PLACEHOLDER, report)
    prompt = prompt.replace(SECTOR_PLACEHOLDER, filename)

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "system", "content": prompt}]
    )
    message = completion.choices[0].message
    LOG.debug("[TASK-11] Response from assistant: %s", message)
    content = message.content
    LOG.debug("[TASK-11] Message content: %s", content)
    try:
        response = dict(json.loads(content))
        keywords = response["keywords"]
        # references = []
        # for keyword in keywords:
        # if keyword in facts.keys():
        # references.append(keyword)
        references = response["references"]
        return keywords, references
    except json.decoder.JSONDecodeError:
        LOG.error("[TASK-11] Cannot decode model: %s", content)
        return None


def _get_reports_keywords(report_files: list[str], facts: dict) -> dict:
    reports = {}
    for file in report_files:
        report = _read_file(RESOURCE_PATH, file)
        keywords, references = _extract_report_keywords(file, report, facts)
        LOG.debug(
            "[TASK-11] Keywords for file %s were extracted, with references %s.",
            file,
            references,
        )
        for reference in references:
            if reference in facts.keys():
                keywords.extend(facts[reference])
        LOG.debug("[TASK-11] File: %s, keywords: %s.", file, keywords)
        reports[file] = ", ".join(keywords)
    LOG.debug("[TASK-11] Created reports dict: %s", json.dumps(reports))
    return reports


def _send_answer(answer_content: dict) -> dict:
    code, text = send_answer(
        Answer(task_id=TASK_NAME, answer_url=VERIFY_URL, answer_content=answer_content)
    )
    return {"code": code, "text": text}


def extract_keywords() -> dict:
    """Extract keywords from reports based on facts"""
    LOG.info("[TASK-11] Start keywords extraction...")
    fact_files = _get_files_list(FACTS_PATH)
    LOG.info("[TASK-11] Fact files: %s", fact_files)
    facts = _prepare_facts(fact_files)
    LOG.info("[TASK-11] Facts prepared: %s", json.dumps(facts))
    report_files = _get_files_list(RESOURCE_PATH)
    LOG.info("[TASK-11] Report files: %s", report_files)
    reports = _get_reports_keywords(report_files, facts)
    LOG.info("[TASK-11] Reports keywords prepared: %s", json.dumps(reports))
    response_from_api = _send_answer(reports)
    response_from_api["answer"] = reports
    return response_from_api
