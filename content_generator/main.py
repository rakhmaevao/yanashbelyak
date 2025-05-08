import os
from pathlib import Path

from loguru import logger
from src.biographer import Biographer
from src.gallery import Gallery
from src.gramps_tree import GrampsTree
from src.tree_render import TreeRender

if __name__ == "__main__":
    logger.info("Start")
    gramps_tree = GrampsTree(
        Path(
            "/home/rakhmaevao/.var/app/org.gramps_project.Gramps/data/gramps/grampsdb/yanashbelyak"
        )
    )
    logger.info("The database has been read")

    content_dir = "content" if "content" in set(os.listdir()) else "../content"
    TreeRender(gramps_tree, Path(f"{content_dir}/images/tree.svg"))
    Gallery(gramps_tree).generate_gallery()
    Biographer(gramps_tree, content_dir)
