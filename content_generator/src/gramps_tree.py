from __future__ import annotations

import locale


from .entities import (
    Family,
    GrampsId,
    Media,
    Person,
    Relation,
)

locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")


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
