"""
Solution for task 20:
Analyse PDF notes to answer questions
"""

import os
import json
from pypdf import PdfReader, PageObject

from adapters.openai_adapter import OpenAiAdapter
from adapters.ai_devs_adapter import get_questions
from common.file_processor import read_file, save_file
from conf.logger import LOG

QUESTIONS_URL = os.environ["TASK20_QUESTIONS_URL"]
VERIFY_URL = os.environ["VERIFY_URL"]
TASK_NAME = "notes"
RESOURCE_PATH = os.fspath(f"{os.environ["PROJECT_DIR"]}/resources/S04E05")
QUESTIONS_FILENAME = "questions.json"
NOTES_FILENAME = "notatnik-rafala.pdf"
PAGE_PREFIX = "page_"

MODEL_NAME = "gpt-4o-mini"
MARKDOWN_SECTIONS = ["```yml", "```yaml", "```"]
TIMEOUT = 30


openai_client = OpenAiAdapter(api_key=os.environ["OPENAI_API_KEY"])


def _read_page_text(idx: int, page: PageObject) -> str:
    page_dir = os.fspath(f"{RESOURCE_PATH}/{PAGE_PREFIX}{idx}")
    if not os.path.isdir(page_dir):
        os.mkdir(page_dir)
        LOG.debug("Create directory: %s.", page_dir)
    page_filename = os.fspath(f"{PAGE_PREFIX}{idx}.txt")
    page_file = os.fspath(f"{page_dir}/{page_filename}")
    if not os.path.isfile(page_file):
        page_content = page.extract_text()
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


def _read_pdf() -> tuple[dict[int, str], dict[int, list[str]]]:
    notes_file = os.fspath(f"{RESOURCE_PATH}/{NOTES_FILENAME}")
    reader = PdfReader(notes_file)
    pages = reader.pages
    LOG.debug("Reading file: %s, pages=%d", notes_file, len(pages))
    pages_content = {}
    images = {}
    for idx, page in enumerate(pages):
        page_text_file = _read_page_text(idx, page)
        LOG.debug("Page nr %d content file: %s.", idx, page_text_file)
        pages_content[idx] = page_text_file
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


def analyse_notes() -> dict:
    """Analyse PDF notes"""
    LOG.info("Start analysis...")
    questions = get_questions(QUESTIONS_URL, RESOURCE_PATH, QUESTIONS_FILENAME)
    LOG.info("Questions loaded: %s.", json.dumps(questions))
    pages, images = _read_pdf()
    LOG.info(
        "Extracted text from: %d pages. Extracted images from: %d pages.",
        len(pages.keys()),
        len(images.keys()),
    )
    return {"placeholder": "placeholder"}
