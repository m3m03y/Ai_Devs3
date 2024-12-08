"""Adapter for Qdrant interface"""

import os

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, ScoredPoint

from conf.logger import LOG

QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
QDRANT_URL = os.environ["QDRANT_URL"]

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)


def recreate_collection(
    name: str, size: int = 1024, distance: Distance = Distance.COSINE
) -> None:
    """Recreaet collection in Qdrant"""
    qdrant_client.recreate_collection(
        name,
        vectors_config=VectorParams(
            size=size,
            distance=distance,
        ),
    )
    LOG.debug("Recreate %s collection.", name)


def upsert_documents(collection_name: str, points: list[PointStruct]):
    """Update or insert documents"""
    qdrant_client.upsert(collection_name, points)
    LOG.debug("%d points inserted to collection: %s.", len(points), collection_name)


def search_documents(
    query_vector: str, collection_name: str, limit: int = 1
) -> list[ScoredPoint]:
    """Search documents based on query"""
    result = qdrant_client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit,
    )
    LOG.debug("Result of '%s' query search: %s", query_vector, result)
    return result
