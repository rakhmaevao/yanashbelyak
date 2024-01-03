import datetime
from pathlib import Path
from typing import List

from entities import Person
from gramps_tree import GrampsTree


class Article:
    def __init__(
        self,
        title: str,
        date: str,
        category: str,
        tags: List[str],
        slug: str,
        main_content: str,
    ):
        self.__title = title
        self.__date = date
        self.__category = category
        self.__tags = tags
        self.__slug = slug
        self.__main_content = main_content

    def __str__(self):
        return (
            f"Title: {self.__title}\n"
            f"Date: {self.__date}\n"
            f"Category: {self.__category}\n"
            f"Tags: {self.__repr_list(self.__tags)}\n"
            f"Slug: {self.__slug}\n"
            f"{self.__main_content}"
        )

    def export_to_file(self, parent_path: Path):
        with open(f"{parent_path}/{self.__slug}.md", "w") as file:
            file.write(str(self))

    @staticmethod
    def __repr_list(list_: list) -> str:
        returned = ""
        for item in list_:
            returned += f"{item}, "
        return returned[:-2]


class Biographer:
    def __init__(self, gramps_tree: GrampsTree, content_dir: str):
        self.__gramps_tree = gramps_tree

        persons_dir = Path(f"{content_dir}/persons")
        persons_dir.mkdir(parents=True, exist_ok=True)

        for person in self.__gramps_tree.persons.values():
            article = self.__crate_article_from_person(person)
            article.export_to_file(persons_dir)

    def __crate_article_from_person(self, person: Person):
        main_content = f"Дата рождения: {person.birth_day}\n\n"
        if person.death_day.date < datetime.date.today():
            main_content += f"Дата смерти: {person.death_day}\n\n"
        main_content += self.__prepare_events(person)
        if person.notes:
            main_content += "## Заметки\n\n"
            main_content += list(person.notes)[0].content
            main_content += "\n\n"
        if person.media:
            main_content += "## Галерея\n\n"
            for media in person.media:
                link = "{static}/images/gallery/" + media.path.name
                main_content += f"![{media.description}]({link})\n\n"

        return Article(
            title=person.full_name,
            date="1100-02-21 13:12",
            category="Люди",
            tags=["Люди"],
            slug=person.id,
            main_content=main_content,
        )

    def __prepare_events(self, person) -> str:
        content = ""
        if person.events:
            for event in person.events:
                if event.date is not None and event.description != "":
                    content += f"- {event.date} {event.description}\n\n"
                if event.date is None:
                    content += f"- {event.description}\n\n"
        if content != "":
            return "## События жизни\n\n" + content
        else:
            return ""
