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
            self.__copy_media_to_gallery(media)
            self.__content.add_image(media)
        self.__content.save()

    def __clear_gallery(self):
        shutil.rmtree(self._IMAGES_DIR, ignore_errors=True)
        os.mkdir(self._IMAGES_DIR)

    def __copy_media_to_gallery(self, media: Media):
        new_path = Path(shutil.copy(media.path, self._IMAGES_DIR)).absolute()
        media.path = new_path


class _GalleryPage:
    def __init__(self, path: Path):
        self.__content = (
            "Title: Галерея\n" "Category: Галерея\n" "Date: 2021-01-29 13:12\n"
        )
        self.__path = path

    def add_image(self, media: Media):
        self.__content += f"![{media.description}]({media.relative_path})\n\n"
        self.__content += media.title + "\n\n"
        if media.persons:
            self.__content += "Люди на изображении: "
            for p in media.persons:
                self.__content += (
                    "[" + p.full_name + "](" + "{filename}../persons/" + p.id + ".md) "
                )
        self.__content += "\n\n---\n\n"

    def save(self):
        with open(self.__path, "w", encoding="utf-8") as f:
            f.write(self.__content)