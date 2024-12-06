"""
Solution for task 18:
Search websites to answer questions
"""

import os
import json
from http import HTTPStatus
import yaml
import requests
from markdownify import markdownify as md

from adapters.openai_adapter import OpenAiAdapter
from adapters.ai_devs_adapter import get_questions
from common.file_processor import read_file, save_file
from common.prompts import BROWSE_SITE, ANSWER_QUESTIONS_BASED_ON_WEBSITES
from conf.logger import LOG
from models import Answer
from task_service import send_answer

INFO_URL = os.environ["TASK18_INFO_URL"]
QUESTIONS_URL = os.environ["TASK18_QUESTIONS_URL"]
VERIFY_URL = os.environ["VERIFY_URL"]

TASK_NAME = "softo"

RESOURCE_PATH = os.fspath(f"{os.environ["PROJECT_DIR"]}/resources/S04E03")
QUESTIONS_FILENAME = "questions.json"
URLS_WITH_ANSWERS = "urls.json"

MODEL_NAME = "gpt-4o-mini"

MARKDOWN_SECTIONS = ["```yml", "```yaml", "```"]

TIMEOUT = 30


openai_client = OpenAiAdapter(api_key=os.environ["OPENAI_API_KEY"])


def _analyse_site(
    context: str, links: list, questions: dict, visited_links: list, base_url: str
) -> tuple[list, str, list]:
    prompt = (
        BROWSE_SITE.replace("task_18_context", context)
        .replace("task_18_links", str(links))
        .replace("task_18_questions", json.dumps(questions))
        .replace("task_18_visited_links", str(visited_links))
        .replace("task_18_base_url", base_url)
    )
    LOG.debug("Current prompt: %s.", prompt)
    messages = [{"role": "system", "content": prompt}]
    completion = openai_client.get_first_completions(MODEL_NAME, messages)
    LOG.debug("Completion: %s.", completion)
    for section in MARKDOWN_SECTIONS:
        completion = completion.replace(section, "")
    response = yaml.safe_load(completion)
    LOG.debug("Response from assistant: %s.", response)
    answers = response["answers"]
    next_page = response["redirect-to"]
    new_links = response["links"]
    LOG.debug("Discovered links: %s.", new_links)

    links.extend(link for link in new_links if link not in links)
    LOG.debug("Answers detected: %s.", answers)
    LOG.debug("Redirect to link: %s.", next_page)
    LOG.debug("All discovered links: %s.", links)
    return answers, next_page, links


def _update_answers_dict(
    urls_with_answer: dict[str, list], question_keys: list, current_url: str
) -> dict:
    for question in question_keys:
        if current_url not in urls_with_answer[question]:
            urls_with_answer[question].append(current_url)
    LOG.debug("Updated urls with answers: %s.", json.dumps(urls_with_answer))
    return urls_with_answer


def _get_context(url: str) -> str:
    response = requests.get(url, timeout=TIMEOUT)
    if response.status_code != HTTPStatus.OK:
        LOG.error("Could not get initial page.")
        return None
    return md(response.text)


def _browse_sites(questions: dict) -> dict:
    links = []
    context = _get_context(INFO_URL)
    if not context:
        LOG.error("No initial context loaded.")
        return None
    urls_with_answer = {"01": [], "02": [], "03": []}

    answers_count = 0
    request_count = 0

    visited_links = []
    current_url = INFO_URL
    while (answers_count < 3) and (request_count < 20):
        if current_url not in visited_links:
            visited_links.append(current_url)
        question_keys, current_url, links = _analyse_site(
            context, links, questions, visited_links, current_url
        )
        urls_with_answer = _update_answers_dict(
            urls_with_answer, question_keys, current_url
        )
        context = _get_context(current_url)
        if not context:
            break
        answers_count = 0
        for urls_list in urls_with_answer.values():
            LOG.debug("Current list: %s, length = %d.", urls_list, len(urls_list))
            if len(urls_list) > 0:
                answers_count += 1
        request_count += 1
        LOG.debug("Stats: requests=%d, answers found=%d.", request_count, answers_count)
    return urls_with_answer


def _answer_questions(questions: dict, urls_with_answers: dict) -> dict:
    links = set()
    for urls in urls_with_answers.values():
        for url in urls:
            links.add(url)
    LOG.debug("Context links: %s.", links)
    context = ""
    for link in links:
        page_response = requests.get(link, timeout=TIMEOUT)
        if page_response != HTTPStatus.OK:
            LOG.warning("Could not read content of page: %s.", link)
            continue
        context += f"{md(page_response.text)}\n"
    LOG.debug("Context: %s.", context)
    prompt = ANSWER_QUESTIONS_BASED_ON_WEBSITES.replace(
        "task_18_questions", json.dumps(questions)
    ).replace("task_18_context", context)

    messages = [{"role": "system", "content": prompt}]
    completion = openai_client.get_first_completions(MODEL_NAME, messages)
    for section in MARKDOWN_SECTIONS:
        completion = completion.replace(section, "")
    LOG.debug("Response from assistant: %s.", completion)
    answers = yaml.safe_load(completion)
    LOG.debug("Answers to questions: %s.", json.dumps(answers))
    return answers


def _get_urls_with_answers(questions: dict, build_urls: bool = False) -> dict:
    answers_file = os.fspath(f"{RESOURCE_PATH}/{URLS_WITH_ANSWERS}")
    if os.path.isfile(answers_file):
        urls_with_answers = read_file(RESOURCE_PATH, URLS_WITH_ANSWERS)
        if urls_with_answers and (not build_urls):
            LOG.debug("Read answers urls from file.")
            try:
                return json.loads(urls_with_answers)
            except json.decoder.JSONDecodeError:
                LOG.error("Could not decode urls with answers from file.")
        os.remove(answers_file)
        LOG.debug("Remove old answers file.")

    urls_with_answers = _browse_sites(questions)
    save_file(URLS_WITH_ANSWERS, RESOURCE_PATH, json.dumps(urls_with_answers))

    return urls_with_answers


def search_answers(build_urls: bool = False) -> dict:
    """Search answers to questions"""
    LOG.info("Start browsing...")
    questions = get_questions(QUESTIONS_URL, RESOURCE_PATH, QUESTIONS_FILENAME)
    if questions is None:
        return {"error": "No questions found."}
    LOG.info("Questions loaded: %s.", json.dumps(questions))
    urls_with_answers = _get_urls_with_answers(questions, build_urls)
    LOG.info("Urls with answers for questions: %s.", json.dumps(urls_with_answers))
    answers = _answer_questions(questions, urls_with_answers)
    LOG.info("Answers: %s.", json.dumps(answers))
    answer = Answer(task_id=TASK_NAME, answer_url=VERIFY_URL, answer_content=answers)
    code, text = send_answer(answer)
    return {"code": code, "text": text, "answers": answers}
