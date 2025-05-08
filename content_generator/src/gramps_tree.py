from __future__ import annotations

import json
import locale
import pickle
import sqlite3
from pathlib import Path

from loguru import logger
from singleton_decorator import singleton

from .entities import (
    Date,
    Event,
    EventType,
    Family,
    Gender,
    GrampsId,
    Media,
    Note,
    Person,
    PersonWithoutBirthdayError,
    Relation,
    RelationType,
)

locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")


class GrampsTree:
    def __init__(
        self,
        persons: dict[GrampsId, Person],
        events: dict[GrampsId, Event],
        notes: dict[GrampsId, Note],
        media: dict[GrampsId, Media],
        relations: set[Relation],
        families: dict[GrampsId, Family],
    ):
        self.__persons = persons
        self.__events = events
        self.__notes = notes
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
