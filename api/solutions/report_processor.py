"""
Solution for task 9:
Report processor
"""

import os
import io
import json
import base64
from dataclasses import dataclass
from groq import Groq, BadRequestError
from openai import OpenAI
from common.prompts import ANALYSE_REPORT
from conf.logger import LOG
from task_service import send_answer
from models import Answer

FILE_DIR = os.fspath(f"{os.environ["PROJECT_DIR"]}/resources/S02E04")
AUDIO_FILE_EXTENSION = ".mp3"
TEXT_FILE_EXTENSION = ".txt"
IMAGE_FILE_EXTENSION = ".png"
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
AIDEVS_API_KEY = os.environ["API_KEY"]
TASK_NAME = "kategorie"
VERIFY_URL = os.environ["VERIFY_URL"]
PLACEHOLDER = "task_9_context"

groq_client = Groq(api_key=GROQ_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


@dataclass(frozen=True)
class _ReportResult:
    filename: str
    label: str


def _get_file_map() -> dict:
    filenames = {"audio": [], "text": [], "image": []}
    for file in os.listdir(FILE_DIR):
        _, file_extension = os.path.splitext(os.fspath(f"{FILE_DIR}/{file}"))
        match file_extension:
            case ".mp3":
                filenames["audio"].append(file)
            case ".txt":
                filenames["text"].append(file)
            case ".png":
                filenames["image"].append(file)
    LOG.info(
        "[TASK-9] Filenames in %s directory detected: %s",
        FILE_DIR,
        json.dumps(filenames),
    )
    return filenames


def _transcribe_audio(filename: str) -> str:
    audio_filename = os.fspath(f"{FILE_DIR}/{filename}")
    LOG.debug("[TASK-9] Read audio file: %s", audio_filename)
    with open(audio_filename, "rb") as file:
        LOG.info("[TASK-9] Transcribing audio file: %s.", filename)
        audio_binary = io.BytesIO(file.read())
        audio_binary.name = "input.mp3"
        try:
            transcription = groq_client.audio.transcriptions.create(
                file=audio_binary,
                model="whisper-large-v3-turbo",
                temperature=0.1,
                language="pl",
                response_format="text",
            )
        except BadRequestError as exception:
            LOG.error("[TASK-9] Could not transcribe audio file: %s", exception.message)
            return None
    return transcription


def _encode_image(filename: str) -> str:
    with open(filename, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def _describe_image(filename: str) -> str:
    image_filename = os.fspath(f"{FILE_DIR}/{filename}")
    LOG.debug("[TASK-9] Read image: %s", image_filename)
    image = _encode_image(image_filename)
    LOG.debug("[TASK-9] Encoded image: %s.", image)

    try:
        LOG.info("[TASK-9] Describe image: %s", filename)
        completion = groq_client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe file"},
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
        LOG.error("[TASK-9] Could not describe image: %s", exception.message)
        return None

    message = completion.choices[0].message
    LOG.debug("[TASK-9] Response from assistant with image description: %s", message)
    content = message.content
    LOG.info("[TASK-9] Message content with image description: %s", content)
    return content


def _read_text_file(filename: str) -> str:
    text_filename = os.fspath(f"{FILE_DIR}/{filename}")
    LOG.info("[TASK-9] Read text file: %s", text_filename)
    with open(text_filename, "r", encoding="UTF-8") as file:
        return file.read()


def _analyse_text(text: str) -> str:
    prompt = ANALYSE_REPORT.replace(PLACEHOLDER, text)
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
        ],
    )
    message = completion.choices[0].message
    LOG.debug("[TASK-9] Response from assistant: %s", message)
    content = message.content
    LOG.info("[TASK-9] Message content: %s", content)

    try:
        response = json.loads(content)
        LOG.info("[TASK-9] Answer from the model: %s", response)
        return response
    except json.decoder.JSONDecodeError:
        LOG.error("[TASK-9] Cannot decode model response: %s", content)
        return None


def _build_report_result(response_from_ai: str, filename: str) -> _ReportResult:
    label = response_from_ai["label"]
    LOG.info("[TASK-9] File = %s, Label = %s", filename, label)
    return _ReportResult(label=label, filename=filename)


def _analyse_file(filename: str, filetype: str) -> _ReportResult:
    LOG.debug("[TASK-9] Analyze file: %s", filename)
    match filetype:
        case "audio":
            text = _transcribe_audio(filename)
        case "text":
            text = _read_text_file(filename)
        case "image":
            text = _describe_image(filename)
    analysis = _analyse_text(text)
    return _build_report_result(analysis, filename)


def _build_answer(report_results: list[_ReportResult]) -> dict:
    answer = {"people": [], "hardware": []}

    for result in report_results:
        if result.label == "people":
            answer["people"].append(result.filename)
        elif result.label == "hardware":
            answer["hardware"].append(result.filename)
    LOG.info("[TASK-9] Answer: %s", json.dumps(answer))
    return answer


def _send_answer(answer_content: dict) -> dict:
    code, text = send_answer(
        Answer(task_id=TASK_NAME, answer_url=VERIFY_URL, answer_content=answer_content)
    )
    return {"code": code, "text": text}


def report_analysis() -> dict:
    """Analyse all reports in resource directory"""
    files = _get_file_map()
    reports = []
    for _, (filetype, file_list) in enumerate(files.items()):
        for filename in file_list:
            result = _analyse_file(filename, filetype)
            reports.append(result)

    answer = _build_answer(reports)
    return _send_answer(answer)
