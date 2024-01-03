import os

from biographer import Biographer
from gallery import Gallery
from gramps_tree import GrampsTree
from loguru import logger
from tree_render import TreeRender

if __name__ == "__main__":
    logger.info("Start")
    gramps_tree = GrampsTree()
    logger.info("The database has been read")

    if "content" in set(os.listdir()):
        content_dir = "content"
    else:
        content_dir = "../content"
    TreeRender(gramps_tree, f"{content_dir}/images/tree.svg")
    Gallery(gramps_tree).generate_gallery()
    Biographer(gramps_tree, content_dir)
