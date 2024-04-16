import os
from pathlib import Path

from biographer import Biographer
from gallery import Gallery
from gramps_tree import GrampsTree
from loguru import logger
from tree_render import TreeRender

if __name__ == "__main__":
    logger.info("Start")
    gramps_tree = GrampsTree()
    logger.info("The database has been read")

    content_dir = "content" if "content" in set(os.listdir()) else "../content"
    TreeRender(gramps_tree, Path(f"{content_dir}/images/tree.svg"))
    Gallery(gramps_tree).generate_gallery()
    Biographer(gramps_tree, content_dir)
