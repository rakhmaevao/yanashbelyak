import os
from operator import attrgetter
from pathlib import Path
from typing import NamedTuple
from xml.etree import ElementTree

import drawsvg
from loguru import logger

from content_generator.entities import (
    Gender,
    GrampsId,
    Person,
)
from content_generator.gramps_tree import GrampsTree


class UnknownDirectionError(Exception):
    def __init__(self, direction: str) -> None:
        super().__init__(f"Unknown direction: {direction}")


class _Coordinates(NamedTuple):
    """Класс, хранящий координаты svg элемента."""

    x: str
    y: str


_COLORS = {
    Gender.MALE: "lightblue",
    Gender.FEMALE: "pink",
    Gender.UNKNOWN: "LightYellow",
}


class _PartnerRelation(NamedTuple):
    partner: Person
    children: list[Person]


class SmallTreeRender:
    _UP_GENERATION = 2
    _DOWN_GENERATION = 2
    _PERSON_WIDTH = 150
    _PERSON_HEIGHT = 50
    _Y_SPACING = 50
    _X_SPACING = 50
    _FONT_SIZE = 12
    _LINE_WIDTH = 0.8

    def create_svg(
        self, base_person_id: GrampsId, gramps_tree: GrampsTree, output_path: Path
    ):
        base_person = gramps_tree.persons[base_person_id]

        panther_relations, parents = self.__create_relationships(
            base_person, gramps_tree
        )

        generations: dict[int, list[Person]] = self.__arrange_in_generation(
            base_person, gramps_tree
        )

        draw_objects = self.__draw_objects(base_person, panther_relations, parents)

        draw_svg = drawsvg.Drawing(*self.__get_size(generations))
        [draw_svg.append(obj) for obj in sorted(draw_objects, key=self.__do_comparator)]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        draw_svg.save_svg(output_path)
        self.__rewrite_svg_with_hyperlink(output_path, gramps_tree)

    def __do_comparator(self, obj):
        return str(type(obj))

    def __create_relationships(
        self, base_person: Person, gramps_tree: GrampsTree
    ) -> tuple[list[_PartnerRelation], list[Person]]:
        partner_relations = []
        parents = []
        for family in gramps_tree.families.values():
            if base_person in family.parents:
                partner = family.mother if base_person.is_male() else family.father
                partner_relations.append(
                    _PartnerRelation(partner=partner, children=family.children)
                )
            if base_person in family.children:
                parents.append(family.father)
                parents.append(family.mother)
        return partner_relations, parents

    def __draw_objects(
        self,
        base_person: Person,
        panther_relations: list[_PartnerRelation],
        parents: list[Person],
    ):
        draw_objects = []
        for i, parent in enumerate(sorted(parents, key=attrgetter("gender.value"))):
            draw_objects += self.__add_person(person=parent, generation=0, column=i)
        draw_objects += self.__create_relationships_line(
            generation=0, left_column=0, right_column=1
        )

        draw_objects += self.__add_person(base_person, generation=1, column=0)
        draw_objects += self.__create_parents_line(
            up_generation=0, down_generation=1, right_parent_column=1, child_column=0
        )

        relationship_column = 1
        old_relationship_column = relationship_column
        for panther_relation in panther_relations:
            draw_objects += self.__add_person(
                panther_relation.partner, generation=1, column=relationship_column
            )
            this_partner_column = relationship_column
            draw_objects += self.__create_relationships_line(
                generation=1, left_column=0, right_column=this_partner_column
            )
            for i, child in enumerate(panther_relation.children):
                draw_objects += self.__add_person(person=child, generation=2, column=i)
                draw_objects += self.__create_parents_line(
                    up_generation=1,
                    down_generation=2,
                    right_parent_column=this_partner_column,
                    child_column=i,
                )
                relationship_column += 1
            if relationship_column == old_relationship_column:
                relationship_column += 1
                old_relationship_column = relationship_column

        return draw_objects

    def __create_parents_line(
        self,
        up_generation: int,
        down_generation: int,
        right_parent_column: int,
        child_column: int,
    ):
        return [
            drawsvg.Lines(
                right_parent_column * (self._PERSON_WIDTH + self._X_SPACING)
                - self._X_SPACING / 2,
                (
                    up_generation * (self._PERSON_HEIGHT + self._Y_SPACING)
                    + self._PERSON_HEIGHT / 2
                ),
                child_column * (self._PERSON_WIDTH + self._X_SPACING)
                + self._PERSON_WIDTH / 2,
                (down_generation * (self._PERSON_HEIGHT + self._Y_SPACING)),
                close=False,
                stroke="gray",
                stroke_width=self._LINE_WIDTH,
                fill="none",
            )
        ]

    def __create_relationships_line(
        self, generation: int, left_column: int, right_column: int
    ):
        y = (
            generation * (self._PERSON_HEIGHT + self._Y_SPACING)
            + self._PERSON_HEIGHT / 2
        )
        return [
            drawsvg.Lines(
                left_column * (self._PERSON_WIDTH) + self._PERSON_WIDTH,
                y,
                right_column * (self._PERSON_WIDTH + self._X_SPACING),
                y,
                close=False,
                stroke="black",
                stroke_width=self._LINE_WIDTH,
                fill="none",
            )
        ]

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

    def __add_person(self, person: Person, generation: int, column: int) -> list:
        y = generation * (self._PERSON_HEIGHT + self._Y_SPACING)
        x = column * (self._PERSON_WIDTH + self._X_SPACING)
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
        label_weight = self._FONT_SIZE * 0.7 * len(person_label)
        draw_objects.append(
            drawsvg.Text(
                text=person_label,
                font_size=self._FONT_SIZE,
                x=x + self._PERSON_WIDTH / 2 - label_weight / 2,
                y=y + self._PERSON_HEIGHT / 2,
            ),
        )
        draw_objects.append(
            drawsvg.Text(
                text=person.gramps_id,
                font_size=self._FONT_SIZE,
                x=x + self._PERSON_WIDTH / 2 - label_weight / 2,
                y=y + self._PERSON_HEIGHT / 2,
                style="fill-opacity:0",
            ),
        )
        logger.info(f"Added {person}")
        return draw_objects

    @staticmethod
    def __rewrite_svg_with_hyperlink(path: Path, gramps_tree: GrampsTree):
        """DrawSvg не умеет в гиперссылки, поэтому уже готовый файл изменяется.

        В нем ищется скрытый текстовый блок с id персоны.
        Из него берется его координата. По этой же координате находится и label персоны.
        Блок label персоны дополняется гиперссылкой на страницу персоны.
        """
        clean_svg = []  # Массив строк svg файла без невидимых строк с id персон
        person_id_by_coordinates: dict[_Coordinates, GrampsId] = {}
        with path.open() as f:
            for line in f:
                if line.find("<text") != -1:
                    svg_struct = ElementTree.ElementTree(
                        ElementTree.fromstring(line),  # noqa: S314
                    ).getroot()
                    coordinates = _Coordinates(
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
                coordinates = _Coordinates(
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
