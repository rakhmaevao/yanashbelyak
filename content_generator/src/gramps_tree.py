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


@singleton
class GrampsTree:
    def __init__(self, gramps_tree_path: Path):
        self.__gramps_tree_path = gramps_tree_path
        logger.info(f"gramps_tree_path: {self.__gramps_tree_path}")
        conn = sqlite3.connect(self.__gramps_tree_path / Path("sqlite.db"))
        self.__cur = conn.cursor()

        self.__persons = self.__get_persons()  # type: dict[GrampsId, Person]
        self.__events = self.__get_events()  # type: dict[GrampsId, Event]
        self.__notes = self.__get_notes()  # type: dict[GrampsId, Note]
        self.__media = self.__get_media()  # type: dict[GrampsId, Media]
        self.__add_notes_to_person()
        self.__add_event_for_persone()
        self.__map_media_to_person()

        self.__relations, self.__families = self.__get_relationship()

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

    def __get_persons(self) -> dict[GrampsId, Person]:
        persons = {}
        self.__cur.execute("SELECT gramps_id, given_name, surname, gender FROM person")
        persons_raw = self.__cur.fetchall()
        for _id, given_name, surname, gender in persons_raw:
            birth_day, death_day = self.__parse_lifetime(_id)
            person = Person(
                _id=_id,
                full_name=f"{given_name} {surname}",
                birth_day=birth_day,
                death_day=death_day,
                gender=Gender(gender),
            )
            persons[_id] = person
        return persons

    def __parse_lifetime(self, _id: GrampsId) -> tuple[Date, Date | None]:
        self.__cur.execute(
            f"SELECT event.json_data "  # noqa: S608
            f"FROM person "
            f"JOIN reference ON reference.obj_handle  = person.handle "
            f"JOIN event ON event.handle = reference.ref_handle "
            f'WHERE person.gramps_id = "{_id}"',
        )
        events = self.__cur.fetchall()
        birth_day, death_day = None, None
        for (raw_event,) in events:
            event = json.loads(raw_event)
            event_type_id = event["type"]["value"]
            raw_date = event["date"]

            if event_type_id == EventType.BIRTH.value:
                # if raw_date is None:
                #     raise PersonWithoutBirthdayError(_id)
                birth_day = Date.from_gramps_json_date(raw_date)

            if event_type_id == EventType.DEATH.value:
                death_day = Date.from_gramps_json_date(raw_date)

        return birth_day, death_day

    def __get_notes(self) -> dict[GrampsId, Note]:
        notes = {}
        self.__cur.execute("SELECT note.gramps_id, note.json_data FROM note")
        notes_raw = self.__cur.fetchall()
        for _id, raw_data in notes_raw:
            dict_data = json.loads(raw_data)
            note = Note(
                gramps_id=GrampsId(dict_data["gramps_id"]),
                content=dict_data["text"]["string"],
            )
            notes[_id] = note
        return notes

    def __get_events(self) -> dict[GrampsId, Event]:
        events = {}
        self.__cur.execute("SELECT event.gramps_id, event.json_data FROM event")
        event_raw = self.__cur.fetchall()
        for _id, raw_data in event_raw:
            dict_data = json.loads(raw_data)
            try:
                event = Event(
                    date=Date.from_gramps_json_date(dict_data["date"]),
                    description=dict_data["description"],
                    gramps_id=dict_data["gramps_id"],
                )
            except ValueError as error:
                logger.error(
                    f"Error for event for {dict_data}"
                )  # TODO: rao: Вроде тут баг
            events[GrampsId(_id)] = event
        return events

    def __add_notes_to_person(self) -> None:
        self.__cur.execute(
            "SELECT person.gramps_id AS person_id, note.gramps_id AS note_id "
            "FROM reference JOIN person ON person.handle = reference.obj_handle "
            "JOIN note ON note.handle = reference.ref_handle "
            'WHERE reference.ref_class = "Note"; ',
        )
        for person_id, note_id in self.__cur.fetchall():
            self.__persons[person_id].add_note(self.__notes[note_id])

    def __add_event_for_persone(self) -> None:
        self.__cur.execute(
            "SELECT person.gramps_id AS person_id, event.gramps_id AS event_id "
            "FROM reference JOIN person ON person.handle = reference.obj_handle "
            "JOIN event ON event.handle = reference.ref_handle "
            'WHERE reference.ref_class = "Event"; ',
        )
        for person_id, event_id in self.__cur.fetchall():
            self.__persons[person_id].add_event(self.__events[event_id])

    def __get_relationship(self) -> tuple[set[Relation], dict[GrampsId, Family]]:
        self.__cur.execute(
            "SELECT family_id,"
            "       father_id,"
            "       mother_id,"
            "       person.gramps_id AS person_id FROM "
            "( "
            "	SELECT family_id,"
            "         father_id,"
            "         person.gramps_id as mother_id,"
            "         person_handle FROM "
            "	( "
            "		SELECT family.gramps_id as family_id, "
            "		       person.gramps_id as father_id, "
            "			   family.mother_handle as mother_handle, "
            "			   reference.ref_handle as person_handle "
            "		FROM reference "
            "		JOIN family ON family.handle = reference.obj_handle "
            "		LEFT JOIN person ON person.handle = family.father_handle "
            '		WHERE reference.ref_class = "Person" '
            "	) "
            "	LEFT JOIN person ON person.handle = mother_handle "
            ") "
            "JOIN person ON person.handle = person_handle ",
        )
        relations = set()
        families = {}
        relation_raw = self.__cur.fetchall()
        for _family_id, father_id, mother_id, person_id in relation_raw:
            family_id = GrampsId(_family_id)
            if family_id not in families:
                families[family_id] = Family(family_id)
            if (person_id == father_id and mother_id is not None) or (
                person_id == mother_id and father_id is not None
            ):
                families[family_id].father = self.__persons[father_id]
                families[family_id].mother = self.__persons[mother_id]
                relations.add(
                    Relation(father_id, RelationType.MARRIAGE, mother_id, family_id),
                )
            elif person_id not in {father_id, mother_id}:
                if father_id is not None:
                    families[family_id].father = self.__persons[father_id]
                    families[family_id].add_child(self.__persons[person_id])
                    relations.add(
                        Relation(
                            person_id,
                            RelationType.BIRTH_FROM,
                            father_id,
                            family_id,
                        ),
                    )
                elif mother_id is not None:
                    families[family_id].mother = self.__persons[mother_id]
                    families[family_id].add_child(self.__persons[person_id])
                    relations.add(
                        Relation(
                            person_id,
                            RelationType.BIRTH_FROM,
                            mother_id,
                            family_id,
                        ),
                    )

        return relations, families

    def __get_media(self) -> dict[GrampsId, Media]:
        media = {}
        self.__cur.execute(
            "SELECT media.gramps_id, media.mime, media.path, media.desc FROM media"
        )
        raw = self.__cur.fetchall()
        for gramps_id, mime, media_path, description in raw:
            logger.info(f"FFFF {gramps_id, description, media_path}")
            if mime not in ("image/jpeg", "image/png"):
                continue
            media_obj = Media(
                description=description,
                path=self.__gramps_tree_path / Path("media") / media_path,
            )
            media[gramps_id] = media_obj
        return media

    def __map_media_to_person(self):
        self.__cur.execute(
            "SELECT person.gramps_id AS person_id, media.gramps_id AS media_id "
            "FROM reference JOIN person ON person.handle = reference.obj_handle "
            "JOIN media ON media.handle = reference.ref_handle "
            'WHERE reference.ref_class = "Media"; ',
        )
        for person_id, media_id in self.__cur.fetchall():
            media = self.__media[media_id]
            person = self.__persons[person_id]
            media.mark_person(person)
            person.add_media(media)
