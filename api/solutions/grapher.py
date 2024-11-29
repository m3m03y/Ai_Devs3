"""
Solution for task 15:
Create graph and count distance.
"""

import os
import json
from neo4j import GraphDatabase, RoutingControl
from common.db_connector import send_request
from conf.logger import LOG
from models import DBRequest, Answer
from task_service import send_answer

DB_API_URL = os.environ["TASK13_DB_API_URL"]
TASK_NAME = "connections"
VERIFY_URL = os.environ["VERIFY_URL"]

GET_CONNECTIONS = """
SELECT u1.username as user1, u2.username as user2
FROM connections
    LEFT JOIN users u1 ON u1.id = user1_id
    LEFT JOIN users u2 ON u2.id = user2_id
"""
SOURCE = "user1"
TARGET = "user2"
DB_TASK_NAME = "database"

NEO4J_URI = os.environ["NEO4J_URI"]
NEO4J_AUTH = (os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
NEO4J_DATABASE = "neo4j"


def _get_connections() -> dict:
    request = DBRequest(task_id=DB_TASK_NAME, query=GET_CONNECTIONS)
    connections_response = send_request(DB_API_URL, request)
    LOG.debug("Connections response: %s.", connections_response)
    try:
        reply = json.loads(connections_response.text)
        LOG.debug("Reply content: %s.", reply)
        connections = reply["reply"]
        LOG.debug("Retrive connections: %s", json.dumps(connections))
        return connections
    except json.decoder.JSONDecodeError as e:
        LOG.error("Connections response cannot be decoded: %s", e.msg)
        return None


def _insert_connections(connections: dict) -> None:
    with GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH) as driver:
        with driver.session(database=NEO4J_DATABASE) as session:
            for connection in connections:
                session.run(
                    """
                    MERGE (u1:User {name: $user1})
                    MERGE (u2:User {name: $user2})
                    MERGE (u1)-[:CONNECTED_TO]->(u2)
                    """,
                    user1=connection[SOURCE],
                    user2=connection[TARGET],
                )
                LOG.debug(
                    "User %s added to user: %s connections.",
                    connection[TARGET],
                    connection[SOURCE],
                )


def _find_shortest_path(user_from: str, user_to: str) -> list[str]:
    with GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH) as driver:
        query = (
            "MATCH "
            "path = shortestPath((u1:User {name: $user1})-"
            "[:CONNECTED_TO*]->(u2:User {name: $user2})) "
            "RETURN path"
        )
        path = driver.execute_query(
            query,
            user1=user_from,
            user2=user_to,
            database_=NEO4J_DATABASE,
            routing_=RoutingControl.READ,
            result_transformer_=lambda r: r.value("path"),
        )
        user_names = []
        for record in path:
            LOG.debug("Path: %s", path)
            user_names = [node["name"] for node in record.nodes]
            LOG.debug(" -> ".join(user_names))
        LOG.debug("Shortest path: %s.", user_names)
        return user_names


def get_shortest_path(user_from: str, user_to: str, initialize: bool = False) -> dict:
    """Calculate shortest path between chosen users."""
    if initialize:
        LOG.info("Start creating graph...")
        connections = _get_connections()
        LOG.info("%d connections loaded.", len(connections))
        _insert_connections(connections)
        LOG.info("Data created.")
    LOG.info("Start searching shortst path...")
    shortest_path = _find_shortest_path(user_from, user_to)
    answer = ", ".join(shortest_path)
    LOG.info("Shortest path is: %s.", answer)
    code, text = send_answer(
        Answer(task_id=TASK_NAME, answer_url=VERIFY_URL, answer_content=answer)
    )
    return {"code": code, "text": text, "answer": answer}
