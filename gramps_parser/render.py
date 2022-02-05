import copy
from operator import attrgetter
from typing import List, Tuple, Dict, Optional
from db import Person, RelationType, Database, GrampsId, Family, Gender
from datetime import datetime, date
from loguru import logger
import drawSvg
from operator import attrgetter


class NotRightPersonException(Exception):
    pass


_DAY_IN_CENTURY = 360 * 100
_Y_SPACING = 6
_X_SCALE = 0.01
_FONT_SIZE = 12
_HEIGHT = _FONT_SIZE * 1.2
_LINE_WIDTH = 1

_COLORS = {Gender.MALE: 'lightblue',
           Gender.FEMALE: 'pink',
           Gender.UNKNOWN: 'LightYellow'}


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
    def __init__(self, db: Database):
        self.__db = db
        self.__unpined_person = copy.deepcopy(self.__db.persons)  # type: Dict[GrampsId, Person]
        self.__older_date = self.__get_older_person(self.__unpined_person).birth_day

        self.__nodes = dict()  # type: Dict[GrampsId, Node]
        self.__draw_objects = []  # type: List[drawSvg.DrawingElement]
        self.__vertical_index = -1
        while True:
            self.__vertical_index += 1
            patriarch = self.__get_patriarch(self.__unpined_person)
            if patriarch is None:
                break
            self.__add_person(patriarch)

            self.__recursively_adding_person_to_the_right(patriarch)

        draw_svg = drawSvg.Drawing(*self.get_size())

        for family in self.__db.families.values():
            if len(family.children) != 0 or family.is_full():
                if family.is_full():
                    lower_y, top_y = sorted(
                        [self.__nodes[family.father.id].y_pos, self.__nodes[family.mother.id].y_pos])
                    lower_y += _HEIGHT
                else:
                    ys = [self.__nodes[p.id].y_pos for p in family.children]
                    ys.append(self.__nodes[family.parents[0].id].y_pos)
                    top_y = max(ys) + _HEIGHT / 2
                    lower_y = min(ys) + _HEIGHT

                self.__draw_objects.append(
                    drawSvg.Lines(
                        self._compute_x_pos(family.wedding_day), lower_y,
                        self._compute_x_pos(family.wedding_day), top_y,
                        close=False,
                        stroke="black",
                        stroke_width=_LINE_WIDTH,
                        fill='none'
                    )
                )

        [draw_svg.append(obj) for obj in self.__draw_objects]
        draw_svg.saveSvg('../content/images/tree.svg')

    def get_size(self) -> Tuple[float, float]:
        return (
            (datetime.today().date() - self.__older_date).days * _X_SCALE,
            (_HEIGHT + _Y_SPACING) * self.__vertical_index
        )

    def __get_patriarch(self, where: Dict[GrampsId, Person]):
        patriarch = self.__older_grandpa(where)
        if patriarch is None:
            patriarch = self.__older_grandma(where)
        if patriarch is not None:
            logger.info(f'Patriarchs of a new kind found: {patriarch}')
        return patriarch

    def __recursively_adding_person_to_the_right(self, person: Person):
        logger.info(f'Searching the next person for {person}')
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

        logger.info(f'There are no more next people for {person}')

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
                return max(un_children, key=attrgetter("birth_day"))

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
            return max(children, key=attrgetter('birth_day'))
        return None

    def __get_oldest_partner(self, person: Person) -> Optional[Person]:
        partners = sorted(self.__get_partners(person, self.__unpined_person), key=attrgetter('birth_day'))
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
        return min(persons, key=attrgetter('birth_day'))

    @staticmethod
    def __older_grandpa(where: Dict[GrampsId, Person]) -> Optional[Person]:
        mens = [p for p in where.values() if p.gender == Gender.MALE]
        if not mens:
            return None
        return min(mens, key=attrgetter('birth_day'))

    @staticmethod
    def __older_grandma(where: Dict[GrampsId, Person]) -> Optional[Person]:
        womens = [p for p in where.values() if p.gender == Gender.FEMALE]
        if not womens:
            return None
        return min(womens, key=attrgetter('birth_day'))

    def __get_partners(self, person: Person, where: Dict[GrampsId, Person]) \
            -> List[Person]:
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
        self.__draw_objects.append(
            drawSvg.Rectangle(
                x=self._compute_x_pos(person.birth_day),
                y=y,
                width=person.days_of_life * _X_SCALE,
                height=_HEIGHT,
                stroke="black",
                stroke_width=_LINE_WIDTH,
                fill=_COLORS[person.gender]
            )
        )
        self.__draw_objects.append(
            drawSvg.Text(
                text=str(person),
                fontSize=_FONT_SIZE,
                x=self._compute_x_pos(person.birth_day),
                y=y + (_HEIGHT - _FONT_SIZE)
            )
        )
        del self.__unpined_person[person.id]
        logger.info(f"Added {person}")

        parental_family = self.__get_parental_family(person)
        if parental_family is not None:
            logger.info(
                f"Finded family for {person} {(self._compute_x_pos(person.birth_day), y + _HEIGHT / 2, self._compute_x_pos(parental_family.wedding_day), y + _HEIGHT / 2)}")
            self.__draw_objects.append(
                drawSvg.Lines(
                    self._compute_x_pos(person.birth_day), y + _HEIGHT / 2,
                    self._compute_x_pos(parental_family.wedding_day), y + _HEIGHT / 2,
                    close=False,
                    stroke="black",
                    stroke_width=_LINE_WIDTH,
                    fill='none'
                )
            )
        self.__nodes[person.id] = Node(person, y)

    def _compute_x_pos(self, date_: date):
        return (date_ - self.__older_date).days * _X_SCALE

    def __get_parental_family(self, person: Person) -> Optional[Family]:
        for family in self.__db.families.values():
            if person in family.children:
                return family
        return None
