import copy
import os
import xml.etree.ElementTree as ET
from datetime import date, datetime
from operator import attrgetter
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

import drawSvg
from db import Database, DateQuality, Family, Gender, GrampsId, Person, RelationType
from loguru import logger


class NotRightPersonException(Exception):
    pass


_Y_SPACING = 6
_X_SCALE = 0.01
_FONT_SIZE = 12
_HEIGHT = _FONT_SIZE * 1.2
_LINE_WIDTH = 0.8
_TRIANGLE_HEIGHT = 4
_TRIANGLE_WEIGHT = 4
_DASH_WEIGHT = 20
_X_OFFSET = _HEIGHT
_DAY_IN_YEAR = 365
_BIRTHDAY_ERROR_DAYS = 5 * _DAY_IN_YEAR
_DEATHDAY_ERROR_DAYS = 10 * _DAY_IN_YEAR

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


class Render:
    def __init__(self, db: Database, output_path: str):
        self.__db = db
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        self.__unpined_person = copy.deepcopy(
            self.__db.persons
        )  # type: Dict[GrampsId, Person]
        self.__older_date = self.__get_older_person(
            self.__unpined_person
        ).birth_day.date

        self.__nodes = dict()  # type: Dict[GrampsId, Node]
        self.__draw_objects = []  # type: List[drawSvg.DrawingElement]
        self.__person_id_by_label: Dict[str, GrampsId] = {}
        self.__vertical_index = -1
        while True:
            self.__vertical_index += 1
            patriarch = self.__get_patriarch(self.__unpined_person)
            if patriarch is None:
                break
            self.__add_person(patriarch)

            self.__recursively_adding_person_to_the_right(patriarch)

        family_lines = self.__create_family_lines()

        background = self.__create_background()

        draw_svg = drawSvg.Drawing(*self.__get_size())
        [draw_svg.append(obj) for obj in background]
        [draw_svg.append(obj) for obj in family_lines]
        [draw_svg.append(obj) for obj in self.__draw_objects]
        draw_svg.saveSvg(output_path)
        self.__rewrite_svg_with_hyperlink(output_path)

    @staticmethod
    def __get_triangular(y: float, x: float, direction: str) -> drawSvg.Lines:
        if direction == "down":
            return drawSvg.Lines(
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
        elif direction == "up":
            return drawSvg.Lines(
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
        else:
            raise ValueError(f"Unknown direction: {direction}")

    def __create_time_slice(
        self, label: str, date: date, date_view: bool
    ) -> List[drawSvg.DrawingElement]:
        x = self._compute_x_pos(date)
        y_max = (_HEIGHT + _Y_SPACING) * self.__vertical_index
        y_min = _HEIGHT
        ret_objects = [
            drawSvg.Lines(
                x - _DASH_WEIGHT / 2,
                y_min,
                x + _DASH_WEIGHT / 2,
                y_min,
                x,
                y_min,
                x,
                y_max,
                x + _DASH_WEIGHT / 2,
                y_max,
                x - _DASH_WEIGHT / 2,
                y_max,
                close=False,
                stroke="gray",
                stroke_width=_LINE_WIDTH,
                fill="none",
            )
        ]
        if date_view:
            ret_objects.append(
                drawSvg.Text(
                    text=str(date.year),
                    fontSize=_FONT_SIZE,
                    x=x - _FONT_SIZE * 1,
                    y=y_max + _Y_SPACING / 2,
                )
            )
        else:
            label_weight = _FONT_SIZE * 0.7 * len(label)
            ret_objects.append(
                drawSvg.Text(
                    text=label,
                    fontSize=_FONT_SIZE,
                    x=x - label_weight / 2,
                    y=y_max + _Y_SPACING / 2,
                )
            )
        return ret_objects

    def __create_background(self) -> List[drawSvg.DrawingElement]:
        background = []
        background += self.__create_time_slice("", date(1700, 1, 1), date_view=True)
        background += self.__create_time_slice("", date(1800, 1, 1), date_view=True)
        background += self.__create_time_slice("", date(1900, 1, 1), date_view=True)

        background += self.__create_time_slice(
            "ВОВ", date(1941, 6, 22), date_view=False
        )
        background += self.__create_time_slice("", date(1945, 5, 9), date_view=False)

        background += self.__create_time_slice("", date(2000, 1, 1), date_view=True)
        return background

    def __create_family_lines(self):
        family_lines = []
        for family in self.__db.families.values():
            if len(family.children) != 0 or family.is_full():
                nodes = [self.__nodes[p.id] for p in family.children] + [
                    self.__nodes[parent.id] for parent in list(family.parents)
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
                                self.__get_triangular(top_y, x_pos, "down")
                            )
                        elif node.person == lower_node.person:
                            lower_y = node.y_pos + _HEIGHT
                            family_lines.append(
                                self.__get_triangular(lower_y, x_pos, "up")
                            )
                        else:
                            family_lines.append(
                                self.__get_triangular(node.y_pos, x_pos, "down")
                            )
                            family_lines.append(
                                self.__get_triangular(node.y_pos + _HEIGHT, x_pos, "up")
                            )
                    else:
                        if node.person == top_node.person:
                            top_y = node.y_pos + _HEIGHT / 2
                        elif node.person == lower_node.person:
                            lower_y = node.y_pos + _HEIGHT / 2

                family_lines.append(
                    drawSvg.Lines(
                        x_pos,
                        lower_y,
                        x_pos,
                        top_y,
                        close=False,
                        stroke="black",
                        stroke_width=_LINE_WIDTH,
                        fill="none",
                    )
                )
        return family_lines

    def __get_size(self) -> Tuple[float, float]:
        return (
            (datetime.today().date() - self.__older_date).days * _X_SCALE
            + _X_OFFSET * 10,
            (_HEIGHT + _Y_SPACING) * (self.__vertical_index + 2),
        )

    def __get_patriarch(self, where: Dict[GrampsId, Person]):
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

    def __get_next_person(self, person: Person) -> Optional[Person]:
        child = self.__get_latest_child_by_last_partner(person)
        if child is not None:
            return child

        partner = self.__get_oldest_partner(person)
        if partner is not None:
            return partner

        logger.info(f"There are no more next people for {person}")

        return None

    def __get_latest_child_by_last_partner(self, person: Person) -> Optional[Person]:
        oldest_family = self.__get_oldest_family(person)
        if oldest_family is not None and oldest_family.children:
            un_children = []
            for child in oldest_family.children:
                un_child = self.__unpined_person.get(child.id, None)
                if un_child is not None:
                    un_children.append(un_child)
            if un_children:
                return max(un_children, key=attrgetter("birth_day.date"))

        children = []
        for relation in self.__db.relations:
            if relation.type_of_relation != RelationType.BIRTH_FROM:
                continue
            if person.id == relation.other_person_id:
                child = self.__unpined_person.get(relation.first_person_id)
                if child is None:
                    continue
                children.append(child)
        if children:
            return max(children, key=attrgetter("birth_day.date"))
        return None

    def __get_oldest_partner(self, person: Person) -> Optional[Person]:
        partners = sorted(
            self.__get_partners(person, self.__unpined_person),
            key=attrgetter("birth_day.date"),
        )
        if partners:
            return partners[-1]
        return None

    def __get_oldest_family(self, person: Person) -> Optional[Family]:
        partner = self.__get_oldest_partner(person)
        if partner is None:
            return None

        for family in self.__db.families.values():
            if person.is_male():
                if family.father == person and family.mother == partner:
                    return family
            if person.is_female():
                if family.father == partner and family.mother == person:
                    return family
        return None

    @staticmethod
    def __get_older_person(where: Dict[GrampsId, Person]) -> Person:
        persons = [p for p in where.values()]
        return min(persons, key=attrgetter("birth_day.date"))

    @staticmethod
    def __older_grandpa(where: Dict[GrampsId, Person]) -> Optional[Person]:
        mens = [p for p in where.values() if p.gender == Gender.MALE]
        if not mens:
            return None
        return min(mens, key=attrgetter("birth_day.date"))

    @staticmethod
    def __older_grandma(where: Dict[GrampsId, Person]) -> Optional[Person]:
        womens = [p for p in where.values() if p.gender == Gender.FEMALE]
        if not womens:
            return None
        return min(womens, key=attrgetter("birth_day.date"))

    def __get_partners(
        self, person: Person, where: Dict[GrampsId, Person]
    ) -> List[Person]:
        partners = []
        for relation in self.__db.relations:
            if relation.type_of_relation != RelationType.MARRIAGE:
                continue

            partner = None
            if person.id == relation.first_person_id:
                partner = where.get(relation.other_person_id)
            elif person.id == relation.other_person_id:
                partner = where.get(relation.first_person_id)

            if partner is not None:
                partners.append(partner)

        return partners

    def __add_person(self, person: Person):
        self.__vertical_index += 1
        y = (_HEIGHT + _Y_SPACING) * self.__vertical_index
        x = self._compute_x_pos(person.birth_day.date)
        width = person.days_of_life * _X_SCALE
        self.__draw_objects.append(
            drawSvg.Rectangle(
                x=x,
                y=y,
                width=width,
                height=_HEIGHT,
                stroke=_COLORS[person.gender],
                stroke_width=0.0,
                fill=_COLORS[person.gender],
            )
        )

        if person.birth_day.quality is DateQuality.ESTIMATED:
            birthday_offset = _BIRTHDAY_ERROR_DAYS * _X_SCALE
            gradient = drawSvg.LinearGradient(x - birthday_offset, y, x, y + _HEIGHT)
            gradient.addStop(0, "white", 0)
            gradient.addStop(1, _COLORS[person.gender], 1)
            self.__draw_objects.append(
                drawSvg.Rectangle(
                    x=x - birthday_offset,
                    y=y,
                    width=birthday_offset,
                    height=_HEIGHT,
                    stroke=_COLORS[person.gender],
                    stroke_width=0.0,
                    fill=gradient,
                )
            )

        if person.death_day.quality is DateQuality.ESTIMATED:
            gradient = drawSvg.LinearGradient(
                x + width, y, x + width + _DEATHDAY_ERROR_DAYS * _X_SCALE, y + _HEIGHT
            )
            gradient.addStop(0, _COLORS[person.gender], 1)
            gradient.addStop(1, "white", 0)
            self.__draw_objects.append(
                drawSvg.Rectangle(
                    x=x + width,
                    y=y,
                    width=_DEATHDAY_ERROR_DAYS * _X_SCALE,
                    height=_HEIGHT,
                    stroke=_COLORS[person.gender],
                    stroke_width=0.0,
                    fill=gradient,
                )
            )

        self.__draw_objects.append(
            drawSvg.Text(
                text=str(person), fontSize=_FONT_SIZE, x=x, y=y + (_HEIGHT - _FONT_SIZE)
            )
        )
        self.__draw_objects.append(
            drawSvg.Text(
                text=person.id,
                fontSize=_FONT_SIZE,
                x=x,
                y=y + (_HEIGHT - _FONT_SIZE),
                style="fill-opacity:0",
            )
        )
        self.__person_id_by_label[str(person)] = person.id
        del self.__unpined_person[person.id]
        logger.info(f"Added {person}")

        parental_family = self.__get_parental_family(person)
        if parental_family is not None:
            self.__draw_objects.append(
                drawSvg.Lines(
                    x,
                    y + _HEIGHT / 2,
                    self._compute_x_pos(parental_family.wedding_day),
                    y + _HEIGHT / 2,
                    close=False,
                    stroke="black",
                    stroke_width=_LINE_WIDTH,
                    fill="none",
                )
            )
        self.__nodes[person.id] = Node(person, y)

    def _compute_x_pos(self, date_: date) -> float:
        return (date_ - self.__older_date).days * _X_SCALE + _X_OFFSET

    def __get_parental_family(self, person: Person) -> Optional[Family]:
        for family in self.__db.families.values():
            if person in family.children:
                return family
        return None

    def __rewrite_svg_with_hyperlink(self, path: str):
        """
        DrawSvg не умеет в гиперссылки, поэтому уже готовый файл изменяется.
        В нем ищется скрытый текстовый блок с id персоны.
        Из него берется его координата. По этой же координате находится и label персоны.
        Блок label персоны дополняется гиперссылкой на страницу персоны.
        """
        clean_svg = []  # Массив строк svg файла без невидимых строк с id персон
        person_id_by_coordinates: Dict[Coordinates, GrampsId] = {}
        f = open(path, "r")
        for line in f:
            if line.find("<text") != -1:
                svg_struct = ET.ElementTree(ET.fromstring(line)).getroot()
                coordinates = Coordinates(
                    svg_struct.attrib["x"], svg_struct.attrib["y"]
                )
                person: Person | None = self.__db.persons.get(svg_struct.text, None)
                if person is not None:
                    person_id_by_coordinates[coordinates] = person.id
                    continue
            clean_svg.append(line)
        f.close()

        new_strings = []
        for line in clean_svg:
            if line.find("<text") != -1:
                svg_struct = ET.ElementTree(ET.fromstring(line)).getroot()
                coordinates = Coordinates(
                    svg_struct.attrib["x"], svg_struct.attrib["y"]
                )

                person_id: GrampsId | None = person_id_by_coordinates.get(
                    coordinates, None
                )
                if person_id is not None:
                    new_strings.append(
                        f'<a xlink:href="{os.getenv("SITEURL")}/{person_id}.html" target="_parent">[...]>{line}</a>'
                    )
                    continue

            new_strings.append(line)

        with open(path, "w") as file:
            for s in new_strings:
                file.write(s)


class Coordinates(NamedTuple):
    """Класс, хранящий координаты svg элемента"""

    x: str
    y: str
