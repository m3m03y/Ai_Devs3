"""
Solution for task 14:
Browse people and places to find missing person
"""

import os
import json
from http import HTTPStatus
import yaml
import requests
from openai import OpenAI
from common.file_processor import read_remote_file, save_file
from common.prompts import MISSING_PERSON_DATA_EXTRACTOR, FIND_PERSON_OR_CITY
from conf.logger import LOG
from models import Answer
from task_service import send_answer

FILE_DIR = os.fspath(f"{os.environ["PROJECT_DIR"]}/resources/S03E04")
ENTRY_DATA_FILENAME = "barbara.txt"

ENTRY_DATA_URL = os.environ["TASK14_ENTRY_DATA"]
PLACES_URL = os.environ["TASK14_PLACES_URL"]
PEOPLE_URL = os.environ["TASK14_PEOPLE_URL"]

MODEL = "gpt-4o-mini"
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

PLACEHOLDER = "task_14_placeholder"
RELATIONS_PLACEHOLDER = "task_14_relations"

TASK_NAME = "loop"
VERIFY_URL = os.environ["VERIFY_URL"]
API_KEY = os.environ["API_KEY"]

TIMEOUT = 30

openai_client = OpenAI(api_key=OPENAI_API_KEY)


def _read_entry_data():
    entry_data_path = os.fspath(f"{FILE_DIR}/{ENTRY_DATA_FILENAME}")
    if os.path.isfile(entry_data_path):
        LOG.debug("File %s exists. Reading data from file", entry_data_path)
        with open(entry_data_path, "r", encoding="UTF-8") as file:
            return file.read()
    entry_data = read_remote_file(ENTRY_DATA_URL)
    if entry_data is None:
        LOG.warning("Could not read file from remote url.")
        raise ValueError("No remote file found.")
    LOG.debug("Data read from file: %s successfully.", ENTRY_DATA_URL)
    save_file(ENTRY_DATA_FILENAME, FILE_DIR, entry_data)
    return entry_data


def _talk_to_assistant(messages: list[dict]):
    completions = openai_client.chat.completions.create(model=MODEL, messages=messages)
    message = completions.choices[0].message
    LOG.debug("Message from assistant: %s.", message)
    content = message.content
    LOG.debug("Content of message from assistant: %s.", content)
    yaml_content = yaml.safe_load(content)
    LOG.debug("Formatted content: %s.", yaml_content)
    if isinstance(yaml_content, list):
        yaml_content = yaml_content[0]
    return yaml_content


def _search_starting_points(entry_data: str):
    prompt = MISSING_PERSON_DATA_EXTRACTOR.replace(PLACEHOLDER, entry_data)
    messages = [{"role": "system", "content": prompt}]
    return _talk_to_assistant(messages)


def _search_data(question: str, context: str) -> dict:
    prompt = FIND_PERSON_OR_CITY.replace(PLACEHOLDER, context)

    LOG.debug("Used prompt: %s", prompt)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]
    return _talk_to_assistant(messages)


def _search_system(url: str, query: str) -> str:
    request_body = json.dumps({"apikey": API_KEY, "query": query})
    LOG.debug("Send search request with body=%s.", request_body)
    response = requests.get(url, data=request_body, timeout=TIMEOUT)
    if response.status_code != HTTPStatus.OK:
        LOG.warning("Could not get reponse from resource %s for query: %s.", url, query)
        return None
    LOG.debug("Data from url %s read successfully.", url)
    content = json.loads(response.text)
    message = content["message"]
    LOG.debug("Response from system: %s.", message)
    if message == "[**RESTRICTED DATA**]":
        return None
    return message


def _search_city(city: str) -> str:
    return _search_system(PLACES_URL, city)


def _search_person(name: str) -> str:
    return _search_system(PEOPLE_URL, name)


def _create_relations(data: dict, relations: dict = None) -> dict:
    if relations is None:
        LOG.debug("Initialize relations.")
        relations = {}
    if "cities" in data:
        for city in data["cities"]:
            if city not in relations:
                relations[city] = _search_city(city)
    if "people" in data:
        for person in data["people"]:
            relations[person] = _search_person(person)
    LOG.debug("Known relations %s.", yaml.safe_dump(relations))
    return relations


def _create_visited(relations: dict, visited: set[str] = None) -> set[str]:
    if visited is None:
        LOG.debug("Initialize visited.")
        visited = set()
    visited = {*relations.keys(), *visited}
    LOG.debug("Get all visited: %s", visited)
    return visited


def _create_context(relations: dict, visited: set[str]) -> str:
    context = f"Relations:\n{yaml.safe_dump(relations)}"
    if len(visited) != 0:
        context += f"\nVisited: {" ".join(visited)}"
    LOG.debug("Created context: %s.", context)
    return context


def _check_answer(relations: dict, visited: list[str], name: str) -> str:
    for key, value in relations.items():
        if value is None:
            continue
        if (name in value) and (key not in visited):
            LOG.debug("Answer found: %s", key)
            return key
    LOG.debug("Answer not found.")
    return None


def _find_answer_to_question(relations: dict, visited: set[str], name: str) -> str:
    answer = ""
    query_count = 1
    context = _create_context(relations, visited)
    LOG.debug("Initial context: %s.", context)
    while (not answer) and (query_count < 10):
        assistant_response = _search_data(name, context)
        LOG.debug("Response #%d: %s", query_count, assistant_response)
        query_count += 1
        relations = _create_relations(assistant_response, relations)
        answer = _check_answer(relations, visited, name)
        if answer:
            return answer
        visited = _create_visited(relations, visited)
        LOG.debug("New relations: %s.", relations)
        context = _create_context(relations, visited)
    return answer


def find_missing_person(name: str) -> dict:
    """Find place where missing person is"""
    LOG.info("Start searching...")
    entry_data = _read_entry_data()
    LOG.info("Entry data loaded: %s...", entry_data[:100])
    starting_points = _search_starting_points(entry_data)
    LOG.info("Starting points discovered: %s.", json.dumps(starting_points))
    relations = _create_relations(starting_points)
    visited = _create_visited(relations)
    LOG.info("Finding the answer...")
    answer = _find_answer_to_question(relations, visited, name)
    LOG.info("Answer found: %s.", answer)
    code, text = send_answer(
        Answer(task_id=TASK_NAME, answer_url=VERIFY_URL, answer_content=answer)
    )
    return {"code": code, "text": text, answer: "answer"}
