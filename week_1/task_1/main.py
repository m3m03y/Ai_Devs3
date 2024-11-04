"""Implementation of AI login service"""

import os
import re
from http import HTTPStatus

import requests
from bs4 import BeautifulSoup

from logger import LOG

WEBSITE_URL = os.environ["WEBSITE_URL"]
OLLAMA_URL = "http://127.0.0.1:11434/v1/completions"
OLLAMA_MODEL = "gemma2:2b"
USERNAME = os.environ["TASK1_USERNAME"]
PASSWORD = os.environ["TASK1_PASSWORD"]
TIMEOUT_DEFAULT = 60


def get_current_question() -> str:
    """Get current login question"""
    response = requests.get(WEBSITE_URL, timeout=TIMEOUT_DEFAULT)
    if response.status_code != HTTPStatus.OK:
        LOG.error("Invalid http status on question get: %s", response.status_code)
    soup = BeautifulSoup(response.text, "html.parser")
    question_paragraph = soup.find("p", id="human-question")
    if question_paragraph:
        question = (
            question_paragraph.get_text().strip().replace("Question:", "").strip()
        )
        LOG.info("Retrive question: %s", question)
        return question
    LOG.error("No question was found in <p> with id='human-question' on the website.")
    return None


def get_llm_answer(question: str) -> None:
    """Given question returns a valid answer"""
    prompt = f"In the response for the question send me only the year. Question is: {question}"
    ollama_payload = {"model": OLLAMA_MODEL, "prompt": prompt}
    ollama_response = requests.post(
        OLLAMA_URL, json=ollama_payload, timeout=TIMEOUT_DEFAULT
    )
    if ollama_response.status_code != HTTPStatus.OK:
        LOG.error("Invalid response from LLM")
        return None
    response_data = ollama_response.json()
    LOG.debug("LLM response: %s", response_data)
    answer = response_data.get("choices", [{}])[0].get("text", "").strip()
    if not answer:
        LOG.error("No answer from LLM, response = %s", ollama_response.text)
        return None
    LOG.info("The answer is: %s", answer)
    return answer


def login_with_answer(answer: str) -> str:
    """Given the answer for question send POST request to login"""
    form_data = {"username": USERNAME, "password": PASSWORD, "answer": answer}
    LOG.debug("Send following request to log in: %s", form_data)
    response = requests.post(WEBSITE_URL, data=form_data, timeout=TIMEOUT_DEFAULT)
    if response.status_code != HTTPStatus.OK:
        LOG.error("Login failed, status code = %s", response.status_code)
        return None
    return response.text


def process_response(response: str) -> str:
    """Extract flags and secret link from login response"""
    flag_pattern = re.compile(r"{{FLG:[a-zA-Z0-9]+}}")
    flags = flag_pattern.findall(response)
    if flags:
        LOG.info("Flags found: %s", " ".join(flags))
    soup = BeautifulSoup(response, "html.parser")
    LOG.debug("The following response was sent after login: %s", response)
    secret_link = soup.find("a", href=True)
    if secret_link:
        LOG.info("Secret link is: %s", secret_link["href"])
        return secret_link["href"], flags
    LOG.error("No secret link found")
    return None


if __name__ == "__main__":
    current_question = get_current_question()
    current_answer = get_llm_answer(current_question)
    login_response = login_with_answer(current_answer)
    process_response(login_response)
