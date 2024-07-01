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
    def __init__(self, kategorie: Schutzbedarfskategorie, anmerkung: str | None = None):
        self.kategorie = kategorie
        self.anmerkungen = [] if anmerkung is None else [anmerkung]

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
            return Schutzbedarf(self.kategorie, self.anmerkungen + other.anmerkungen)

    def __iadd__(self, other: "Schutzbedarf") -> "Schutzbedarf":
        return other.__add__(self)

    @classmethod
    def bestimme(cls, *schutzbedarfe: "Schutzbedarf | None") -> "Schutzbedarf":
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
        uebergeordnet: "Struktur" | None = None,
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
        self._untergeordnet: set[Struktur] = {}

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
        return self._uebergeordnet.versteckt or self._versteckt

    @property
    def integritaet(self) -> Schutzbedarf:
        Schutzbedarf.bestimme(
            self._integritaet,
            *map(lambda a: a.integritaet, self._untergeordnet),
        )

    @property
    def verfuegbarkeit(self) -> Schutzbedarf:
        Schutzbedarf.bestimme(
            self._verfuegbarkeit,
            *map(lambda a: a.verfuegbarkeit, self._untergeordnet),
        )

    @property
    def vertraulichkeit(self) -> Schutzbedarf:
        Schutzbedarf.bestimme(
            self._vertraulichkeit,
            *map(lambda a: a.vertraulichkeit, self._untergeordnet),
        )

    def to_dict(self):
        # fmt: off
        return {
            "ID": self._id,
            "Ebene": self.ebene,
            "Bezeichnung": self.bezeichnung,
            "Beschreibung": self.beschreibung,
            "Anmerkung": self.anmerkung,
            **{f"Integritaet {k}": v for k, v in self.integritaet.to_dict().items()},
            **{f"Verfuegbarkeit {k}": v for k, v in self.verfuegbarkeit.to_dict().items()},
            **{f"Vertraulichkeit {k}": v for k, v in self.vertraulichkeit.to_dict().items()},
        }
        # fmt: on


class Information(Struktur):
    pass


class Geschaeftsprozess(Struktur):
    def __init__(self, *args, informationen: set[Information] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._informationen: set[Information] = informationen or set()

    @property
    def informationen(self) -> set[Information]:
        informationen = set()
        for i in self._informationen:
            informationen.add(i)
            informationen |= i.untergeordnet
        return informationen

    def to_dict(self):
        return {
            **super().to_dict(),
            "Informationen": "; ".join(
                i.bezeichnung_und_id for i in self.informationen
            ),
        }
