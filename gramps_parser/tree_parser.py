import os

from biographer import Biographer
from db import Database
from loguru import logger
from render import Render

if __name__ == "__main__":
    logger.info("Start")
    db = Database()
    logger.info("The database has been read")

    if "content" in set(os.listdir()):
        content_dir = "content"
    else:
        content_dir = "../content"
    Render(db, f"{content_dir}/images/tree.svg")
    Biographer(db, content_dir)
