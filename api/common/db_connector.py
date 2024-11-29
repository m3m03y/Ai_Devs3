"""Connector to AiDevs3 APIDB"""

import os
import json
from http import HTTPStatus
import requests
from models import DBRequest
from conf.logger import LOG

API_KEY = os.environ["API_KEY"]
TIMOUT = 30


def send_request(url: str, request: DBRequest) -> requests.Response:
    """Send query to DB API"""
    LOG.debug("Send query: %s to url: %s.", request.query, url)
    request_body = json.dumps(
        {"task": request.task_id, "apikey": API_KEY, "query": request.query}
    )
    response = requests.get(url=url, data=request_body, timeout=30)
    if response.status_code != HTTPStatus.OK:
        LOG.error("[db-connector] Request failed: %s.", response)
        return None
    return response
