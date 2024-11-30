"""
Solution for task 16:
Retrive photos, repair or change brightness, and extract details
"""

import os
import json
from http import HTTPStatus
import yaml
import requests

from adapters.groq_adapter import GroqAdapter
from adapters.openai_adapter import OpenAiAdapter
from common.exceptions import AiDevsApiException
from common.prompts import EXTRACT_URLS, IMAGE_ANALYSIS, EXTRACT_FIXED_IMAGE
import common.image_processor as image_processor
from conf.logger import LOG
from models import Answer
from task_service import send_answer

TASK_ID = "photos"
AI_DEVS_URL = os.environ["VERIFY_URL"]
TIMEOUT = 30
GENERAL_PLACEHOLDER = "placeholder"
groq_client = GroqAdapter()
local_client = OpenAiAdapter(base_url=os.environ["OLLAMA_URL"])
openai_client = OpenAiAdapter(api_key=os.environ["OPENAI_API_KEY"])

LOCAL_MODEL = "llama3.2:3b"
VISION_MODEL = "gpt-4o-mini"
MARKDOWN_SECTIONS = ["```yml", "```yaml", "```"]
PLACEHOLDER = "task_16_placeholder"


def _use_automaton(command: str) -> tuple[str, str]:
    initialize_answer = Answer(
        task_id=TASK_ID, answer_url=AI_DEVS_URL, answer_content=command
    )
    LOG.debug("Initialize answer to bot: %s.", initialize_answer)
    code, init_response = send_answer(initialize_answer)
    LOG.debug("Code: %d, Init response: %s.", code, init_response)
    if code != HTTPStatus.OK:
        LOG.error(
            "Error connecting to AiDevs Api: code=%d, response=%s.",
            code,
            init_response,
        )
        raise AiDevsApiException(code, init_response)
    try:
        response_body = json.loads(init_response)
        LOG.debug("Init message: %s.", response_body)
        code, message = response_body["code"], response_body["message"]
        if code != 0:
            LOG.error(
                "Could not initialize conversation: code=%d, message=%s.",
                code,
                message,
            )
            raise AiDevsApiException(code, message)
        return message, None
    except json.decoder.JSONDecodeError as e:
        LOG.error("Cannot decode init message: %s.", e.msg)
        return None, "Json decode failed"


def _find_all_urls(init_message: str) -> list[str]:
    messages = [
        {"role": "system", "content": EXTRACT_URLS},
        {"role": "user", "content": init_message},
    ]
    LOG.debug("Messages build: %s.", messages)
    response = local_client.get_first_completions(LOCAL_MODEL, messages)
    LOG.debug("Response from assistant: %s.", response)
    for section in MARKDOWN_SECTIONS:
        response = response.replace(section, "")
    url_lists = yaml.safe_load(response)
    LOG.debug("Urls: %s", yaml.safe_dump(url_lists))
    return url_lists


def _prepare_image_prompt(url: str, is_description: bool = False) -> list[dict]:
    prompt = IMAGE_ANALYSIS.replace(PLACEHOLDER, url)
    if is_description:
        messages = [{"role": "user", "content": prompt}]
        LOG.debug("Build only description messages: %s.", json.dumps(messages))
        return messages

    LOG.debug("Request to get image from: %s.", url)
    response = requests.get(url, timeout=TIMEOUT)

    if response.status_code != HTTPStatus.OK:
        LOG.error("Cannot get image: %s data.", url)
        raise AiDevsApiException(response.status_code, response.content)

    image = response.content
    encoded_image = image_processor.encode_image(image)
    image_data = image_processor.image_url_from_base64(encoded_image)
    LOG.debug("Image encoded in base64.")
    image_content = openai_client.build_image_content(prompt, image_data)
    messages = [{"role": "user", "content": image_content}]
    return messages


def _execute_command(command: str) -> str:
    message, error = _use_automaton(command)
    if not message:
        raise AiDevsApiException(-1, error)
    LOG.debug("Response from automaton: %s.", message)
    return message


def _extract_data_from_automaton(message: str, original_url: str) -> tuple[str, bool]:
    prompt = EXTRACT_FIXED_IMAGE.replace(PLACEHOLDER, original_url)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": message},
    ]
    LOG.debug("Messages with fixed image data: %s.", json.dumps(messages))
    completion = openai_client.get_first_completions(VISION_MODEL, messages)
    LOG.debug("Completion retrived: %s.", completion)
    for section in MARKDOWN_SECTIONS:
        completion = completion.replace(section, "")

    response = yaml.safe_load(completion)
    if "image_url" in response:
        LOG.debug("Image url detected: %s.", response["image_url"])
        return response["image_url"], False
    if "description" in response:
        LOG.debug("Description detected: %s.", response["description"])
        return response["description"], True


def _extract_image_details(
    data: str, original_url: str, is_description: bool = False
) -> tuple[str, bool]:
    messages = _prepare_image_prompt(data, is_description)
    completion = openai_client.get_first_completions(VISION_MODEL, messages)
    LOG.debug("Response from vision model: %s.", completion)
    for section in MARKDOWN_SECTIONS:
        completion = completion.replace(section, "")

    response = yaml.safe_load(completion)
    if "description" in response:
        LOG.debug("Description detected: %s.", response["description"])
        return response["description"], True
    elif "command" in response:
        LOG.debug("Command detected: %s.", response["command"])
        message = _execute_command(response["command"])
        return _extract_data_from_automaton(message, original_url)

    return None, False


def _analyse_images(urls: str) -> str:
    person_description = ""
    requests_per_url = 0
    for url in urls:
        is_description = False
        data = url
        requests_per_url = 0
        while (not is_description) and (requests_per_url < 10):
            data, is_description = _extract_image_details(data, url, is_description)
            requests_per_url += 1
        person_description += data + "\n"
    LOG.debug("Full description: %s.", person_description)
    return person_description


def get_person_description() -> dict:
    """Use Ai Assistant to enhance images quality and extract details"""
    LOG.info("Start analysis...")
    init_message, error = _use_automaton("START")
    if not init_message:
        return {"error": error}
    urls = _find_all_urls(init_message)
    LOG.info("Photos: %s.", urls)
    description = _analyse_images(urls)
    LOG.info("Barbara's description: %s...", description[:100])
    answer = Answer(task_id=TASK_ID, answer_url=AI_DEVS_URL, answer_content=description)
    code, message = send_answer(answer)
    return {"code": code, "message": message, "answer": description}
