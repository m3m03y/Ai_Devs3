"""Common logger"""

import logging
import os
import datetime

PROJECT_DIR = os.environ["PROJECT_DIR"]

log_dir = os.fspath(f"{PROJECT_DIR}/logs")

if not os.path.isdir(log_dir):
    os.mkdir(log_dir)

logfile = os.fspath(f"{log_dir}/{datetime.datetime.now()}.log")
logging.basicConfig(level=logging.INFO, filename=logfile)

LOG = logging.getLogger("main")
