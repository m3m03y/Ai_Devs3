"""
Solution for task 10:
Process article and answer to questions
"""

import os
import io
import json
import base64
import html
from http import HTTPStatus
import requests
from groq import Groq, BadRequestError
from openai import OpenAI
from common.prompts import CONVERT_ARTICLE, DESCRIBE_FIGURE, ANSWER_ARTICLE_QUESTIONS
from conf.logger import LOG
from task_service import send_answer
from models import Answer

FILE_DIR = os.fspath(f"{os.environ["PROJECT_DIR"]}/resources/S02E05")
AUDIO_FILE_EXTENSION = ".mp3"
IMAGE_FILE_EXTENSION = ".png"
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
AIDEVS_API_KEY = os.environ["API_KEY"]
TASK_NAME = "arxiv"
VERIFY_URL = os.environ["VERIFY_URL"]
PLACEHOLDER = "task_10_article"
ARTICLE_URL = os.environ["TASK10_ARTICLE_URL"]
QUESTIONS_URL = os.environ["TASK10_QUESTIONS_URL"]
TIMEOUT = 30

groq_client = Groq(api_key=GROQ_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def _get_article() -> str:
    if not os.path.isdir(FILE_DIR):
        os.mkdir(FILE_DIR)
    filename = os.fspath(f"{FILE_DIR}/article.html")
    if not os.path.isfile(filename):
        LOG.debug("[TASK-10] File %s not exist.", filename)
        article = requests.get(url=ARTICLE_URL, timeout=30)
        LOG.debug("[TASK-10] Article content: %s", article.text)
        with open(filename, "w", encoding="UTF-8") as file:
            file.write(article.text)
            LOG.debug("[TASK-10] Article saved to file.")
        return article.text
    with open(filename, "r", encoding="UTF-8") as file:
        LOG.debug("[TASK-10] Read article from file.")
        return file.read()


def _get_questions() -> str:
    if not os.path.isdir(FILE_DIR):
        os.mkdir(FILE_DIR)
    filename = os.fspath(f"{FILE_DIR}/questions.txt")
    if not os.path.isfile(filename):
        LOG.debug("[TASK-10] File %s not exist.", filename)
        questions = requests.get(url=QUESTIONS_URL, timeout=30)
        LOG.debug("[TASK-10] Questions content: %s", questions.text)
        with open(filename, "w", encoding="UTF-8") as file:
            file.write(questions.text)
            LOG.debug("[TASK-10] Questions saved to file.")
        return questions.text
    with open(filename, "r", encoding="UTF-8") as file:
        LOG.debug("[TASK-10] Read questions from file.")
        return file.read()


def _convert_article(article: str) -> str:
    LOG.debug("[TASK-10] Remove tags, figures and audio from article.")
    prompt = CONVERT_ARTICLE.replace(PLACEHOLDER, article)
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
        ],
    )
    message = completion.choices[0].message
    LOG.debug("[TASK-10] Response from assistant: %s", message)
    content = message.content
    LOG.debug("[TASK-10] Message content: %s", content)

    try:
        response = json.loads(content)
        LOG.debug("[TASK-10] Answer from the model: %s", response)
        return response
    except json.decoder.JSONDecodeError:
        LOG.error("[TASK-10] Cannot decode model response: %s", content)
        return None


def _get_converted_article(article: str) -> str:
    if not os.path.isdir(FILE_DIR):
        os.mkdir(FILE_DIR)
    filename = os.fspath(f"{FILE_DIR}/article.json")
    if not os.path.isfile(filename):
        LOG.debug("[TASK-10] File %s not exist.", filename)
        article = _convert_article(article)
        LOG.debug("[TASK-10] Converted article content: %s", article)
        with open(filename, "w", encoding="UTF-8") as file:
            file.write(json.dumps(article))
            LOG.debug("[TASK-10] Converted article saved to file.")
        return article
    with open(filename, "r", encoding="UTF-8") as file:
        LOG.debug("[TASK-10] Read converted article from file.")
        return json.loads(file.read())


def _transcribe_audio(resource_url: str) -> str:
    LOG.debug("[TASK-10] Read audio file: %s", resource_url)
    response = requests.get(resource_url, timeout=TIMEOUT)
    if response.status_code != HTTPStatus.OK:
        raise ValueError(f"Cannot audio_file from resource url: {resource_url}")
    audio_file = response.content
    LOG.debug("[TASK-10] Transcribing audio file: %s.", resource_url)
    audio_binary = io.BytesIO(audio_file)
    audio_binary.name = "input.mp3"
    try:
        transcription = groq_client.audio.transcriptions.create(
            file=audio_binary,
            model="whisper-large-v3-turbo",
            temperature=0.1,
            language="pl",
            response_format="text",
        )
        LOG.debug("[TASK-10] Transcription content: %s", transcription)
    except BadRequestError as exception:
        LOG.error("[TASK-10] Could not transcribe audio file: %s", exception.message)
        return None
    return f"\n<AUDIO_TRANSCRIPTION>\n{transcription}\n<AUDIO_TRANSCRIPTION>\n"


def _encode_image(resource_url: str) -> str:
    response = requests.get(resource_url, timeout=TIMEOUT)

    if response.status_code != HTTPStatus.OK:
        raise ValueError(f"Cannot read image from resource url: {resource_url}")
    figure = response.content
    LOG.debug("[TASK-10] Image sucessfully read from url.")
    return base64.b64encode(figure).decode("utf-8")


def _describe_image(resource_url: str) -> str:
    LOG.debug("[TASK-10] Read figure: %s", resource_url)
    image = _encode_image(resource_url)
    LOG.debug("[TASK-10] Encoded image: %s.", image)

    try:
        LOG.debug("[TASK-10] Describe image: %s", resource_url)
        completion = groq_client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": DESCRIBE_FIGURE},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image}",
                            },
                        },
                    ],
                },
            ],
            temperature=0.1,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )

    except BadRequestError as exception:
        LOG.error("[TASK-10] Could not describe image: %s", exception.message)
        return None

    message = completion.choices[0].message
    LOG.debug("[TASK-10] Response from assistant with image description: %s", message)
    content = message.content
    LOG.debug("[TASK-10] Message content with image description: %s", content)
    return f"\n<IMAGE_DESCRIPTION>:\n{content}\n</IMAGE_DESCRIPTION>\n"


def _get_text_and_placeholders(converted_article: str) -> tuple[str, list[dict]]:
    text = converted_article["content"]
    LOG.debug("[TASK-10] Text length: %d", len(text))
    placeholders = converted_article["placeholders"]
    LOG.debug("[TASK-10] Placeholders: %s", json.dumps(placeholders))
    return text, placeholders


def _replace_text(text: str, placeholders: list[dict]) -> str:
    for placeholder in placeholders:
        LOG.debug("[TASK-10] Placeholder preparation: %s.", placeholder)
        file_path: str = placeholder["resource-url"]
        placeholder_name = placeholder["placeholder-name"]
        resource_url = f"{ARTICLE_URL}/../{file_path}"
        LOG.debug("[TASK-10] Convert resource %s into text.", file_path)
        text_representation = ""
        if file_path.endswith(IMAGE_FILE_EXTENSION):
            text_representation = _describe_image(resource_url)
        elif file_path.endswith(AUDIO_FILE_EXTENSION):
            text_representation = _transcribe_audio(resource_url)
        LOG.debug("[TASK-10] Text representation of resource: %s", text_representation)
        text = text.replace(placeholder_name, text_representation)
        LOG.debug("[TASK-10] Placeholder %s replaced successfully.", placeholder_name)
    return text


def _get_replaced_text(text: str, placeholders: list[dict]) -> str:
    if not os.path.isdir(FILE_DIR):
        os.mkdir(FILE_DIR)
    filename = os.fspath(f"{FILE_DIR}/complete_article.txt")
    if not os.path.isfile(filename):
        LOG.debug("[TASK-10] File %s not exist.", filename)
        article = _replace_text(text, placeholders)
        LOG.debug("[TASK-10] Replaced all placeholders.")
        with open(filename, "w", encoding="UTF-8") as file:
            file.write(article)
            LOG.debug("[TASK-10] Article with placeholder replaced saved to file.")
        return article
    with open(filename, "r", encoding="UTF-8") as file:
        LOG.debug("[TASK-10] Read article with all resources converted to text.")
        return file.read()


def _get_fixed_text(text: str) -> str:
    if not os.path.isdir(FILE_DIR):
        os.mkdir(FILE_DIR)
    filename = os.fspath(f"{FILE_DIR}/fixed_article.txt")
    if not os.path.isfile(filename):
        LOG.debug("[TASK-10] File %s not exist.", filename)
        article = html.unescape(text)
        LOG.debug("[TASK-10] Replaced all numeric character references.")
        with open(filename, "w", encoding="UTF-8") as file:
            file.write(article)
            LOG.debug("[TASK-10] Fixed article saved to file.")
        return article
    with open(filename, "r", encoding="UTF-8") as file:
        LOG.debug("[TASK-10] Read fixed article.")
        return file.read()


def _create_questions_dict(questions: str) -> dict:
    lines = questions.splitlines()
    LOG.debug("[TASK-10] Questions in lines: %s", lines)
    questions_dict = {}
    for line in lines:
        question_id, question_content = line.split("=", maxsplit=1)
        LOG.debug(
            "[TASK-10] Create question with id=%s and content=%s",
            question_id,
            question_content,
        )
        questions_dict[question_content] = question_id
    LOG.debug("[TASK-10] Questions in dict: %s", json.dumps(questions_dict))
    return questions_dict


def _build_messages(questions: dict, article: str):
    prompt = ANSWER_ARTICLE_QUESTIONS.replace(PLACEHOLDER, article)
    questions_prompt = "\n".join(questions.keys())
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": questions_prompt},
    ]

    LOG.debug("[TASK-10] Messages list: %s", messages)
    return messages


def _build_answers(response: dict, questions: dict) -> dict:
    answers = {}
    answers_with_questions = response["response"]
    for entry in answers_with_questions:
        question = entry["question"]
        answer = entry["answer"]
        question_id = questions[question]
        answers[question_id] = answer
    LOG.debug("[TASK-10] Answers: %s", json.dumps(answers))
    return answers


def _answer_questions(article: str, questions_str: str) -> dict:
    LOG.debug("[TASK-10] Build assistant to answer questions")
    questions = _create_questions_dict(questions_str)
    messages = _build_messages(questions, article)
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    LOG.debug("[TASK-10] Assistant choices: %s", completion.choices)
    message = completion.choices[0].message
    LOG.debug("[TASK-10] Response from assistant: %s", message)
    content = message.content
    LOG.debug("[TASK-10] Message content: %s", content)

    try:
        response = json.loads(content)
        LOG.debug("[TASK-10] Answer from the model: %s", response)
        return _build_answers(response, questions)
    except json.decoder.JSONDecodeError:
        LOG.error("[TASK-10] Cannot decode model response: %s", content)
        return None


def _send_answer(answer_content: dict) -> dict:
    code, text = send_answer(
        Answer(task_id=TASK_NAME, answer_url=VERIFY_URL, answer_content=answer_content)
    )
    return {"code": code, "text": text}


def answer_questions() -> dict:
    """Answer questions based on article information"""
    LOG.info("[TASK-10] Article reading started ...")
    article = _get_article()
    LOG.info("[TASK-10] Read article html of length: %d", len(article))
    questions = _get_questions()
    LOG.info("[TASK-10] Questions: %s", questions)
    converted_article = _get_converted_article(article)
    LOG.info(
        "[TASK-10] Article has been converted, length: %d.", len(converted_article)
    )
    text, placeholders = _get_text_and_placeholders(converted_article)
    LOG.info("[TASK-10] Text and placeholders retrived.")
    text = _get_replaced_text(text, placeholders)
    LOG.info("[TASK-10] Placeholders replaced.")
    fixed_text = _get_fixed_text(text)
    LOG.info("[TASK-10] Special characters restored.")
    answers = _answer_questions(fixed_text, questions)
    LOG.info("[TASK-10] Answers based on article: %s", json.dumps(answers))
    result = _send_answer(answers)
    LOG.info("[TASK-10] Task submission result: %s", result)
    return result
