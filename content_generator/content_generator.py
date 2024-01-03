import os

from biographer import Biographer
from db import Database
from loguru import logger
from tree_render import TreeRender

if __name__ == "__main__":
    logger.info("Start")
    db = Database()
    logger.info("The database has been read")

    if "content" in set(os.listdir()):
        content_dir = "content"
    else:
        content_dir = "../content"
    TreeRender(db, f"{content_dir}/images/tree.svg")
    Biographer(db, content_dir)
