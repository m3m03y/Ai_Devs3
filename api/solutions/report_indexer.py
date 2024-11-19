"""
Solution for task 12:
Generate report embeddings, store in vector db, search relevant data
"""

import os
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, ScoredPoint

from common.file_processor import read_file, get_text_files_list
from common.prompts import GET_ANSWER_FROM_EMBEDED_DOCUMENT
from conf.logger import LOG
from task_service import send_answer
from models import Answer

RESOURCE_PATH = os.fspath(f"{os.environ["PROJECT_DIR"]}/resources/S03E02")

QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
QDRANT_URL = os.environ["QDRANT_URL"]
COLLECTION_NAME = "aidevss03e02"

AIDEVS_API_KEY = os.environ["API_KEY"]
TASK_NAME = "wektory"
VERIFY_URL = os.environ["VERIFY_URL"]

OLLAMA_URL = os.environ["OLLAMA_URL"]
EMBEDDING_MODEL = "bge-m3"
ASSISTANT_MODEL = "gpt-4o-mini"
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

PLACEHOLDER = "task_12_placeholder"

openai_client = OpenAI(base_url=OLLAMA_URL)
assistant_client = OpenAI(api_key=OPENAI_API_KEY)

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)


def _create_collection() -> None:
    qdrant_client.recreate_collection(
        COLLECTION_NAME,
        vectors_config=VectorParams(
            size=1024,
            distance=Distance.COSINE,
        ),
    )


def _embedding_documents(reports: list[str]) -> None:
    if not reports:
        LOG.warning("[TASK-12] No reports to embed.")
        return

    LOG.debug("[TASK-12] Start embedding.")
    result = openai_client.embeddings.create(input=reports, model=EMBEDDING_MODEL)
    LOG.debug("[TASK-12] Embedding of size: %d created.", len(result.data))
    points = [
        PointStruct(
            id=idx,
            vector=data.embedding,
            payload={"text": text},
        )
        for idx, (data, text) in enumerate(zip(result.data, reports))
    ]
    LOG.debug("[TASK-12] %d points created.", len(points))
    qdrant_client.upsert(COLLECTION_NAME, points)


def _search_documents(question: str) -> list[ScoredPoint]:
    result = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=openai_client.embeddings.create(
            input=[question],
            model=EMBEDDING_MODEL,
        )
        .data[0]
        .embedding,
        limit=1,
    )[0]
    LOG.debug("[TASK-12] Document search result: %s", result)
    return result


def _read_answer(scored_points: ScoredPoint, question: str) -> str:
    payload = scored_points.payload["text"]
    LOG.debug("[TASK-12] Found document\n%s.", payload)
    prompt = GET_ANSWER_FROM_EMBEDED_DOCUMENT.replace(PLACEHOLDER, payload)
    completion = assistant_client.chat.completions.create(
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
        model=ASSISTANT_MODEL,
    )
    message = completion.choices[0].message
    LOG.debug("[TASK-12] Message from assistant %s.", message)
    content = message.content
    LOG.debug("[TASK-12] Assistant response content: '%s'.", content)
    return str(content)


def report_embeddings() -> None:
    """Generate report embeddings"""
    LOG.info("[TASK-12] Start preparing embeddings...")
    files = get_text_files_list(RESOURCE_PATH, [".txt"])
    LOG.info("[TASK-12] %d reports detected.", len(files))
    reports = [f"Filename: {file}\n" + read_file(RESOURCE_PATH, file) for file in files]
    LOG.info("[TASK-12] %d reports read.", len(reports))
    _create_collection()
    LOG.info("[TASK-12] Collection created successfully.")
    _embedding_documents(reports)
    LOG.info("[TASK-12] Embeddings succesfully created.")


def get_answer(question: str) -> dict:
    """Get answer to question"""
    LOG.info("[TASK-12] Get answer to question: %s.", question)
    result = _search_documents(question)
    LOG.info("[TASK-12] Documents searched.")
    answer = _read_answer(result, question)
    LOG.info("[TASK-12] Answer: %s", answer)
    code, text = send_answer(
        Answer(task_id=TASK_NAME, answer_url=VERIFY_URL, answer_content=answer)
    )
    return {"code": code, "text": text, "answer": answer}
