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


class Schutzbedarfskategorie:
    def __init__(
        self,
        bezeichnung: str,
        untergeordnet: "Schutzbedarfskategorie | None" = None,
    ):
        self.bezeichnung = bezeichnung
        self.ordnung = 0 if untergeordnet is None else untergeordnet.ordnung + 1


NORMAL = Schutzbedarfskategorie("Normal")
HOCH = Schutzbedarfskategorie("Hoch", NORMAL)
SEHR_HOCH = Schutzbedarfskategorie("Sehr hoch", HOCH)


class Schutzbedarf:
    def __init__(self, kategorie: Schutzbedarfskategorie, *anmerkungen: str):
        self.kategorie = kategorie
        self.anmerkungen = list(anmerkungen)

    def to_dict(self):
        return {
            "Schutzbedarf": self.kategorie.bezeichnung,
            "Anmerkungen": "; ".join(self.anmerkungen),
        }

    def __add__(self, other: "Schutzbedarf") -> "Schutzbedarf":
        if self.kategorie.ordnung < other.kategorie.ordnung:
            return other
        elif self.kategorie.ordnung > other.kategorie.ordnung:
            return self
        else:
            return Schutzbedarf(
                self.kategorie, *set(self.anmerkungen + other.anmerkungen)
            )

    def __iadd__(self, other: "Schutzbedarf") -> "Schutzbedarf":
        return other.__add__(self)

    @classmethod
    def bestimme(cls, *schutzbedarfe: "Schutzbedarf | None") -> "Schutzbedarf | None":
        schutzbedarf: Schutzbedarf | None = None
        for s in schutzbedarfe:
            if s is not None:
                if schutzbedarf is None:
                    schutzbedarf = s
                else:
                    schutzbedarf += s
        return schutzbedarf


class Struktur:
    def __init__(
        self,
        bezeichnung: str,
        beschreibung: str | None = None,
        uebergeordnet: "Struktur | None" = None,
        anmerkung: str | None = None,
        versteckt: bool = False,
        integritaet: Schutzbedarf | None = None,
        verfuegbarkeit: Schutzbedarf | None = None,
        vertraulichkeit: Schutzbedarf | None = None,
    ):
        self._id: None | int = None
        self.bezeichnung = bezeichnung
        self.beschreibung = beschreibung
        self.anmerkung = anmerkung
        self._versteckt = versteckt
        self._integritaet = integritaet
        self._verfuegbarkeit = verfuegbarkeit
        self._vertraulichkeit = vertraulichkeit
        self._uebergeordnet = uebergeordnet
        self._untergeordnet: set[Struktur] = set()

        # Link the structure to its parent structure if it exists
        if uebergeordnet is not None:
            uebergeordnet._untergeordnet.add(self)

    @property
    def bezeichnung_und_id(self) -> str:
        return (
            self.bezeichnung if self._id is None else f"{self._id}: {self.bezeichnung}"
        )

    @property
    def ebene(self) -> int:
        return 0 if self._uebergeordnet is None else self._uebergeordnet.ebene + 1

    @property
    def untergeordnet(self) -> "set[Struktur]":
        untergeordnet = set()
        for u in self._untergeordnet:
            untergeordnet.add(u)
            untergeordnet |= u.untergeordnet
        return untergeordnet

    @property
    def versteckt(self) -> bool:
        return (
            self._uebergeordnet.versteckt if self._uebergeordnet is not None else False
        ) or self._versteckt

    @property
    def integritaet(self) -> Schutzbedarf | None:
        return Schutzbedarf.bestimme(
            (
                self._uebergeordnet._integritaet
                if self._uebergeordnet is not None
                else None
            ),
            self._integritaet,
            *map(lambda a: a.integritaet, self._untergeordnet),
        )

    @property
    def verfuegbarkeit(self) -> Schutzbedarf | None:
        return Schutzbedarf.bestimme(
            (
                self._uebergeordnet._verfuegbarkeit
                if self._uebergeordnet is not None
                else None
            ),
            self._verfuegbarkeit,
            *map(lambda a: a.verfuegbarkeit, self._untergeordnet),
        )

    @property
    def vertraulichkeit(self) -> Schutzbedarf | None:
        return Schutzbedarf.bestimme(
            (
                self._uebergeordnet._vertraulichkeit
                if self._uebergeordnet is not None
                else None
            ),
            self._vertraulichkeit,
            *map(lambda a: a.vertraulichkeit, self._untergeordnet),
        )

    def to_dict(self):
        # fmt: off
        dict_integritaet = self.integritaet.to_dict() if self.integritaet is not None else {}
        dict_verfuegbarkeit = self.verfuegbarkeit.to_dict() if self.verfuegbarkeit is not None else {}
        dict_vertraulichkeit = self.vertraulichkeit.to_dict() if self.vertraulichkeit is not None else {}

        return {
            "ID": self._id,
            "Ebene": self.ebene,
            "Bezeichnung": self.bezeichnung,
            "Beschreibung": self.beschreibung,
            "Anmerkung": self.anmerkung,
            **{f"Integritaet {k}": v for k, v in dict_integritaet.items()},
            **{f"Verfuegbarkeit {k}": v for k, v in dict_verfuegbarkeit.items()},
            **{f"Vertraulichkeit {k}": v for k, v in dict_vertraulichkeit.items()},
        }
        # fmt: on


A = TypeVar("A", bound=Struktur)


class Sekundaerstruktur(Generic[A], Struktur):
    def __init__(self, *args, abhaengige: set[A] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._abhaengige: set[A] = abhaengige or set()

    @property
    def abhaengige(self) -> set[A]:
        abhaengige: set[A] = set()

        # Collect all structures subordinate to the dependent structures
        for a in self._abhaengige:
            abhaengige.add(a)
            abhaengige |= cast(set[A], a.untergeordnet)

        # Collect all structures dependent on the subordinate structures
        for u in cast(set[Sekundaerstruktur[A]], self.untergeordnet):
            abhaengige |= u.abhaengige
        return abhaengige

    @property
    def integritaet(self) -> Schutzbedarf | None:
        return Schutzbedarf.bestimme(
            (
                self._uebergeordnet._integritaet
                if self._uebergeordnet is not None
                else None
            ),
            self._integritaet,
            *map(lambda a: a.integritaet, self.abhaengige),
            *map(lambda u: u.integritaet, self._untergeordnet),
        )

    @property
    def verfuegbarkeit(self) -> Schutzbedarf | None:
        return Schutzbedarf.bestimme(
            (
                self._uebergeordnet._verfuegbarkeit
                if self._uebergeordnet is not None
                else None
            ),
            self._verfuegbarkeit,
            *map(lambda a: a.verfuegbarkeit, self.abhaengige),
            *map(lambda u: u.verfuegbarkeit, self._untergeordnet),
        )

    @property
    def vertraulichkeit(self) -> Schutzbedarf | None:
        return Schutzbedarf.bestimme(
            (
                self._uebergeordnet._vertraulichkeit
                if self._uebergeordnet is not None
                else None
            ),
            self._vertraulichkeit,
            *map(lambda a: a.vertraulichkeit, self.abhaengige),
            *map(lambda u: u.vertraulichkeit, self._untergeordnet),
        )


class Information(Struktur):
    pass


class Geschaeftsprozess(Sekundaerstruktur[Information]):

    def to_dict(self):
        return {
            **super().to_dict(),
            "Informationen": "; ".join(i.bezeichnung_und_id for i in self.abhaengige),
        }


class Anwendung(Sekundaerstruktur[Geschaeftsprozess]):

    def to_dict(self):
        return {
            **super().to_dict(),
            "Geschäftsprozesse": "; ".join(
                p.bezeichnung_und_id for p in self.abhaengige
            ),
        }


class Infrastruktur(Sekundaerstruktur[Anwendung]):

    def to_dict(self):
        return {
            **super().to_dict(),
            "Anwendungen": "; ".join(a.bezeichnung_und_id for a in self.abhaengige),
        }


class Raum(Sekundaerstruktur[Infrastruktur]):

    def to_dict(self):
        return {
            **super().to_dict(),
            "Infrastrukturen": "; ".join(i.bezeichnung_und_id for i in self.abhaengige),
        }


class Gebaeude(Sekundaerstruktur[Raum]):

    def to_dict(self):
        return {
            **super().to_dict(),
            "Raeume": "; ".join(r.bezeichnung_und_id for r in self.abhaengige),
        }


class Modell:
    def __init__(
        self,
        informationen: list[Information] | None = None,
        prozesse: list[Geschaeftsprozess] | None = None,
        anwendungen: list[Anwendung] | None = None,
        infrastrukturen: list[Infrastruktur] | None = None,
        raeume: list[Raum] | None = None,
        gebaeude: list[Gebaeude] | None = None,
    ):
        self.informationen = informationen or []
        self.prozesse = prozesse or []
        self.anwendungen = anwendungen or []
        self.infrastrukturen = infrastrukturen or []
        self.raeume = raeume or []
        self.gebaeude = gebaeude or []

    @staticmethod
    def _set_struktur_ids(strukturen: Sequence[Struktur], skip_versteckt: bool = False):
        for id, s in enumerate(strukturen, start=1):
            if s._id is None and not (s.versteckt and skip_versteckt):
                s._id = id

    def _set_all_struktur_ids(self, skip_versteckt: bool = False):
        self._set_struktur_ids(self.informationen, skip_versteckt)
        self._set_struktur_ids(self.prozesse, skip_versteckt)
        self._set_struktur_ids(self.anwendungen, skip_versteckt)
        self._set_struktur_ids(self.infrastrukturen, skip_versteckt)
        self._set_struktur_ids(self.raeume, skip_versteckt)
        self._set_struktur_ids(self.gebaeude, skip_versteckt)

    @staticmethod
    def _write_struktur_dicts_to_csv(
        strukturen: Sequence[Struktur], filename: str, skip_versteckt: bool = False
    ):
        is_first_struktur = True
        with open(filename, "w", newline="") as file:
            for s in strukturen:
                if s.versteckt and skip_versteckt:
                    continue
                if is_first_struktur:
                    writer = csv.DictWriter(file, fieldnames=s.to_dict().keys())
                    writer.writeheader()
                    is_first_struktur = False
                writer.writerow(s.to_dict())

    def write_csvs(self, dirname: str, skip_versteckt: bool = False):
        # fmt: off
        self._set_all_struktur_ids(skip_versteckt)
        self._write_struktur_dicts_to_csv(self.informationen, f"{dirname}/1_informationen.csv", skip_versteckt)
        self._write_struktur_dicts_to_csv(self.prozesse, f"{dirname}/2_prozesse.csv", skip_versteckt)
        self._write_struktur_dicts_to_csv(self.anwendungen, f"{dirname}/3_anwendungen.csv", skip_versteckt)
        self._write_struktur_dicts_to_csv(self.infrastrukturen, f"{dirname}/4_infrastrukturen.csv", skip_versteckt)
        self._write_struktur_dicts_to_csv(self.raeume, f"{dirname}/5_raeume.csv", skip_versteckt)
        self._write_struktur_dicts_to_csv(self.gebaeude, f"{dirname}/6_gebaeude.csv", skip_versteckt)
        # fmt: on
