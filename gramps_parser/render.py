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


class Node:
    _DAY_IN_CENTURY = 360 * 100
    _Y_STEP = 0.1
    _HEIGHT = 0.15
    _X_SCALE = 7
    _FONT_SIZE = '12'

    def __init__(self, y_pos):
        self._y_pos = y_pos * self._Y_STEP
        self._id = None

    def __eq__(self, other):
        if self._id == other._id:
            return True
        return False

    def _compute_x_pos(self, date: date):
        dt = (date - datetime.now().date()).days
        return self._X_SCALE * dt / self._DAY_IN_CENTURY

    @property
    def id(self):
        return self._id


class NoteNode(Node):
    def __init__(self, y_pos, date, label):
        super().__init__(y_pos)
        self._id = label + str(y_pos)
        self.__label = label
        self.__x_pos = self._compute_x_pos(date)

    def to_dot(self):
        return {'name': self._id,
                'label': f'{self.__label}',
                'shape': 'underline',
                'fontsize': self._FONT_SIZE,
                'pos': f'{self.__x_pos}, {self._y_pos}!'}


class FamilyNode(Node):

    def __init__(self, family: Family, y_pos: int):
        super().__init__(y_pos)
        self._id = family.id
        self.__x_pos = self._compute_x_pos(family.wedding_day)

    def to_dot(self):
        return {'name': self._id,
                'label': '',
                'shape': 'circle',
                'height': str(self._HEIGHT - self._Y_STEP), 'width': str(self._HEIGHT - self._Y_STEP),
                'fixedsize': 'true',
                'fontsize': self._FONT_SIZE,
                'pos': f'{self.__x_pos}, {self._y_pos}!'}


_COLORS = {Gender.MALE: 'lightblue',
           Gender.FEMALE: 'pink',
           Gender.UNKNOWN: 'LightYellow'}


class PersonNode(Node):
    # _

    def __init__(self, person: Person, y_pos: int):
        super().__init__(y_pos)
        self._id = person.id
        self.__person = person
        self.__height = self._HEIGHT
        self.__width = self._X_SCALE * person.days_of_life / self._DAY_IN_CENTURY
        self.__x_pos = self._compute_x_pos(person.mid_life)

    @property
    def person(self) -> Person:
        return self.__person

    def to_dot(self):
        return {'name': self._id,
                'label': str(self.__person),
                'style': 'filled',
                'fillcolor': self.__COLORS[self.__person.gender],
                'shape': 'box',
                'height': str(self.__height), 'width': str(self.__width),
                'fixedsize': 'true',
                'fontsize': self._FONT_SIZE,
                'pos': f'{self.__x_pos}, {self._y_pos}!'}


class Edge:
    def __init__(self, first: GrampsId,
                 type_of_relation: RelationType,
                 other: GrampsId):

        self.__first_item_id = first
        self.__other_item_id = other

        if type_of_relation == RelationType.BIRTH_FROM:
            self.__arrow = 'vee'
        elif type_of_relation == RelationType.MARRIAGE:
            self.__arrow = 'none'
        elif type_of_relation == RelationType.SIMPLE:
            self.__arrow = 'none'
        else:
            raise ValueError(f'Unknown relation type: '
                             f'{type_of_relation}')

    def __eq__(self, other):
        if self.__first_item_id == other.__first_item_id \
                and self.__other_item_id == other.__other_item_id:
            return True
        return False

    def to_dot(self):
        return {'tail_name': str(self.__other_item_id),
                'head_name': str(self.__first_item_id),
                'arrowhead': self.__arrow,
                }


class Render:
    def __init__(self, db: Database):
        self.__db = db
        self.__unpined_person = copy.deepcopy(self.__db.persons)  #type: Dict[GrampsId, Person]
        self.__older_date = self.__get_older_person(self.__unpined_person).birth_day
        self.__drawer = draw.Drawing(
            (datetime.today().date() - self.__older_date).days * _X_SCALE,
            (datetime.today().date() - self.__older_date).days * _X_SCALE
        )
        self.__vertical_index = -1
        # while True:
        self.__vertical_index += 1

        patriarch = self.__add_patriarch(self.__unpined_person, self.__vertical_index)
        new_person = self.__get_next_person(patriarch)
        self.__add_unrelated_person(new_person)
        new_person = self.__get_next_person(patriarch)
        self.__add_unrelated_person(new_person)
        # if patriarch is None:
        #     break

        # self.__recursively_adding_person_to_the_right(patriarch)
        #
        # self.__add_decor()
        # self.__to_dots()
        self.__drawer.saveSvg('content/images/tree.svg')

    def __add_patriarch(self, where: Dict[GrampsId, Person], vertical_index: int):
        patriarch = self.__older_grandpa(where)
        if patriarch is None:
            patriarch = self.__older_grandma(where)
        if patriarch is not None:
            logger.info(f'Patriarchs of a new kind found: {patriarch}')
            self.__add_unrelated_person(patriarch)
        return patriarch

    def __add_decor(self):
        self.__add_hline(date(1800, 1, 1), label='1800')
        self.__add_hline(date(1900, 1, 1), label='1900')
        self.__add_hline(date(1941, 6, 22), label='ВОВ')
        self.__add_hline(date(1945, 5, 9), label='')
        self.__add_hline(date(2000, 1, 1), label='2000')
        self.__add_hline(date(2000, 1, 1), label='2000')

    def __add_hline(self, date: date, label: str):
        n1 = NoteNode(-2, date, label)
        n2 = NoteNode(self.__ti + 2, date, label)
        self.__append_node(n1)
        self.__append_node(n2)
        self.__append_edge(Edge(n1.id, RelationType.SIMPLE, n2.id))

    def __recursively_adding_person_to_the_right(self, person: Person):
        logger.info(f'Searching the person on the right for {person}')
        while True:
            try:
                new_person = self.__get_next_person(person)
            except NotRightPersonException:
                break
            else:
                self.__recursively_adding_person_to_the_right(new_person)

    def __append_node(self, node: Node):
        found = False
        for n in self.__nodes:
            if n == node:
                found = True
        if not found:
            self.__nodes.append(node)
            if isinstance(node, PersonNode):
                del self.__unpined_person[node.id]

    def __get_next_person(self, person: Person) -> Person:
        partner = self.__get_oldest_partner(person)
        if partner is not None:
            return partner

        child = self.__get_first_child(person)
        if child is not None:
            return child

        logger.info(f'There are no more people on the right of {person}')

        raise NotRightPersonException()

    def __append_edge(self, edge: Edge):
        found = False
        for e in self.__edges:
            if e == edge:
                found = True
        if not found:
            self.__edges.append(edge)

    def __get_first_child(self, person: Person):
        for relation in self.__db.relations:
            if relation.type_of_relation != RelationType.BIRTH_FROM:
                continue
            if person.id == relation.other_person_id:
                child = self.__unpined_person.get(relation.first_person_id)
                if child is None:
                    continue
                return child
        return None

    def __get_father(self, person: Person) -> \
            Tuple[Person, Family]:

        for relation in self.__db.relations:
            if relation.type_of_relation != RelationType.BIRTH_FROM:
                continue
            if person.id == relation.first_person_id:
                parent = self.__unpined_person.get(relation.other_person_id)
                if parent is None:
                    continue
                if parent.gender == Gender.MALE:
                    return parent, self.__db.families[relation.family_id]

        return None, None

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
    def __older_grandpa(where: Dict[GrampsId, Person]) -> Person:
        mens = [p for p in where.values() if p.gender == Gender.MALE]
        if not mens:
            return None
        return min(mens, key=attrgetter('birth_day'))

    @staticmethod
    def __older_grandma(where: Dict[GrampsId, Person]) -> Person:
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
