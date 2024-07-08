# Copyright (C) 2024 Helmar Hutschenreuter
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import csv
from typing import Generic, Sequence, TypeVar, cast


class ProtectionNeedCategory:
    def __init__(
        self,
        designation: str,
        subordinate: "ProtectionNeedCategory | None" = None,
    ):
        self.designation = designation
        self.level = 0 if subordinate is None else subordinate.level + 1


NORMAL = ProtectionNeedCategory("Normal")
HIGH = ProtectionNeedCategory("Hoch", NORMAL)
VERY_HIGH = ProtectionNeedCategory("Sehr hoch", HIGH)


class ProtectionNeed:
    def __init__(self, category: ProtectionNeedCategory, *remarks: str):
        self.category = category
        self.remarks = list(remarks)

    def to_dict(self):
        return {
            "Schutzbedarf": self.category.designation,
            "Anmerkungen": "; ".join(self.remarks),
        }

    def __add__(self, other: "ProtectionNeed") -> "ProtectionNeed":
        if self.category.level < other.category.level:
            return other
        elif self.category.level > other.category.level:
            return self
        else:
            return ProtectionNeed(self.category, *set(self.remarks + other.remarks))

    def __iadd__(self, other: "ProtectionNeed") -> "ProtectionNeed":
        return other.__add__(self)

    @classmethod
    def determine(
        cls, *protection_needs: "ProtectionNeed | None"
    ) -> "ProtectionNeed | None":
        protection_need: ProtectionNeed | None = None
        for pn in protection_needs:
            if pn is not None:
                if protection_need is None:
                    protection_need = pn
                else:
                    protection_need += pn
        return protection_need


class Structure:
    def __init__(
        self,
        name: str,
        description: str | None = None,
        parent: "Structure | None" = None,
        remark: str | None = None,
        hidden: bool = False,
        integrity: ProtectionNeed | None = None,
        availability: ProtectionNeed | None = None,
        confidentiality: ProtectionNeed | None = None,
    ):
        self._id: None | int = None
        self.name = name
        self.description = description
        self.remark = remark
        self._hidden = hidden
        self._integrity = integrity
        self._availability = availability
        self._confidentiality = confidentiality
        self._parent = parent
        self._children: set[Structure] = set()

        # Link the structure to its parent structure if it exists
        if parent is not None:
            parent._children.add(self)

    @property
    def id_and_name(self) -> str:
        return self.name if self._id is None else f"{self._id}: {self.name}"

    @property
    def level(self) -> int:
        return 0 if self._parent is None else self._parent.level + 1

    @property
    def children(self) -> "set[Structure]":
        children = set()
        for child in self._children:
            children.add(child)
            children |= child.children
        return children

    @property
    def hidden(self) -> bool:
        return (
            self._parent.hidden if self._parent is not None else False
        ) or self._hidden

    @property
    def integrity(self) -> ProtectionNeed | None:
        return ProtectionNeed.determine(
            (self._parent._integrity if self._parent is not None else None),
            self._integrity,
            *map(lambda s: s.integrity, self._children),
        )

    @property
    def availability(self) -> ProtectionNeed | None:
        return ProtectionNeed.determine(
            (self._parent._availability if self._parent is not None else None),
            self._availability,
            *map(lambda s: s.availability, self._children),
        )

    @property
    def confidentiality(self) -> ProtectionNeed | None:
        return ProtectionNeed.determine(
            (self._parent._confidentiality if self._parent is not None else None),
            self._confidentiality,
            *map(lambda s: s.confidentiality, self._children),
        )

    def to_dict(self):
        # fmt: off
        dict_integrity = self.integrity.to_dict() if self.integrity is not None else {}
        dict_availability = self.availability.to_dict() if self.availability is not None else {}
        dict_confidentiality = self.confidentiality.to_dict() if self.confidentiality is not None else {}

        return {
            "ID": self._id,
            "Ebene": self.level,
            "Name": self.name,
            "Beschreibung": self.description,
            "Anmerkung": self.remark,
            **{f"Integrität {k}": v for k, v in dict_integrity.items()},
            **{f"Verfügbarkeit {k}": v for k, v in dict_availability.items()},
            **{f"Vertraulichkeit {k}": v for k, v in dict_confidentiality.items()},
        }
        # fmt: on


A = TypeVar("A", bound=Structure)


class SecondaryStructure(Generic[A], Structure):
    def __init__(self, *args, dependent: set[A] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._dependent: set[A] = dependent or set()

    @property
    def dependent(self) -> set[A]:
        dependent: set[A] = set()

        # Collect all structures subordinate to the dependent structures
        for d in self._dependent:
            dependent.add(d)
            dependent |= cast(set[A], d.children)

        # Collect all structures dependent on the subordinate structures
        for sub in cast(set[SecondaryStructure[A]], self.children):
            dependent |= sub.dependent
        return dependent

    @property
    def integrity(self) -> ProtectionNeed | None:
        return ProtectionNeed.determine(
            (self._parent._integrity if self._parent is not None else None),
            self._integrity,
            *map(lambda d: d.integrity, self.dependent),
            *map(lambda sub: sub.integrity, self._children),
        )

    @property
    def availability(self) -> ProtectionNeed | None:
        return ProtectionNeed.determine(
            (self._parent._availability if self._parent is not None else None),
            self._availability,
            *map(lambda d: d.availability, self.dependent),
            *map(lambda sub: sub.availability, self._children),
        )

    @property
    def confidentiality(self) -> ProtectionNeed | None:
        return ProtectionNeed.determine(
            (self._parent._confidentiality if self._parent is not None else None),
            self._confidentiality,
            *map(lambda d: d.confidentiality, self.dependent),
            *map(lambda sub: sub.confidentiality, self._children),
        )


class Information(Structure):
    pass


class BusinessProcess(SecondaryStructure[Information]):

    def to_dict(self):
        return {
            **super().to_dict(),
            "Information": "; ".join(i.id_and_name for i in self.dependent),
        }


class Application(SecondaryStructure[BusinessProcess]):

    def to_dict(self):
        return {
            **super().to_dict(),
            "Geschäftsprozesse": "; ".join(p.id_and_name for p in self.dependent),
        }


class Infrastructure(SecondaryStructure[Application]):

    def to_dict(self):
        return {
            **super().to_dict(),
            "Anwendungen": "; ".join(a.id_and_name for a in self.dependent),
        }


class Room(SecondaryStructure[Infrastructure]):

    def to_dict(self):
        return {
            **super().to_dict(),
            "Infrastrukturen": "; ".join(i.id_and_name for i in self.dependent),
        }


class Building(SecondaryStructure[Room]):

    def to_dict(self):
        return {
            **super().to_dict(),
            "Räume": "; ".join(r.id_and_name for r in self.dependent),
        }


class Model:
    def __init__(
        self,
        informations: list[Information] | None = None,
        processes: list[BusinessProcess] | None = None,
        applications: list[Application] | None = None,
        infrastructures: list[Infrastructure] | None = None,
        rooms: list[Room] | None = None,
        buildings: list[Building] | None = None,
    ):
        self.informations = informations or []
        self.processes = processes or []
        self.applications = applications or []
        self.infrastructures = infrastructures or []
        self.rooms = rooms or []
        self.buildings = buildings or []

    @staticmethod
    def _set_structure_ids(structures: Sequence[Structure], skip_hidden: bool = False):
        for id, s in enumerate(structures, start=1):
            if s._id is None and not (s.hidden and skip_hidden):
                s._id = id

    def _set_all_structure_ids(self, skip_hidden: bool = False):
        self._set_structure_ids(self.informations, skip_hidden)
        self._set_structure_ids(self.processes, skip_hidden)
        self._set_structure_ids(self.applications, skip_hidden)
        self._set_structure_ids(self.infrastructures, skip_hidden)
        self._set_structure_ids(self.rooms, skip_hidden)
        self._set_structure_ids(self.buildings, skip_hidden)

    @staticmethod
    def _write_structure_dicts_to_csv(
        structures: Sequence[Structure], filename: str, skip_hidden: bool = False
    ):
        # Determine fieldnames and dicts to write to CSV
        fieldnames = []
        data_dicts = []
        for s in structures:
            if s.hidden and skip_hidden:
                continue
            data = s.to_dict()
            data_dicts.append(data)
            keys = data.keys()
            if len(keys) > len(fieldnames):
                fieldnames = keys

        # Write dicts to CSV
        with open(filename, "w", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            for data in data_dicts:
                writer.writerow(data)

    def write_csvs(self, dirname: str, skip_hidden: bool = False):
        # fmt: off
        self._set_all_structure_ids(skip_hidden)
        self._write_structure_dicts_to_csv(self.informations, f"{dirname}/1_informationen.csv", skip_hidden)
        self._write_structure_dicts_to_csv(self.processes, f"{dirname}/2_prozesse.csv", skip_hidden)
        self._write_structure_dicts_to_csv(self.applications, f"{dirname}/3_anwendungen.csv", skip_hidden)
        self._write_structure_dicts_to_csv(self.infrastructures, f"{dirname}/4_infrastrukturen.csv", skip_hidden)
        self._write_structure_dicts_to_csv(self.rooms, f"{dirname}/5_raeume.csv", skip_hidden)
        self._write_structure_dicts_to_csv(self.buildings, f"{dirname}/6_gebaeude.csv", skip_hidden)
        # fmt: on
