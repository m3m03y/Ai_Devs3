"""Common logger"""

import logging
import os
import datetime

PROJECT_DIR = os.environ["PROJECT_DIR"]

log_dir = os.fspath(f"{PROJECT_DIR}/logs")

if not os.path.isdir(log_dir):
    os.mkdir(log_dir)

logfile = os.fspath(f"{log_dir}/{datetime.datetime.now()}.log")

LOG = logging.getLogger("main")

LOG.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(logfile)
console_handler = logging.StreamHandler()

file_handler.setLevel(logging.DEBUG)
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(levelname)s::%(module)s::%(funcName)s  %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

LOG.addHandler(file_handler)
LOG.addHandler(console_handler)
