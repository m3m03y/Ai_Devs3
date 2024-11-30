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
from common.prompts import EXTRACT_URLS, IMAGE_ANALYSIS
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
MARKDOWN_START = "```yml"
MARKDOWN_END = "```"


def _initialize_communication() -> tuple[str, str]:
    initialize_answer = Answer(
        task_id=TASK_ID, answer_url=AI_DEVS_URL, answer_content="START"
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
    response = response.replace(MARKDOWN_START, "").replace(MARKDOWN_END, "")
    url_lists = yaml.safe_load(response)
    LOG.debug("Urls: %s", yaml.safe_dump(url_lists))
    return url_lists


def _prepare_image_prompt(url) -> list[dict]:
    LOG.debug("Request to get image from: %s.", url)
    response = requests.get(url, timeout=TIMEOUT)

    if response.status_code != HTTPStatus.OK:
        LOG.error("Cannot get image: %s data.", url)
        raise AiDevsApiException(response.status_code, response.content)

    image = response.content
    encoded_image = image_processor.encode_image(image)
    image_data = image_processor.image_url_from_base64(encoded_image)
    LOG.debug("Image encoded in base64.")
    image_content = openai_client.build_image_content(IMAGE_ANALYSIS, image_data)
    messages = [{"role": "user", "content": image_content}]
    return messages


def _extract_image_details(url) -> str:
    messages = _prepare_image_prompt(url)
    completion = openai_client.get_first_completions(VISION_MODEL, messages)
    LOG.debug("Response from vision model: %s.", completion)
    completion = completion.replace(MARKDOWN_START, "").replace(MARKDOWN_END, "")
    response = yaml.safe_load(completion)
    if "command" in response:
        LOG.debug("Command detected: %s.", response["command"])
    elif "description" in response:
        LOG.debug("Description detected: %s.", response["description"])
    return ""


def _analyse_images(urls: str) -> str:
    for url in urls:
        _extract_image_details(url)
        break
    return ""


def get_person_description() -> dict:
    """Use Ai Assistant to enhance images quality and extract details"""
    LOG.info("Start analysis...")
    init_message, error = _initialize_communication()
    if not init_message:
        return {"error": error}
    urls = _find_all_urls(init_message)
    LOG.info("Photos: %s.", urls)
    answer = _analyse_images(urls)
    return {"FLAG": "EXAMPLE"}
