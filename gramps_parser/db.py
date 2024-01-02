from __future__ import annotations

import locale
import pickle
import random
import sqlite3
from datetime import date, timedelta
from enum import Enum
from functools import cached_property
from operator import attrgetter

from loguru import logger
from singleton_decorator import singleton

locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")  # the ru locale is installed


class DateQuality(Enum):
    EXACTLY = 0
    ESTIMATED = 1

    def __str__(self):
        if self == DateQuality.EXACTLY:
            return ""
        elif self == DateQuality.ESTIMATED:
            return "≈ "


class Date:
    def __init__(self, date: date, quality: DateQuality):
        self.__date = date
        self.__quality = quality

    @staticmethod
    def from_gramps_db(raw_date: tuple) -> Date:
        logger.debug(f"Parsing date: {raw_date}")
        day, month, year, _ = raw_date[3]
        if day == 0:
            day = 1
        if month == 0:
            month = 1

        try:
            return Date(date(year, month, day), DateQuality(raw_date[2]))
        except ValueError as message:
            logger.error(f"{message} for raw_date {raw_date}")
            raise ValueError(message)

    @property
    def date(self) -> date:
        return self.__date

    @property
    def quality(self) -> DateQuality:
        return self.__quality

    @quality.setter
    def quality(self, quality: DateQuality):
        self.__quality = quality

    def __str__(self) -> str:
        return f"{self.quality}{self.date.strftime('%d %B %Y')}"


class GrampsId(str):
    pass


class Note:
    def __init__(self, blob_data: bytes):
        handle, gramps_id, (content, _), _, _, _, _, is_private = pickle.loads(
            blob_data
        )
        self.__content = content
        self.__id = GrampsId(gramps_id)

    @property
    def id(self) -> GrampsId:
        return self.__id

    @property
    def content(self) -> str:
        return self.__content


class Gender(Enum):
    FEMALE = 0
    MALE = 1
    UNKNOWN = 2


class Person:
    __MAX_LIFETIME_Y = 100

    def __init__(
        self,
        id: GrampsId,
        full_name: str,
        birth_day: Date,
        death_day: Date,
        gender: Gender,
    ):
        self.__gramps_id = GrampsId(id)
        self.__full_name: str = full_name
        self.__birth_day: Date = birth_day
        if death_day is None:
            death_day = self.__birth_day.date + timedelta(
                days=365 * self.__MAX_LIFETIME_Y
            )
            self.__death_day = Date(death_day, DateQuality.ESTIMATED)
        else:
            self.__death_day = death_day
        self.__gender: Gender = gender
        self.__notes: set[Note] = set()

    def add_note(self, note: Note):
        self.__notes.add(note)

    @property
    def id(self) -> GrampsId:
        return self.__gramps_id

    @property
    def full_name(self) -> str:
        return self.__full_name

    @property
    def birth_day(self) -> Date:
        return self.__birth_day

    @property
    def death_day(self) -> Date:
        return self.__death_day

    @property
    def days_of_life(self) -> int:
        if self.__birth_day is None:
            raise ValueError
        return (self.death_day.date - self.__birth_day.date).days

    @property
    def mid_life(self) -> date:
        return (self.death_day.date - self.__birth_day.date) / 2 + self.__birth_day.date

    @property
    def gender(self):
        return self.__gender

    @property
    def notes(self) -> set[Note]:
        return self.__notes

    def __str__(self):
        if self.death_day.date > date.today():
            right_year = "н. в."
        else:
            right_year = self.death_day.date.year

        return f"{self.__full_name} " f"({self.__birth_day.date.year}-{right_year})"

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
        self.__father = None  # type: Person | None
        self.__mother = None  # type: Person | None
        self.__children = set()  # type: set[Person]

    def add_child(self, child: Person):
        self.__children.add(child)

    @property
    def id(self) -> GrampsId:
        return self.__id

    @property
    def father(self) -> Person | None:
        return self.__father

    @father.setter
    def father(self, value: Person):
        self.__father = value

    @property
    def parents(self) -> set[Person]:
        return set(
            [person for person in [self.__father, self.__mother] if person is not None]
        )

    @property
    def mother(self) -> Person | None:
        return self.__mother

    @mother.setter
    def mother(self, value: Person):
        self.__mother = value

    @cached_property
    def wedding_day(self) -> date:
        if self.__children:
            return (
                min(self.__children, key=attrgetter("birth_day.date")).birth_day.date
                - timedelta(weeks=40)
                - timedelta(weeks=random.randint(a=0, b=500))
            )
        else:
            majority = 360 * 18
            parents = [self.__father, self.__mother]
            youngest = min((p.birth_day.date for p in parents if p is not None))
            return youngest + timedelta(days=majority)

    @property
    def children(self) -> set[Person]:
        return self.__children

    def is_full(self) -> bool:
        return self.father is not None and self.mother is not None


class RelationType(Enum):
    MARRIAGE = 1
    BIRTH_FROM = 2
    SIMPLE = 3


class Relation:
    def __init__(self, first_person_id, type_of_relation, other_person_id, family_id):
        self.first_person_id = GrampsId(first_person_id)
        self.type_of_relation = type_of_relation
        self.other_person_id = GrampsId(other_person_id)
        self.family_id = GrampsId(family_id)

    def __eq__(self, other):
        if (
            self.first_person_id == other.first_person_id
            and self.type_of_relation == other.type_of_relation
            and self.other_person_id == other.other_person_id
            and self.family_id == other.family_id
        ):
            return True
        return False

    def __hash__(self):
        return hash(self.family_id)


class EventType(Enum):
    BIRTH = 12
    DEATH = 13


@singleton
class Database:
    def __init__(self):
        conn = sqlite3.connect("sqlite.db")
        self.__cur = conn.cursor()

        self.__persons = self.__get_persons()  # type: dict[GrampsId, Person]

        self.__notes = self.__get_notes()  # type: dict[GrampsId, Note]

        self.__add_notes_to_person()

        self.__relations, self.__families = self.__get_relationship()
        pass

    @property
    def relations(self):
        return self.__relations

    @property
    def families(self) -> dict[GrampsId, Family]:
        return self.__families

    @property
    def persons(self) -> dict[GrampsId, Person]:
        return self.__persons

    def __get_persons(self) -> dict[GrampsId, Person]:
        persons = dict()
        self.__cur.execute("SELECT gramps_id, given_name, surname, gender FROM person")
        persons_raw = self.__cur.fetchall()
        for id, given_name, surname, gender in persons_raw:
            birth_day, death_day = self.__parse_lifetime(id)
            person = Person(
                id=id,
                full_name=f"{given_name} {surname}",
                birth_day=birth_day,
                death_day=death_day,
                gender=Gender(gender),
            )
            persons[id] = person
        return persons

    def __parse_lifetime(self, id: GrampsId) -> tuple[Date, Date | None]:
        self.__cur.execute(
            f"SELECT event.blob_data "
            f"FROM person "
            f"JOIN reference ON reference.obj_handle  = person.handle "
            f"JOIN event ON event.handle = reference.ref_handle "
            f'WHERE person.gramps_id = "{id}"'
        )
        events = self.__cur.fetchall()
        birth_day, death_day = None, None
        for (event,) in events:
            _, _, type, r_date, _, _, _, _, _, _, _, _, _ = pickle.loads(event)
            type = type[0]

            if type == EventType.BIRTH.value:
                if r_date is None:
                    logger.error(f"The person {id} without birthday")
                    raise ValueError
                birth_day = Date.from_gramps_db(r_date)

            if type == EventType.DEATH.value:
                if r_date is None:
                    death_day = None
                else:
                    death_day = Date.from_gramps_db(r_date)

        return birth_day, death_day

    def __get_notes(self) -> dict[GrampsId, Note]:
        notes = dict()
        self.__cur.execute("SELECT note.gramps_id, note.blob_data FROM note")
        notes_raw = self.__cur.fetchall()
        for id, blob_data in notes_raw:
            note = Note(blob_data)
            notes[id] = note
        return notes

    def __add_notes_to_person(self) -> None:
        self.__cur.execute(
            f"SELECT person.gramps_id AS person_id, note.gramps_id AS note_id "
            "FROM reference JOIN person ON person.handle = reference.obj_handle "
            "JOIN note ON note.handle = reference.ref_handle "
            'WHERE reference.ref_class = "Note"; '
        )
        for person_id, note_id in self.__cur.fetchall():
            self.__persons[person_id].add_note(self.__notes[note_id])

    def __get_relationship(self) -> tuple[set[Relation], dict[GrampsId, Family]]:
        self.__cur.execute(
            f"SELECT family_id,"
            f"       father_id,"
            f"       mother_id,"
            f"       person.gramps_id AS person_id FROM "
            f"( "
            f"	SELECT family_id,"
            f"         father_id,"
            f"         person.gramps_id as mother_id,"
            f"         person_handle FROM "
            f"	( "
            f"		SELECT family.gramps_id as family_id, "
            f"		       person.gramps_id as father_id, "
            f"			   family.mother_handle as mother_handle, "
            f"			   reference.ref_handle as person_handle "
            f"		FROM reference "
            f"		JOIN family ON family.handle = reference.obj_handle "
            f"		LEFT JOIN person ON person.handle = family.father_handle "
            f'		WHERE reference.ref_class = "Person" '
            f"	) "
            f"	LEFT JOIN person ON person.handle = mother_handle "
            f") "
            f"JOIN person ON person.handle = person_handle "
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
                relations.add(
                    Relation(father_id, RelationType.MARRIAGE, mother_id, family_id)
                )
            elif person_id == mother_id and father_id is not None:
                families[family_id].father = self.__persons[father_id]
                families[family_id].mother = self.__persons[mother_id]
                relations.add(
                    Relation(father_id, RelationType.MARRIAGE, mother_id, family_id)
                )
            elif person_id != father_id and person_id != mother_id:
                if father_id is not None:
                    families[family_id].father = self.__persons[father_id]
                    families[family_id].add_child(self.__persons[person_id])
                    relations.add(
                        Relation(
                            person_id, RelationType.BIRTH_FROM, father_id, family_id
                        )
                    )
                elif mother_id is not None:
                    families[family_id].mother = self.__persons[mother_id]
                    families[family_id].add_child(self.__persons[person_id])
                    relations.add(
                        Relation(
                            person_id, RelationType.BIRTH_FROM, mother_id, family_id
                        )
                    )

        return relations, families
