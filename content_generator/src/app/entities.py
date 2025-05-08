from __future__ import annotations

import datetime
import random
from datetime import date, timedelta
from enum import Enum
from functools import cached_property
from operator import attrgetter
from pathlib import Path

from loguru import logger


class GrampsTree:
    def __init__(
        self,
        persons: dict[GrampsId, Person],
        media: dict[GrampsId, Media],
        relations: set[Relation],
        families: dict[GrampsId, Family],
    ):
        self.__persons = persons
        self.__media = media
        self.__relations = relations
        self.__families = families

    @property
    def relations(self):
        return self.__relations

    @property
    def families(self) -> dict[GrampsId, Family]:
        return self.__families

    @property
    def persons(self) -> dict[GrampsId, Person]:
        return self.__persons

    @property
    def media(self) -> dict[GrampsId, Media]:
        return self.__media


class DateQuality(Enum):
    EXACTLY = 0
    ESTIMATED = 1

    def __str__(self) -> str:
        if self == DateQuality.EXACTLY:
            return ""
        if self == DateQuality.ESTIMATED:
            return "≈ "
        return "???"


class Date:
    def __init__(self, date: date, quality: DateQuality):
        self.__date = date
        self.__quality = quality

    @staticmethod
    def from_gramps_json_date(raw_date: dict) -> Date:
        logger.debug(f"Parsing date: {raw_date}")
        year = raw_date["dateval"][2]
        month = raw_date["dateval"][1]
        day = raw_date["dateval"][0]
        if day == 0:
            day = 1
        if month == 0:
            month = 1
        try:
            return Date(
                date(year, month, day), quality=DateQuality(raw_date["quality"])
            )
        except ValueError as message:
            logger.error(f"{message} for raw_date {raw_date}")
            raise ValueError(message) from message

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
    __slots__ = ()


class Event:
    def __init__(self, gramps_id: GrampsId, date: Date, description: str):
        self.__description = description
        self.__date = date
        self.__id = GrampsId(gramps_id)

    @property
    def gramps_id(self) -> GrampsId:
        return self.__id

    @property
    def description(self) -> str:
        return self.__description

    @property
    def date(self) -> Date:
        return self.__date


class Note:
    def __init__(self, gramps_id: GrampsId, content: str):
        self.__id = gramps_id
        self.__content = content

    @property
    def gramps_id(self) -> GrampsId:
        return self.__id

    @property
    def content(self) -> str:
        return self.__content


class Gender(Enum):
    FEMALE = 0
    MALE = 1
    UNKNOWN = 2


class PersonWithoutBirthdayError(Exception):
    def __init__(self, person_id: str) -> None:
        super().__init__(f"The person {person_id} without birthday")


class Person:
    __MAX_LIFETIME_Y = 100

    def __init__(
        self,
        _id: GrampsId,
        full_name: str,
        birth_day: Date,
        death_day: Date,
        gender: Gender,
    ):
        self.__media: set[Media] = set()
        self.__gramps_id = GrampsId(_id)
        self.__full_name: str = full_name
        self.__birth_day: Date = birth_day
        if birth_day is None:
            raise PersonWithoutBirthdayError(_id)
        if death_day is None:
            death_day = self.__birth_day.date + timedelta(
                days=365 * self.__MAX_LIFETIME_Y,
            )
            self.__death_day = Date(death_day, DateQuality.ESTIMATED)
        else:
            self.__death_day = death_day
        self.__gender: Gender = gender
        self.__notes: set[Note] = set()
        self.__events: set[Event] = set()

    def add_note(self, note: Note):
        self.__notes.add(note)

    def add_event(self, event: Event):
        self.__events.add(event)

    @property
    def gramps_id(self) -> GrampsId:
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
    def gender(self) -> Gender:
        return self.__gender

    @property
    def notes(self) -> set[Note]:
        return self.__notes

    @property
    def media(self) -> set[Media]:
        return self.__media

    @property
    def events(self) -> set[Event]:
        return self.__events

    def __str__(self):
        if self.death_day.date > datetime.datetime.now(tz=datetime.UTC).date():
            right_year = "н. в."
        else:
            right_year = self.death_day.date.year

        return f"{self.__full_name} ({self.__birth_day.date.year}-{right_year})"

    def is_male(self):
        return self.gender == Gender.MALE

    def is_female(self):
        return self.gender == Gender.FEMALE

    def __eq__(self, other: Person) -> bool:
        if other is None:
            return False
        return self.gramps_id == other.gramps_id

    def __hash__(self):
        return hash(self.gramps_id)

    def add_media(self, media: Media):
        self.__media.add(media)


class Family:
    def __init__(self, _id: GrampsId):
        self.__id = _id  # type: GrampsId
        self.__father = None  # type: Person | None
        self.__mother = None  # type: Person | None
        self.__children = set()  # type: set[Person]

    def add_child(self, child: Person):
        self.__children.add(child)

    @property
    def gramps_id(self) -> GrampsId:
        return self.__id

    @property
    def father(self) -> Person | None:
        return self.__father

    @father.setter
    def father(self, value: Person):
        self.__father = value

    @property
    def parents(self) -> set[Person]:
        return {
            person for person in [self.__father, self.__mother] if person is not None
        }

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
                - timedelta(weeks=random.randint(a=0, b=500))  # noqa: S311
            )

        majority = 360 * 18
        parents = [self.__father, self.__mother]
        youngest = min(p.birth_day.date for p in parents if p is not None)
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
    UNKNOWN = -1
    CUSTOM = 0
    MARRIAGE = 1
    MARR_SETTL = 2
    MARR_LIC = 3
    MARR_CONTR = 4
    MARR_BANNS = 5
    ENGAGEMENT = 6
    DIVORCE = 7
    DIV_FILING = 8
    ANNULMENT = 9
    MARR_ALT = 10
    ADOPT = 11
    BIRTH = 12
    DEATH = 13
    ADULT_CHRISTEN = 14
    BAPTISM = 15
    BAR_MITZVAH = 16
    BAS_MITZVAH = 17
    BLESS = 18
    BURIAL = 19
    CAUSE_DEATH = 20
    CENSUS = 21
    CHRISTEN = 22
    CONFIRMATION = 23
    CREMATION = 24
    DEGREE = 25
    EDUCATION = 26
    ELECTED = 27
    EMIGRATION = 28
    FIRST_COMMUN = 29
    IMMIGRATION = 30
    GRADUATION = 31
    MED_INFO = 32
    MILITARY_SERV = 33
    NATURALIZATION = 34
    NOB_TITLE = 35
    NUM_MARRIAGES = 36
    OCCUPATION = 37
    ORDINATION = 38
    PROBATE = 39
    PROPERTY = 40
    RELIGION = 41
    RESIDENCE = 42
    RETIREMENT = 43
    WILL = 44
    STILLBIRTH = 45


class Media:
    def __init__(self, path: Path, description: str):
        self.__persons: list[Person] = []
        self.__description = description
        self.__path = path

    @property
    def path(self) -> Path:
        return Path(self.__path)

    @path.setter
    def path(self, value: Path):
        self.__path = value

    @property
    def description(self):
        return self.__description

    def mark_person(self, person: Person):
        self.__persons.append(person)

    @property
    def persons(self) -> list[Person]:
        return self.__persons
