"""Common file functions"""

import os
import requests
from http import HTTPStatus
from conf.logger import LOG


TEXT_FILE_EXTENSION = ".txt"
TIMEOUT = 30


def get_text_files_list(dirname: str, extensions: list[str] = None) -> list[str]:
    """
    Get list of files in directory of specific type or all if no extension defined
    """
    files = []
    LOG.debug("Search files in %s dir.", dirname)
    for file in os.listdir(dirname):
        file_path = os.fspath(f"{dirname}/{file}")
        _, ext = os.path.splitext(file_path)
        if os.path.isfile(file_path) and ((ext in extensions) or (extensions is None)):
            files.append(file)
    LOG.debug("Files: %s", files)
    return files


def read_file(dirname: str, filename: str) -> str:
    """Read file content in directory"""
    full_path = os.fspath(f"{dirname}/{filename}")
    LOG.debug("Read file: %s", full_path)
    if not os.path.isfile(full_path):
        raise ValueError("Cannot read file.")
    with open(full_path, "r", encoding="UTF-8") as file:
        return file.read()


def read_remote_file(url: str) -> str:
    """Read file from specific url"""
    if not url:
        LOG.warning("Url is empty.")
        return None
    LOG.debug("Read file from remote url=%s.", url)
    response = requests.get(url, timeout=TIMEOUT)
    if response.status_code != HTTPStatus.OK:
        LOG.warning(
            "Could not get resource: %d %s",
            response.status_code,
            response.text,
        )
        return None
    LOG.debug("File read successfully.")
    return response.text


def save_file(filename: str, dirname: str, content: str) -> None:
    """Save specified data to file"""
    if not filename:
        LOG.warning("Filename is missing.")
        return None
    if not dirname:
        LOG.warning("Dirname is missing.")
        return None
    if not content:
        LOG.warning("Content is missing.")
        return None
    file_path = os.fspath(f"{dirname}/{filename}")
    with open(file_path, "w", encoding="UTF-8") as file:
        file.write(content)
    LOG.debug("File %s saved successfully.", filename)
