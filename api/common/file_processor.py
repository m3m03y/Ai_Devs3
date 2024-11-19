"""Common file functions"""

import os
from conf.logger import LOG


TEXT_FILE_EXTENSION = ".txt"


def get_text_files_list(dirname: str, extensions: list[str] = None) -> list[str]:
    """
    Get list of files in directory of specific type or all if no extension defined
    """
    files = []
    LOG.debug("[File-processor] Search files in %s dir.", dirname)
    for file in os.listdir(dirname):
        file_path = os.fspath(f"{dirname}/{file}")
        _, ext = os.path.splitext(file_path)
        if os.path.isfile(file_path) and ((ext in extensions) or (extensions is None)):
            files.append(file)
    LOG.debug("[File-processor] Files: %s", files)
    return files


def read_file(dirname: str, filename: str) -> str:
    """Read file content in directory"""
    full_path = os.fspath(f"{dirname}/{filename}")
    LOG.debug("[File-processor] Read file: %s", full_path)
    if not os.path.isfile(full_path):
        raise ValueError("Cannot read file.")
    with open(full_path, "r", encoding="UTF-8") as file:
        return file.read()
