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


def _search_data(entry_data: str, question: str = None, relations: str = None) -> dict:
    prompt = (
        MISSING_PERSON_DATA_EXTRACTOR.replace(PLACEHOLDER, entry_data)
        if not question and not relations
        else FIND_PERSON_OR_CITY.replace(PLACEHOLDER, entry_data).replace(
            RELATIONS_PLACEHOLDER, relations
        )
    )
    LOG.debug("Used prompt: %s", prompt)
    messages = [{"role": "system", "content": prompt}]
    if question:
        messages.append({"role": "user", "content": question})
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


def _create_context(data: dict) -> str:
    relations = "\n"
    for city in data["cities"]:
        city_data = _search_city(city)
        LOG.debug("City data about %s: %s.", city, city_data)
        relations += f"{city} relations:"
        relations += f" '{city_data}'\n" if city_data else "\n"
    for person in data["people"]:
        person_data = _search_person(person)
        LOG.debug("Person data about %s: %s.", person, person_data)
        relations += f"{person} relations:"
        relations += f" '{person_data}'\n" if person_data else "\n"
    LOG.debug("Relations: %s.", relations[:100])
    return relations


def _find_answer_to_question(context: str, relations: str, question: str) -> str:
    answer = ""
    query_count = 1
    while (not answer) and (query_count < 10):
        response = _search_data(context, question, relations)
        LOG.debug("Response #%d: %s", query_count, response)
        query_count += 1
        answer = response["answer"]
        if answer:
            LOG.debug("Answer found: %s.", answer)
            return answer
        summary = response["summary"]
        relations = _create_context(response)
        context = summary
        LOG.debug("New context: %s.", context)
    return answer


def find_missing_person(question: str) -> dict:
    """Find place where missing person is"""
    LOG.info("Start searching...")
    entry_data = _read_entry_data()
    LOG.info("Entry data loaded: %s...", entry_data[:100])
    starting_points = _search_data(entry_data)
    LOG.info("Starting points discovered: %s.", json.dumps(starting_points))
    relations = _create_context(starting_points)
    LOG.info("Finding the answer...")
    answer = _find_answer_to_question(entry_data, relations, question)
    LOG.info("Answer found: %s.", answer)
    code, text = send_answer(
        Answer(task_id=TASK_NAME, answer_url=VERIFY_URL, answer_content=answer)
    )
    return {"code": code, "text": text, answer: "answer"}
