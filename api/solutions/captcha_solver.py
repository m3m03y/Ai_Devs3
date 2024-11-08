"""
Solution for task 1:
Use AI model to login to service with anti-human captcha.
"""

import os
import json
from http import HTTPStatus
import requests
from openai import OpenAI
from conf.logger import LOG
from common.prompts import ROBOT_CAPTCHA, SOLVE_TASK_1

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
WEBSITE_URL = os.environ["TASK1_WEBSITE_URL"]
USERNAME = os.environ["TASK1_USERNAME"]
PASSWORD = os.environ["TASK1_PASSWORD"]
TIMEOUT = 20
PLACEHOLDER = "#task_1_page"

client = OpenAI(api_key=OPENAI_API_KEY)


def get_answer() -> tuple[str, str]:
    """Given the page context return the answer for captcha question"""
    captcha_page = requests.get(WEBSITE_URL, timeout=TIMEOUT)
    if captcha_page.status_code != HTTPStatus.OK:
        LOG.error(
            "Request to access login page failed, code = %s", captcha_page.status_code
        )
    prompt = ROBOT_CAPTCHA.replace(PLACEHOLDER, captcha_page.text)
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"URL={WEBSITE_URL}, username={USERNAME}, password={PASSWORD}",
            },
        ],
    )

    message = completion.choices[0].message
    LOG.debug("Response from assistant: %s", message)
    content = message.content
    LOG.debug("Message content: %s", content)

    try:
        response = json.loads(content)
        question, answer = response["question"], response["answer"]
        LOG.info("Question read: %s", question)
        LOG.info("Answer from the model: %s", answer)
        return question, answer
    except json.decoder.JSONDecodeError:
        LOG.error("Cannot decode model response: %s", content)
        return None


def login(answer: str, username: str = USERNAME, password: str = PASSWORD) -> str:
    """Given the answer for question send POST request to login"""
    form_data = {"username": username, "password": password, "answer": answer}
    LOG.debug("Send following request to log in: %s", form_data)
    response = requests.post(WEBSITE_URL, data=form_data, timeout=TIMEOUT)
    if response.status_code != HTTPStatus.OK:
        LOG.error("Login failed, status code = %s", response.status_code)
        return None
    return response.text


def find_hidden_data() -> tuple[str, list]:
    """Find flag and hidden links after login"""
    answer = get_answer()
    if answer is None:
        return None
    hidden_page = login(answer)
    if hidden_page is None:
        return None
    prompt = SOLVE_TASK_1.replace(PLACEHOLDER, hidden_page)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": prompt}],
    )

    message = completion.choices[0].message
    LOG.debug("Response from assistant: %s", message)
    content = message.content
    LOG.debug("Message content: %s", content)
    try:
        response = json.loads(content)
        flag, links = response["flag"], response["links"]
        LOG.info("Hidden flag is: %s", flag)

        if len(links) > 0:
            LOG.info("Hidden links list: %s", " ".join(links))

        return flag, links
    except json.decoder.JSONDecodeError:
        LOG.error("Cannot decode model response: %s", content)
        return None, []
