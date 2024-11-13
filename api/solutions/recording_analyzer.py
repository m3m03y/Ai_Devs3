"""
Solution for task 6:
Analyze audio transcriptions
"""

import os
import io
import json
from groq import Groq, BadRequestError
from openai import OpenAI
from common.prompts import TRANSCRIPTION_ANALYSIS
from conf.logger import LOG
from task_service import send_answer
from models import Answer

FILE_DIR = os.fspath(f"{os.environ["PROJECT_DIR"]}/resources/S02E01")
AUDIO_FILE_EXTENSION = ".m4a"
TEXT_FILE_EXTENSION = ".txt"
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
PLACEHOLDER = "task_6_placeholder"
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
AIDEVS_API_KEY = os.environ["API_KEY"]
TASK_NAME = "mp3"
VERIFY_URL = os.environ["VERIFY_URL"]
client = Groq(api_key=GROQ_API_KEY)

openai_client = OpenAI(api_key=OPENAI_API_KEY)


def _get_file_list(dirname: str) -> list[str]:
    if not dirname:
        raise ValueError("Invalid resource directory name")
    filenames = []
    for file in os.listdir(dirname):
        filename, file_extension = os.path.splitext(os.fspath(f"{dirname}/{file}"))
        if file_extension == AUDIO_FILE_EXTENSION:
            filenames.append(filename)
    LOG.info("[TASK-6] Filenames in %s directory detected: %s", dirname, filenames)
    return filenames


def _transcribe_audio(filename: str) -> str:
    transcription_filename = os.fspath(f"{filename}{TEXT_FILE_EXTENSION}")

    if os.path.isfile(transcription_filename):
        LOG.info(
            "[TASK-6] Transcription file: %s already exists.", transcription_filename
        )
        with open(transcription_filename, "r", encoding="UTF-8") as file:
            transcription = file.read()
        return transcription

    audio_filename = os.fspath(f"{filename}{AUDIO_FILE_EXTENSION}")
    with open(audio_filename, "rb") as file:
        LOG.info("[TASK-6] Transcribing audio file: %s.", audio_filename)
        audio_binary = io.BytesIO(file.read())
        audio_binary.name = "test.m4a"
        try:
            transcription = client.audio.transcriptions.create(
                file=audio_binary,
                model="whisper-large-v3-turbo",
                temperature=0.1,
                language="pl",
                response_format="text",
            )
        except BadRequestError as exception:
            LOG.error("[TASK-6] Could not transcribe audio file: %s", exception.message)
            return None
    with open(transcription_filename, "w", encoding="UTF-8") as file:
        file.write(transcription)
    return transcription


def _get_transcriptions(filenames: list[str]) -> list[str]:
    transcriptions = []
    for filename in filenames:
        transcription = _transcribe_audio(filename)
        if transcription is not None:
            transcriptions.append(transcription)
    LOG.info("[TASK-6] %d transcriptions created", len(transcriptions))
    return transcriptions


def _build_prompt_context(transcriptions: list[str]) -> str:
    if (transcriptions is None) or (len(transcriptions) == 0):
        return None
    return "\n".join(transcriptions)


def _build_prompt(transcriptions: list[str]) -> str:
    context = _build_prompt_context(transcriptions)
    prompt = TRANSCRIPTION_ANALYSIS.replace(PLACEHOLDER, context)
    return prompt


def _find_location(prompt: str) -> str:
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
        ],
    )
    message = completion.choices[0].message
    LOG.debug("[TASK-6] Response from assistant: %s", message)
    content = message.content
    LOG.info("[TASK-6] Message content: %s", content)

    try:
        response = json.loads(content)
        LOG.info("[TASK-6] Answer from the model: %s", response)
        return response
    except json.decoder.JSONDecodeError:
        LOG.error("[TASK-6] Cannot decode model response: %s", content)
        return None


def _send_answer(answer_content: str) -> dict:
    code, text = send_answer(
        Answer(task_id=TASK_NAME, answer_url=VERIFY_URL, answer_content=answer_content)
    )
    return {"code": code, "text": text}


def create_transcriptions() -> list[str]:
    """Create transcriptions for audio files in resources dir"""
    filenames = _get_file_list(FILE_DIR)
    transcriptions = _get_transcriptions(filenames)
    return transcriptions


def analyse_transcriptions(transcriptions: list[str]) -> str:
    """Analyse transcriptions and find location using AI"""
    prompt = _build_prompt(transcriptions)
    location_response = _find_location(prompt)
    answer = location_response["answer"]
    return _send_answer(answer)
