"""
Solution for task 19:
Webhook to move through grid
"""

import os
import yaml

from adapters.openai_adapter import OpenAiAdapter
from common.prompts import FIND_POSITION
from conf.logger import LOG
from models import Answer, Instruction
from task_service import send_answer

VERIFY_URL = os.environ["VERIFY_URL"]

TASK_NAME = "webhook"

MODEL_NAME = "gpt-4o-mini"

MARKDOWN_SECTIONS = ["```yml", "```yaml", "```"]

TIMEOUT = 30

GRID = [
    ["START", "trawa", "drzewo", "dom"],
    ["trawa", "wiatrak", "trawa", "trawa"],
    ["trwa", "trawa", "skały", "drzewa"],
    ["skały", "skały", "auto", "jaskinia"],
]

openai_client = OpenAiAdapter(api_key=os.environ["OPENAI_API_KEY"])


def get_details(instruction: Instruction) -> dict:
    """Get field details based on instruction"""
    messages = [
        {"role": "system", "content": FIND_POSITION},
        {"role": "user", "content": instruction.instruction},
    ]
    LOG.debug("Build messages: %s.", messages)
    completion = openai_client.get_first_completions(MODEL_NAME, messages)
    for section in MARKDOWN_SECTIONS:
        completion.replace(section, "")
    LOG.debug("Response from assistant: %s.", completion)
    response = yaml.safe_load(completion)
    position = response["position"]
    y, x = position[0], position[1]
    description = GRID[x][y]
    LOG.info(
        "Instruction: %s, position: %s, description: %s.",
        instruction.instruction,
        position,
        description,
    )
    return {"description": description}


def send_webhook_url(webhook_url: str) -> dict:
    """Send webhook url"""
    LOG.info("Sending answers to: %s.", webhook_url)
    answer = Answer(
        task_id=TASK_NAME, answer_url=VERIFY_URL, answer_content=webhook_url
    )
    code, text = send_answer(answer)
    return {"code": code, "text": text}
