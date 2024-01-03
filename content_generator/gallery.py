import os
import shutil
from pathlib import Path

from entities import Media
from gramps_tree import GrampsTree


class Gallery:
    _IMAGES_DIR = "content/images/gallery"
    _GALLERY_PAGE_PATH = Path("content/gallery/gallery.md")

    def __init__(self, gramps_tree: GrampsTree):
        self.__gramps_tree = gramps_tree
        self.__content = _GalleryPage(self._GALLERY_PAGE_PATH)

    def generate_gallery(self):
        self.__clear_gallery()
        for media in self.__gramps_tree.media.values():
            new_path = self.__copy_media_to_gallery(media)
            self.__content.add_image(media, new_path)
        self.__content.save()

    def __clear_gallery(self):
        shutil.rmtree(self._IMAGES_DIR, ignore_errors=True)
        os.mkdir(self._IMAGES_DIR)

    def __copy_media_to_gallery(self, media: Media) -> Path:
        return Path(shutil.copy(media.path, self._IMAGES_DIR)).absolute()


class _GalleryPage:
    def __init__(self, path: Path):
        self.__content = ("Title: Галерея\n"
                          "Category: Галерея\n"
                          "Date: 2021-01-29 13:12\n"
                          )
        self.__path = path

    def add_image(self, media: Media, new_path: Path):
        self.__content += f"![{media.description}]({self.__relative_path(new_path)})\n\n"
        self.__content += media.title + "\n\n"

    def save(self):
        with open(self.__path, "w", encoding="utf-8") as f:
            f.write(self.__content)

    @staticmethod
    def __relative_path(image_path: Path):
        return "../" + str(image_path.relative_to(image_path.parent.parent.parent))
