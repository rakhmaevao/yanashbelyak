import copy
from operator import attrgetter
from typing import List, Tuple, Dict
import graphviz
from db import Person, RelationType, Database, GrampsId, Family, Gender
from datetime import datetime, date
from loguru import logger


class NotRightPersonException(Exception):
    pass


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


class PersonNode(Node):
    __COLORS = {Gender.MALE: 'lightblue',
                Gender.FEMALE: 'pink',
                Gender.UNKNOWN: 'LightYellow'}

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
        self.__unpined_person = copy.deepcopy(self.__db.persons)
        self.__dot = graphviz.Digraph(format='svg', engine='neato',
                                      graph_attr={'splines': 'line'}
                                      )
        self.__nodes, self.__edges = [], []
        self.__ti = -1
        while True:
            self.__ti += 1
            patriarch = self.__older_grandpa(self.__unpined_person)
            if patriarch is None:
                patriarch = self.__older_grandma(self.__unpined_person)
            if patriarch is None:
                break

            self.__ti += 1
            self.__append_node(PersonNode(patriarch, self.__ti))

            self.__recursively_adding_person_to_the_right(patriarch)

        self.__add_decor()
        self.__to_dots()
        self.__dot.render('content/images/tree')

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
                new_person = self.__add_person_to_the_right(person)
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

    def __add_person_to_the_right(self, person: Person) -> \
            Tuple[Person, int]:
        while True:
            ret_node = self.__add_first_child(person)
            if ret_node is not None:
                break

            ret_node = self.__add_first_partner(person)
            if ret_node is not None:
                break

            logger.info(f'There are no more people on the right of {person}')

            raise NotRightPersonException()

        self.__append_node(ret_node)
        logger.info(f'Found the person on the right: {ret_node.person}')
        return ret_node.person

    def __add_first_child(self, person: Person):
        child, family = self.__get_first_child(person)
        if child is not None:
            self.__ti += 1
            self.__append_node(FamilyNode(family, self.__ti))
            self.__append_edge(Edge(person.id,
                                    RelationType.MARRIAGE,
                                    family.id))
            self.__ti += 1
            node = PersonNode(child, self.__ti)
            self.__append_edge(Edge(child.id,
                                    RelationType.BIRTH_FROM,
                                    family.id))
            return node
        return None

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
                return child, self.__db.families[relation.family_id]

        return None, None

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

    def __add_first_partner(self, person: Person):
        ret_node = None
        partners = self.__get_partners(person, self.__unpined_person)
        if partners:
            partner, family = partners[0]
            self.__ti += 1
            self.__append_node(FamilyNode(family, self.__ti))
            self.__append_edge(
                Edge(person.id, RelationType.MARRIAGE, family.id))
            self.__ti += 1
            ret_node = PersonNode(partner, self.__ti)
            self.__append_edge(Edge(partner.id,
                                    RelationType.MARRIAGE,
                                    family.id))
        return ret_node

    def __to_dots(self):
        for node in self.__nodes:
            self.__dot.node(**node.to_dot())
        for edge in self.__edges:
            self.__dot.edge(**edge.to_dot())

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
            -> List[Tuple[Family, Person]]:
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
                partners.append((
                    partner,
                    self.__db.families[relation.family_id]))

        return partners
