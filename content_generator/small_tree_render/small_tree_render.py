import os
from datetime import date
from operator import attrgetter
from pathlib import Path
from typing import NamedTuple
from xml.etree import ElementTree

import drawsvg
from loguru import logger

from content_generator.entities import (
    Family,
    Gender,
    GrampsId,
    Person,
    RelationType,
)
from content_generator.gramps_tree import GrampsTree


class UnknownDirectionError(Exception):
    def __init__(self, direction: str) -> None:
        super().__init__(f"Unknown direction: {direction}")


_X_SCALE = 0.01
_FONT_SIZE = 12
_HEIGHT = _FONT_SIZE * 1.2
_LINE_WIDTH = 0.8
_TRIANGLE_HEIGHT = 4
_TRIANGLE_WEIGHT = 4
_X_OFFSET = _HEIGHT

_COLORS = {
    Gender.MALE: "lightblue",
    Gender.FEMALE: "pink",
    Gender.UNKNOWN: "LightYellow",
}


class Node:
    def __init__(self, person: Person, y_pos: float):
        self.__person = person
        self.__y_pos = y_pos

    @property
    def person(self):
        return self.__person

    @property
    def y_pos(self):
        return self.__y_pos


class SmallTreeRender:
    _UP_GENERATION = 2
    _DOWN_GENERATION = 2
    _PERSON_WIDTH = 150
    _PERSON_HEIGHT = 50
    _Y_SPACING = 50
    _X_SPACING = 50
    _MIN_GENERATIONS = 1

    def create_svg(
        self, base_person_id: GrampsId, gramps_tree: GrampsTree, output_path: Path
    ):
        base_person = gramps_tree.persons[base_person_id]

        generations: dict[int, list[Person]] = self.__arrange_in_generation(
            base_person, gramps_tree
        )

        draw_objects = self.__draw_objects_from_generations(generations)

        draw_svg = drawsvg.Drawing(*self.__get_size(generations))
        [draw_svg.append(obj) for obj in draw_objects]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        draw_svg.save_svg(output_path)
        self.__rewrite_svg_with_hyperlink(output_path, gramps_tree)

    def __draw_objects_from_generations(self, generations: dict[int, list[Person]]):
        draw_objects = []
        for generation, persons in generations.items():
            for i, person in enumerate(persons):
                draw_objects += self.__add_person(
                    person=person, generation=generation, column=i
                )
        return draw_objects

    @staticmethod
    def __arrange_in_generation(base_person: Person, gramps_tree: GrampsTree):
        generation = {}
        for family in gramps_tree.families.values():
            if base_person in family.parents:
                if 0 not in generation:
                    generation[0] = set()
                if 1 not in generation:
                    generation[1] = set()
                [generation[0].add(person) for person in family.parents]
                [generation[1].add(person) for person in family.children]
            if base_person in family.children:
                if -1 not in generation:
                    generation[-1] = set()
                [generation[-1].add(person) for person in family.children]
        return generation

    @staticmethod
    def __get_triangular(y: float, x: float, direction: str) -> drawsvg.Lines:
        if direction == "down":
            return drawsvg.Lines(
                x - _TRIANGLE_WEIGHT / 2,
                y,
                x + _TRIANGLE_WEIGHT / 2,
                y,
                x,
                y - _TRIANGLE_HEIGHT,
                x - _TRIANGLE_WEIGHT / 2,
                y,
                close=False,
                stroke="black",
                stroke_width=_LINE_WIDTH,
                fill="none",
            )
        if direction == "up":
            return drawsvg.Lines(
                x - _TRIANGLE_WEIGHT / 2,
                y,
                x + _TRIANGLE_WEIGHT / 2,
                y,
                x,
                y + _TRIANGLE_HEIGHT,
                x - _TRIANGLE_WEIGHT / 2,
                y,
                close=False,
                stroke="black",
                stroke_width=_LINE_WIDTH,
                fill="none",
            )
        raise UnknownDirectionError(direction)

    def __create_family_lines(self):
        family_lines = []
        for family in self.__gramps_tree.families.values():
            if len(family.children) != 0 or family.is_full():
                nodes = [self.__nodes[p.gramps_id] for p in family.children] + [
                    self.__nodes[parent.gramps_id] for parent in list(family.parents)
                ]
                top_node = max(nodes, key=attrgetter("y_pos"))
                lower_node = min(nodes, key=attrgetter("y_pos"))
                top_y = None
                lower_y = None
                x_pos = self._compute_x_pos(family.wedding_day)
                for node in nodes:
                    if node.person in family.parents:
                        if node.person == top_node.person:
                            top_y = node.y_pos
                            family_lines.append(
                                self.__get_triangular(top_y, x_pos, "down"),
                            )
                        elif node.person == lower_node.person:
                            lower_y = node.y_pos + _HEIGHT
                            family_lines.append(
                                self.__get_triangular(lower_y, x_pos, "up"),
                            )
                        else:
                            family_lines.append(
                                self.__get_triangular(node.y_pos, x_pos, "down"),
                            )
                            family_lines.append(
                                self.__get_triangular(
                                    node.y_pos + _HEIGHT,
                                    x_pos,
                                    "up",
                                ),
                            )
                    elif node.person == top_node.person:
                        top_y = node.y_pos + _HEIGHT / 2
                    elif node.person == lower_node.person:
                        lower_y = node.y_pos + _HEIGHT / 2

                family_lines.append(
                    drawsvg.Lines(
                        x_pos,
                        lower_y,
                        x_pos,
                        top_y,
                        close=False,
                        stroke="black",
                        stroke_width=_LINE_WIDTH,
                        fill="none",
                    ),
                )
        return family_lines

    @classmethod
    def __get_size(cls, generations: dict[int, list[Person]]) -> tuple[float, float]:
        max_num_persons_in_generation = 0
        for generation in generations.values():
            if len(generation) > max_num_persons_in_generation:
                max_num_persons_in_generation = len(generation)
        return (
            (cls._PERSON_WIDTH + cls._X_SPACING) * max_num_persons_in_generation,
            (cls._PERSON_HEIGHT + cls._Y_SPACING) * len(generations),
        )

    def __get_patriarch(self, where: dict[GrampsId, Person]):
        patriarch = self.__older_grandpa(where)
        if patriarch is None:
            patriarch = self.__older_grandma(where)
        if patriarch is not None:
            logger.info(f"Patriarchs of a new kind found: {patriarch}")
        return patriarch

    def __recursively_adding_person_to_the_right(self, person: Person):
        logger.info(f"Searching the next person for {person}")
        while True:
            new_person = self.__get_next_person(person)
            if new_person is not None:
                self.__add_person(new_person)
                self.__recursively_adding_person_to_the_right(new_person)
            else:
                break

    def __get_next_person(self, person: Person) -> Person | None:
        child = self.__get_latest_child_by_last_partner(person)
        if child is not None:
            return child

        partner = self.__get_oldest_partner(person)
        if partner is not None:
            return partner

        logger.info(f"There are no more next people for {person}")

        return None

    def __get_latest_child_by_last_partner(self, person: Person) -> Person | None:
        oldest_family = self.__get_oldest_family(person)
        if oldest_family is not None and oldest_family.children:
            un_children = []
            for child in oldest_family.children:
                un_child = self.__unpined_person.get(child.gramps_id, None)
                if un_child is not None:
                    un_children.append(un_child)
            if un_children:
                return max(un_children, key=attrgetter("birth_day.date"))

        children = []
        for relation in self.__gramps_tree.relations:
            if relation.type_of_relation != RelationType.BIRTH_FROM:
                continue
            if person.gramps_id == relation.other_person_id:
                child = self.__unpined_person.get(relation.first_person_id)
                if child is None:
                    continue
                children.append(child)
        if children:
            return max(children, key=attrgetter("birth_day.date"))
        return None

    def __get_oldest_partner(self, person: Person) -> Person | None:
        partners = sorted(
            self.__get_partners(person, self.__unpined_person),
            key=attrgetter("birth_day.date"),
        )
        if partners:
            return partners[-1]
        return None

    def __get_oldest_family(self, person: Person) -> Family | None:
        partner = self.__get_oldest_partner(person)
        if partner is None:
            return None

        for family in self.__gramps_tree.families.values():
            if (
                person.is_male()
                and family.father == person
                and family.mother == partner
            ):
                return family
            if (
                person.is_female()
                and family.father == partner
                and family.mother == person
            ):
                return family
        return None

    @staticmethod
    def __get_older_person(where: dict[GrampsId, Person]) -> Person:
        persons = list(where.values())
        return min(persons, key=attrgetter("birth_day.date"))

    @staticmethod
    def __older_grandpa(where: dict[GrampsId, Person]) -> Person | None:
        mens = [p for p in where.values() if p.gender == Gender.MALE]
        if not mens:
            return None
        return min(mens, key=attrgetter("birth_day.date"))

    @staticmethod
    def __older_grandma(where: dict[GrampsId, Person]) -> Person | None:
        womens = [p for p in where.values() if p.gender == Gender.FEMALE]
        if not womens:
            return None
        return min(womens, key=attrgetter("birth_day.date"))

    def __get_partners(
        self,
        person: Person,
        where: dict[GrampsId, Person],
    ) -> list[Person]:
        partners = []
        for relation in self.__gramps_tree.relations:
            if relation.type_of_relation != RelationType.MARRIAGE:
                continue

            partner = None
            if person.gramps_id == relation.first_person_id:
                partner = where.get(relation.other_person_id)
            elif person.gramps_id == relation.other_person_id:
                partner = where.get(relation.first_person_id)

            if partner is not None:
                partners.append(partner)

        return partners

    def __add_person(self, person: Person, generation: int, column: int) -> list:
        y = (generation + self._MIN_GENERATIONS) * (
            self._PERSON_HEIGHT + self._Y_SPACING
        )
        x = column * (self._PERSON_WIDTH * 1.3)
        color = _COLORS[person.gender]

        draw_objects = []
        draw_objects.append(
            drawsvg.Rectangle(
                x=x,
                y=y,
                width=self._PERSON_WIDTH,
                height=self._PERSON_HEIGHT,
                fill=color,
            ),
        )
        person_label = person.full_name
        label_weight = _FONT_SIZE * 0.7 * len(person_label)
        draw_objects.append(
            drawsvg.Text(
                text=person_label,
                font_size=_FONT_SIZE,
                x=x + self._PERSON_WIDTH / 2 - label_weight / 2,
                y=y + self._PERSON_HEIGHT / 2,
            ),
        )
        draw_objects.append(
            drawsvg.Text(
                text=person.gramps_id,
                font_size=_FONT_SIZE,
                x=x + self._PERSON_WIDTH / 2 - label_weight / 2,
                y=y + self._PERSON_HEIGHT / 2,
                style="fill-opacity:0",
            ),
        )
        logger.info(f"Added {person}")
        return draw_objects

    def _compute_x_pos(self, date_: date) -> float:
        return (date_ - self.__older_date).days * _X_SCALE + _X_OFFSET

    def __get_parental_family(self, person: Person) -> Family | None:
        for family in self.__gramps_tree.families.values():
            if person in family.children:
                return family
        return None

    @staticmethod
    def __rewrite_svg_with_hyperlink(path: Path, gramps_tree: GrampsTree):
        """DrawSvg не умеет в гиперссылки, поэтому уже готовый файл изменяется.

        В нем ищется скрытый текстовый блок с id персоны.
        Из него берется его координата. По этой же координате находится и label персоны.
        Блок label персоны дополняется гиперссылкой на страницу персоны.
        """
        clean_svg = []  # Массив строк svg файла без невидимых строк с id персон
        person_id_by_coordinates: dict[Coordinates, GrampsId] = {}
        with path.open() as f:
            for line in f:
                if line.find("<text") != -1:
                    svg_struct = ElementTree.ElementTree(
                        ElementTree.fromstring(line),  # noqa: S314
                    ).getroot()
                    coordinates = Coordinates(
                        svg_struct.attrib["x"],
                        svg_struct.attrib["y"],
                    )
                    person: Person | None = gramps_tree.persons.get(
                        svg_struct.text,
                        None,
                    )
                    if person is not None:
                        person_id_by_coordinates[coordinates] = person.gramps_id
                        continue
                clean_svg.append(line)

        new_strings = []
        for line in clean_svg:
            if line.find("<text") != -1:
                svg_struct = ElementTree.ElementTree(
                    ElementTree.fromstring(line),  # noqa: S314
                ).getroot()
                coordinates = Coordinates(
                    svg_struct.attrib["x"],
                    svg_struct.attrib["y"],
                )

                person_id: GrampsId | None = person_id_by_coordinates.get(
                    coordinates,
                    None,
                )
                if person_id is not None:
                    new_strings.append(
                        f'<a xlink:href="{os.getenv("SITEURL")}/{person_id}.html" '
                        f'target="_parent">[...]>{line}</a>',
                    )
                    continue

            new_strings.append(line)

        with path.open("w") as file:
            for s in new_strings:
                file.write(s)


class Coordinates(NamedTuple):
    """Класс, хранящий координаты svg элемента."""

    x: str
    y: str
