import pickle
import random
from enum import Enum
from datetime import date, datetime, timedelta
import sqlite3
from functools import cached_property
from typing import Tuple, List, Dict, Optional, Set
from operator import attrgetter
from singleton_decorator import singleton
from loguru import logger


class GrampsId(str):
    pass


class Gender(Enum):
    FEMALE = 0
    MALE = 1
    UNKNOWN = 2


class Person:
    __MEAN_LIFETIME = 80

    def __init__(self, id: GrampsId, full_name: str,
                 birth_day: date, death_day: date, gender: Gender):
        self.__gramps_id = GrampsId(id)
        self.__full_name = full_name
        self.__birth_day = birth_day
        self.__death_day = death_day
        self.__gender = gender

    @property
    def id(self) -> GrampsId:
        return self.__gramps_id

    @property
    def full_name(self) -> str:
        return self.__full_name

    @property
    def birth_day(self) -> date:
        if self.__birth_day is None:
            MEAN_LIFETIME = timedelta(days=365 * 75)
            if self.__death_day is None:
                return (datetime.today() - MEAN_LIFETIME).date()
            return self.__death_day - MEAN_LIFETIME
        return self.__birth_day

    @property
    def death_day(self):
        if self.__death_day is None:
            return self.__birth_day + \
                   timedelta(days=365 * self.__MEAN_LIFETIME)
        else:
            return self.__death_day

    @property
    def days_of_life(self):
        if self.__birth_day is None:
            raise ValueError
        return (self.death_day - self.__birth_day).days

    @property
    def mid_life(self) -> date:
        return (self.death_day - self.__birth_day) / 2 + self.__birth_day

    @property
    def gender(self):
        return self.__gender

    def __str__(self):
        r_year = 'н. в.'
        if self.__death_day is not None:
            r_year = self.death_day.year
        return f'{self.__full_name} ' \
               f'({self.__birth_day.year}-{r_year})'

    def is_male(self):
        return self.gender == Gender.MALE

    def is_female(self):
        return self.gender == Gender.FEMALE

    def __eq__(self, other):
        if other is None:
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class Family:
    def __init__(self, id: GrampsId):
        self.__id = id  # type: GrampsId
        self.__father = None  # type: Optional[Person]
        self.__mother = None  # type: Optional[Person]
        self.__children = set()  # type: Set[Person]

    def add_child(self, child: Person):
        self.__children.add(child)

    @property
    def id(self) -> GrampsId:
        return self.__id

    @property
    def father(self) -> Optional[Person]:
        return self.__father

    @father.setter
    def father(self, value: Person):
        self.__father = value

    @property
    def parents(self) -> Set[Person]:
        return set([person for person in [self.__father, self.__mother] if person is not None])

    @property
    def mother(self) -> Optional[Person]:
        return self.__mother

    @mother.setter
    def mother(self, value: Person):
        self.__mother = value

    @cached_property
    def wedding_day(self) -> date:
        if self.__children:
            return min(self.__children, key=attrgetter('birth_day')).birth_day - \
                   timedelta(weeks=40) - \
                   timedelta(weeks=random.randint(a=0, b=500))
        else:
            majority = 360 * 18
            parents = [self.__father, self.__mother]
            youngest = min((p.birth_day for p in parents if p is not None))
            return youngest + timedelta(days=majority)

    @property
    def children(self) -> Set[Person]:
        return self.__children

    def is_full(self) -> bool:
        return self.father is not None and self.mother is not None


class RelationType(Enum):
    MARRIAGE = 1
    BIRTH_FROM = 2
    SIMPLE = 3


class Relation:
    def __init__(self, first_person_id, type_of_relation, other_person_id,
                 family_id):
        self.first_person_id = GrampsId(first_person_id)
        self.type_of_relation = type_of_relation
        self.other_person_id = GrampsId(other_person_id)
        self.family_id = GrampsId(family_id)

    def __eq__(self, other):
        if self.first_person_id == other.first_person_id and \
                self.type_of_relation == other.type_of_relation and \
                self.other_person_id == other.other_person_id and \
                self.family_id == other.family_id:
            return True
        return False

    def __hash__(self):
        return hash(self.family_id)


class Note:
    def __init__(self, blob_data: bytes):
        fff = pickle.loads(blob_data)
        handle, gramps_id, (content, _), _, _, _, _, is_private = pickle.loads(blob_data)
        self.__content = content
        self.__id = GrampsId(gramps_id)

    @property
    def id(self) -> GrampsId:
        return self.__id

    @property
    def content(self) -> str:
        return self.__content


class EventType(Enum):
    BIRTH = 12
    DEATH = 13


@singleton
class Database:
    def __init__(self, path=r'/home/rahmaevao/.gramps/grampsdb/61d89dd1'):

        conn = sqlite3.connect(path + '/sqlite.db')
        self.__cur = conn.cursor()

        self.__persons = self.__get_persons()  # type: Dict[GrampsId, Person]

        self.__notes = self.__get_notes()  # type: Dict[GrampsId, Note]

        self.__relations, self.__families = self.__get_relationship()
        pass

    @property
    def relations(self):
        return self.__relations

    @property
    def families(self) -> Dict[GrampsId, Family]:
        return self.__families

    @property
    def persons(self) -> Dict[GrampsId, Person]:
        return self.__persons

    def __get_persons(self) -> Dict[GrampsId, Person]:
        persons = dict()
        self.__cur.execute(
            f'SELECT gramps_id, given_name, surname, gender FROM person')
        persons_raw = self.__cur.fetchall()
        for id, given_name, surname, gender in persons_raw:
            birth_day, death_day = self.__parse_lifetime(id)
            person = Person(id=id,
                            full_name=f'{given_name} {surname}',
                            birth_day=birth_day,
                            death_day=death_day,
                            gender=Gender(gender))
            persons[id] = person
        return persons

    def __parse_lifetime(self, id: GrampsId) -> Tuple[date, date]:
        self.__cur.execute(
            f'SELECT event.blob_data '
            f'FROM person '
            f'JOIN reference ON reference.obj_handle  = person.handle '
            f'JOIN event ON event.handle = reference.ref_handle '
            f'WHERE person.gramps_id = "{id}"')
        events = self.__cur.fetchall()
        birth_day, death_day = None, None
        for event, in events:
            _, _, type, r_date, _, _, _, _, _, _, _, _, _ = pickle.loads(event)
            type = type[0]

            if type == EventType.BIRTH.value:
                if r_date is None:
                    logger.error(f'The person {id} without birthday')
                    raise ValueError
                birth_day = self.__parse_date(r_date)

            if type == EventType.DEATH.value:
                if r_date is None:
                    death_day = None
                else:
                    death_day = self.__parse_date(r_date)

        return birth_day, death_day

    @staticmethod
    def __parse_date(raw_date):
        day, month, year, _ = raw_date[3]
        if day == 0:
            day = 1
        if month == 0:
            month = 1

        try:
            return date(year, month, day)
        except ValueError as message:
            logger.error(f'{message} for raw_date {raw_date}')
            raise ValueError(message)

    def __get_notes(self) -> Dict[GrampsId, Note]:
        notes = dict()
        self.__cur.execute(f'SELECT note.gramps_id, note.blob_data FROM note')
        notes_raw = self.__cur.fetchall()
        for id, blob_data in notes_raw:
            note = Note(blob_data)
            notes[id] = note
        return notes

    def __get_relationship(self) -> Tuple[Set[Relation], Dict[GrampsId, Family]]:

        self.__cur.execute(

            f'SELECT family_id,'
            f'       father_id,'
            f'       mother_id,'
            f'       person.gramps_id AS person_id FROM '
            f'( '
            f'	SELECT family_id,'
            f'         father_id,'
            f'         person.gramps_id as mother_id,'
            f'         person_handle FROM '
            f'	( '
            f'		SELECT family.gramps_id as family_id, '
            f'		       person.gramps_id as father_id, '
            f'			   family.mother_handle as mother_handle, '
            f'			   reference.ref_handle as person_handle '
            f'		FROM reference '
            f'		JOIN family ON family.handle = reference.obj_handle '
            f'		LEFT JOIN person ON person.handle = family.father_handle '
            f'		WHERE reference.ref_class = "Person" '
            f'	) '
            f'	LEFT JOIN person ON person.handle = mother_handle '
            f') '
            f'JOIN person ON person.handle = person_handle '
        )
        relations = set()
        families = dict()
        relation_raw = self.__cur.fetchall()
        for family_id, father_id, mother_id, person_id in relation_raw:
            family_id = GrampsId(family_id)
            if family_id not in families:
                families[family_id] = Family(family_id)
            if person_id == father_id and mother_id is not None:
                families[family_id].father = self.__persons[father_id]
                families[family_id].mother = self.__persons[mother_id]
                relations.add(Relation(father_id,
                                       RelationType.MARRIAGE,
                                       mother_id,
                                       family_id))
            elif person_id == mother_id and father_id is not None:
                families[family_id].father = self.__persons[father_id]
                families[family_id].mother = self.__persons[mother_id]
                relations.add(Relation(father_id,
                                       RelationType.MARRIAGE,
                                       mother_id,
                                       family_id))
            elif person_id != father_id and person_id != mother_id:
                if father_id is not None:
                    families[family_id].father = self.__persons[father_id]
                    families[family_id].add_child(self.__persons[person_id])
                    relations.add(Relation(person_id,
                                           RelationType.BIRTH_FROM,
                                           father_id,
                                           family_id))
                elif mother_id is not None:
                    families[family_id].mother = self.__persons[mother_id]
                    families[family_id].add_child(self.__persons[person_id])
                    relations.add(Relation(person_id,
                                           RelationType.BIRTH_FROM,
                                           mother_id,
                                           family_id))

        return relations, families
