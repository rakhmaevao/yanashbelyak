import os
from pathlib import Path

from loguru import logger
from src.infra.tree_loader import SQliteGrampsTreeLoader
from src.presenters.biographer import Biographer
from src.presenters.gallery import Gallery
from src.presenters.tree_render import TreeRender

if __name__ == "__main__":
    logger.info("Start")
    gramps_tree = SQliteGrampsTreeLoader().load(
        Path(
            "/home/rakhmaevao/.var/app/org.gramps_project.Gramps/data/gramps/grampsdb/yanashbelyak"
        )
    )

    logger.info("The database has been read")

    content_dir = "content" if "content" in set(os.listdir()) else "../content"
    TreeRender(gramps_tree, Path(f"{content_dir}/images/tree.svg"))
    Gallery(gramps_tree).generate_gallery()
    Biographer(gramps_tree, content_dir)
