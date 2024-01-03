import os
import shutil

from entities import Media
from gramps_tree import GrampsTree


class Gallery:
    _IMAGES_DIR = "content/images/gallery"
    _GALLERY_PAGE_PATH = "content/gallery/gallery.md"

    def __init__(self, gramps_tree: GrampsTree):
        self.__gramps_tree = gramps_tree

    def generate_gallery(self):
        self.__clear_gallery()
        for media in self.__gramps_tree.media.values():
            self.__copy_media_to_gallery(media)

    def __clear_gallery(self):
        shutil.rmtree(self._IMAGES_DIR, ignore_errors=True)
        os.mkdir(self._IMAGES_DIR)

    def __copy_media_to_gallery(self, media: Media):
        shutil.copy(media.path, self._IMAGES_DIR)
