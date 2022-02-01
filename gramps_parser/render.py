import copy
from operator import attrgetter
from typing import List, Tuple, Dict, Optional
import graphviz
from db import Person, RelationType, Database, GrampsId, Family, Gender
from datetime import datetime, date
from loguru import logger
import drawSvg as draw
from operator import attrgetter


class NotRightPersonException(Exception):
    pass


_DAY_IN_CENTURY = 360 * 100
_Y_STEP = 3
_X_SCALE = 0.01
_FONT_SIZE = 12
_HEIGHT = _FONT_SIZE * 1.2
_LINE_WIDTH = 1

_COLORS = {Gender.MALE: 'lightblue',
           Gender.FEMALE: 'pink',
           Gender.UNKNOWN: 'LightYellow'}


class Render:
    def __init__(self, db: Database):
        self.__db = db
        self.__unpined_person = copy.deepcopy(self.__db.persons)  # type: Dict[GrampsId, Person]
        self.__older_date = self.__get_older_person(self.__unpined_person).birth_day
        self.__drawer = draw.Drawing(
            (datetime.today().date() - self.__older_date).days * _X_SCALE,
            (datetime.today().date() - self.__older_date).days * _X_SCALE
        )
        self.__vertical_index = -1
        while True:
            patriarch = self.__get_patriarch(self.__unpined_person, self.__vertical_index)
            if patriarch is None:
                break
            self.__add_unrelated_person(patriarch)

            self.__recursively_adding_person_to_the_right(patriarch)

        self.__drawer.saveSvg('content/images/tree.svg')

    def __get_patriarch(self, where: Dict[GrampsId, Person], vertical_index: int):
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
                self.__add_unrelated_person(new_person)
                self.__recursively_adding_person_to_the_right(new_person)
            else:
                break

    def __get_next_person(self, person: Person) -> Optional[Person]:
        child = self.__get_latest_child(person)
        if child is not None:
            return child

        partner = self.__get_oldest_partner(person)
        if partner is not None:
            return partner

        logger.info(f'There are no more next people for {person}')

        return None

    def __get_latest_child(self, person: Person) -> Optional[Person]:
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

    def __add_unrelated_person(self, person: Person):
        self.__vertical_index += 1
        self.__drawer.append(
            draw.Rectangle(
                x=self._compute_x_pos(person.birth_day),
                y=(_HEIGHT + _Y_STEP) * self.__vertical_index,
                width=person.days_of_life * _X_SCALE,
                height=_HEIGHT,
                stroke="black",
                stroke_width=_LINE_WIDTH,
                fill=_COLORS[person.gender]
            )
        )
        self.__drawer.append(
            draw.Text(
                text=str(person),
                fontSize=_FONT_SIZE,
                x=self._compute_x_pos(person.birth_day),
                y=(_HEIGHT + _Y_STEP) * self.__vertical_index + (_HEIGHT - _FONT_SIZE)
            )
        )
        del self.__unpined_person[person.id]
        logger.info(f"Added {person}")

    def _compute_x_pos(self, date_: date):
        return (date_ - self.__older_date).days * _X_SCALE
