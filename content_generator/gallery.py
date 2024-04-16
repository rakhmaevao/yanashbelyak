import shutil
from pathlib import Path

from entities import GrampsId, Media
from gramps_tree import GrampsTree
from PIL import Image


class Gallery:
    _IMAGES_DIR = Path("content/images/gallery")
    _GALLERY_PAGE_PATH = Path("content/gallery/gallery.md")

    def __init__(self, gramps_tree: GrampsTree):
        self.__gramps_tree = gramps_tree
        self.__content = _GalleryPage(self._GALLERY_PAGE_PATH)

    def generate_gallery(self):
        self.__clear_gallery()
        media_by_paths = self.__regroup_media_by_paths(self.__gramps_tree.media)
        for media in media_by_paths.values():
            self.__copy_media_to_gallery(media)
            self.__content.add_image(media)
        self.__content.save()

    def __clear_gallery(self):
        shutil.rmtree(self._IMAGES_DIR, ignore_errors=True)
        self._IMAGES_DIR.mkdir()

    def __copy_media_to_gallery(self, media: Media):
        new_path = Path(shutil.copy(media.path, self._IMAGES_DIR)).absolute()
        self.__scale_image(new_path)
        media.path = new_path

    @staticmethod
    def __scale_image(
        input_image_path,
        max_width=400,
    ):
        image = Image.open(input_image_path)
        w, h = image.size
        image.thumbnail((max_width, h))
        image.save(input_image_path)

    @staticmethod
    def __regroup_media_by_paths(media: dict[GrampsId, Media]):
        result: dict[Path, Media] = {}
        for m in media.values():
            if m.path not in result:
                result[m.path] = m
            else:
                [result[m.path].mark_person(p) for p in m.persons]
        return result


class _GalleryPage:
    def __init__(self, path: Path):
        self.__content = "Title: Галерея\nCategory: Галерея\nDate: 2021-01-29 13:12\n"
        self.__path = path

    def add_image(self, media: Media):
        link = "{static}/images/gallery/" + media.path.name
        self.__content += f"![{media.description}]({link})\n\n"
        if media.persons:
            self.__content += "Люди на изображении: "
            for p in media.persons:
                self.__content += (
                    "["
                    + p.full_name
                    + "]("
                    + "{filename}../persons/"
                    + p.gramps_id
                    + ".md) "
                )
        self.__content += "\n\n---\n\n"

    def save(self):
        with self.__path.open("w", encoding="utf-8") as f:
            f.write(self.__content)
