"""Adapter for Ai Devs API"""

import os
import json
from http import HTTPStatus
import requests

from common.file_processor import read_file, save_file
from conf.logger import LOG

TIMEOUT = 30


def get_questions(url: str, dirname: str, filename: str) -> dict:
    """Get questions from url in JSON format"""
    questions_file = os.fspath(f"{dirname}/{filename}")

    if os.path.isfile(questions_file):
        try:
            questions = json.loads(read_file(dirname, filename))
            if questions:
                LOG.debug("Questions loaded from file: %s.", json.dumps(questions))
                return questions
            os.remove(questions_file)
            LOG.debug("Questions file was empty and has been deleted.")
        except json.decoder.JSONDecodeError:
            LOG.error("Could not decode questions from file.")
            os.remove(questions_file)

    try:
        questions_response = requests.get(url, timeout=TIMEOUT)
        if questions_response.status_code != HTTPStatus.OK:
            LOG.error("Could not get questions from url.")
            return None
        questions = json.loads(questions_response.text)
        LOG.debug("Questions loaded from url: %s.", json.dumps(questions))
        save_file(filename, dirname, json.dumps(questions))
        return questions
    except json.decoder.JSONDecodeError:
        LOG.error("Could not decode questions from url.")
        return None
