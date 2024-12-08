"""
Solution for task 20:
Analyse PDF notes to answer questions
"""

import os
import json
import yaml
from pypdf import PdfReader, PageObject
from qdrant_client.models import PointStruct

from adapters.openai_adapter import OpenAiAdapter
from adapters.ai_devs_adapter import get_questions
from adapters.qdrant_adapter import (
    recreate_collection,
    search_documents,
    upsert_documents,
)
from common.file_processor import read_file, save_file
from common.image_processor import image_url_from_base64, encode_image
from common.prompts import FIND_ANSWER_IN_NOTES
from conf.logger import LOG
from models import Answer
from task_service import send_answer

QUESTIONS_URL = os.environ["TASK20_QUESTIONS_URL"]
VERIFY_URL = os.environ["VERIFY_URL"]
TASK_NAME = "notes"
RESOURCE_PATH = os.fspath(f"{os.environ["PROJECT_DIR"]}/resources/S04E05")
QUESTIONS_FILENAME = "questions.json"
NOTES_FILENAME = "notatnik-rafala.pdf"
PAGE_PREFIX = "page_"

MODEL_NAME = "gpt-4o-mini"
EMBEDDING_MODEL = "bge-m3"
MARKDOWN_SECTIONS = ["```yml", "```yaml", "```"]
TIMEOUT = 30

AI_IMAGE_READ_TEXT_FILES = [[18, "1_X7.png"]]
openai_client = OpenAiAdapter(api_key=os.environ["OPENAI_API_KEY"])
local_client = OpenAiAdapter(base_url=os.environ["OLLAMA_URL"])


def _read_page_text(idx: int, page: PageObject) -> str:
    page_dir = os.fspath(f"{RESOURCE_PATH}/{PAGE_PREFIX}{idx}")
    if not os.path.isdir(page_dir):
        os.mkdir(page_dir)
        LOG.debug("Create directory: %s.", page_dir)
    page_filename = os.fspath(f"{PAGE_PREFIX}{idx}.txt")
    page_file = os.fspath(f"{page_dir}/{page_filename}")
    if not os.path.isfile(page_file):
        page_content = page.extract_text().replace("\n", " ")
        save_file(page_filename, page_dir, page_content)
        LOG.debug("Save page to file: %s. Page content:\n%s", page_file, page_content)
    return page_file


def _read_page_images(idx: int, page: PageObject) -> list[str]:
    images = []
    page_dir = os.fspath(f"{RESOURCE_PATH}/{PAGE_PREFIX}{idx}")
    if not os.path.isdir(page_dir):
        os.mkdir(page_dir)
        LOG.debug("Create directory: %s.", page_dir)

    for image_idx, image_file_object in enumerate(page.images):
        image_filename = os.fspath(f"{image_idx}_{image_file_object.name}")
        image_file = os.fspath(f"{page_dir}/{image_filename}")
        if not os.path.isfile(image_file):
            save_file(image_filename, page_dir, image_file_object.data, mode="image")
            LOG.debug("Save image to file: %s.", image_file)
        images.append(image_file)
    LOG.debug("Detected: %d imaged for page: %d", len(images), idx)
    return images


def _read_pdf() -> tuple[dict[int, list[str]], dict[int, list[str]]]:
    notes_file = os.fspath(f"{RESOURCE_PATH}/{NOTES_FILENAME}")
    reader = PdfReader(notes_file)
    pages = reader.pages
    LOG.debug("Reading file: %s, pages=%d", notes_file, len(pages))
    pages_content = {}
    images = {}
    for idx, page in enumerate(pages):
        page_text_file = _read_page_text(idx, page)
        LOG.debug("Page nr %d content file: %s.", idx, page_text_file)
        pages_content[idx] = [page_text_file]
        image_files = _read_page_images(idx, page)
        if image_files:
            images[idx] = image_files
    LOG.debug(
        "Pages read: %d. Content: %s.",
        len(pages_content.keys()),
        json.dumps(pages_content),
    )
    LOG.debug("Images files: %s.", json.dumps(images))
    return pages_content, images


def _read_text_from_image(pages: dict[int, list[str]], ai_ocr: bool = False) -> None:
    LOG.debug("AI read text from images.")
    for page, image_filename in AI_IMAGE_READ_TEXT_FILES:
        name, _ = os.path.splitext(image_filename)
        text_filename = f"{name}.txt"
        full_filename = os.fspath(
            f"{RESOURCE_PATH}/{PAGE_PREFIX}{page}/{text_filename}"
        )

        if (not os.path.isfile(full_filename)) or ai_ocr:
            image_data = read_file(
                f"{RESOURCE_PATH}/{PAGE_PREFIX}{page}", image_filename, "image"
            )
            image_url = image_url_from_base64(encode_image(image_data))

            prompt = """
            Read text from image. Return only read text.
            """
            image_content = openai_client.build_image_content(prompt, image_url)
            completion = openai_client.get_first_completions(
                MODEL_NAME, messages=[{"role": "user", "content": image_content}]
            )
            LOG.debug("Response from assistant: %s.", completion)
            name, _ = os.path.splitext(image_filename)

            image_filename = f"{name}.txt"
            save_file(image_filename, RESOURCE_PATH, completion)
            LOG.debug("Image text saved to file: %s.", image_filename)

        LOG.debug("Adding new file for entry: %d, list: %s.", page, pages[page])
        pages[page].append(full_filename)


def _read_pages(pages: dict[int, list[str]]) -> dict[int, str]:
    pages_content = {}
    for page_idx, page_list in pages.items():
        content = ""
        for page_path in page_list:
            LOG.debug("Read file %s content.", page_path)
            with open(page_path, "r", encoding="UTF-8") as file:
                content += f"{file.read()}\n"
        pages_content[page_idx] = content
    return pages_content


def _pages_embedding(pages_content: dict[int, str]):
    recreate_collection(TASK_NAME)
    LOG.debug("Collection %s created.", TASK_NAME)

    result = local_client.get_embeddings(EMBEDDING_MODEL, pages_content.values())

    points = [
        PointStruct(
            id=idx,
            vector=data.embedding,
            payload={"page_id": page_id},
        )
        for idx, (data, page_id) in enumerate(zip(result, pages_content.keys()))
    ]
    LOG.debug("%d points upserted.", len(points))
    upsert_documents(TASK_NAME, points)


def _find_question_context(questions: dict[str, str]) -> dict[str, list[int]]:
    answer_docs = {}
    for idx, question in questions.items():
        LOG.debug("Find document for question: %s.", question)
        query_vector = local_client.create_query_vector(question, EMBEDDING_MODEL)
        doc_list = search_documents(query_vector, TASK_NAME, limit=3)
        LOG.debug("Documents list: %s.", doc_list)
        page_ids = [doc.payload["page_id"] for doc in doc_list]
        LOG.debug("Find answer in documents: %s.", page_ids)
        answer_docs[idx] = page_ids
    LOG.debug("Found answers in docs: %s.", json.dumps(answer_docs))
    return answer_docs


def _answer_questions(
    questions: dict[str, str],
    answer_docs: dict[str, list[int]],
    pages_content: dict[str, str],
):
    answers = {}
    for idx, question in questions.items():
        answer_pages = answer_docs[idx]
        content_list = [pages_content[page_id] for page_id in answer_pages]
        context = "\n".join(content_list)
        LOG.debug("Content for question '%s':\n%s.", question, context)
        prompt = FIND_ANSWER_IN_NOTES.replace("_question", question).replace(
            "_context", context
        )
        completion = openai_client.get_first_completions(
            MODEL_NAME,
            messages=[{"role": "system", "content": prompt}],
        )
        for section in MARKDOWN_SECTIONS:
            completion = completion.replace(section, "")
        LOG.debug("Response from the assistant: %s.", completion)
        answer = yaml.safe_load(completion)["answer"]
        answers[idx] = answer
    LOG.debug("Answers: %s.", json.dumps(answers))
    return answers


def analyse_notes(ai_ocr: bool = False, run_embedding: bool = False) -> dict:
    """Analyse PDF notes"""
    LOG.info("Start analysis...")
    questions = get_questions(QUESTIONS_URL, RESOURCE_PATH, QUESTIONS_FILENAME)
    LOG.info("Questions loaded: %s.", json.dumps(questions))
    pages, images = _read_pdf()
    if ai_ocr:
        _read_text_from_image(pages, ai_ocr)
    LOG.info(
        "Extracted text from: %d pages. Extracted images from: %d pages.",
        len(pages.keys()),
        len(images.keys()),
    )
    pages_content = _read_pages(pages)
    if run_embedding:
        _pages_embedding(pages_content)
    answer_docs = _find_question_context(questions)
    LOG.info("Find relevant documents: %s.", json.dumps(answer_docs))
    answers = _answer_questions(questions, answer_docs, pages_content)
    LOG.info("Answers: %s.", json.dumps(answers))
    answer = Answer(task_id=TASK_NAME, answer_url=VERIFY_URL, answer_content=answers)
    code, text = send_answer(answer)
    return {"code": code, "text": text, "answer": json.dumps(answers)}
