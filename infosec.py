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
            return Schutzbedarf(self.kategorie, *(self.anmerkungen + other.anmerkungen))

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
        Schutzbedarf.bestimme(
            self._integritaet,
            *map(lambda a: a.integritaet, self._untergeordnet),
        )

    @property
    def verfuegbarkeit(self) -> Schutzbedarf | None:
        Schutzbedarf.bestimme(
            self._verfuegbarkeit,
            *map(lambda a: a.verfuegbarkeit, self._untergeordnet),
        )

    @property
    def vertraulichkeit(self) -> Schutzbedarf | None:
        Schutzbedarf.bestimme(
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


class Anwendung(Struktur):
    def __init__(self, *args, prozesse: set[Geschaeftsprozess] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._prozesse: set[Geschaeftsprozess] = prozesse or set()

    @property
    def prozesse(self) -> set[Geschaeftsprozess]:
        prozesse = set()
        for p in self._prozesse:
            prozesse.add(p)
            prozesse |= p.untergeordnet
        return prozesse

    def to_dict(self):
        return {
            **super().to_dict(),
            "Geschäftsprozesse": "; ".join(p.bezeichnung_und_id for p in self.prozesse),
        }


class Infrastruktur(Struktur):
    def __init__(self, *args, anwendungen: set[Anwendung] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._anwendungen: set[Anwendung] = anwendungen or set()

    @property
    def anwendungen(self) -> set[Anwendung]:
        anwendungen = set()
        for a in self._anwendungen:
            anwendungen.add(a)
            anwendungen |= a.untergeordnet
        return anwendungen

    def to_dict(self):
        return {
            **super().to_dict(),
            "Anwendungen": "; ".join(a.bezeichnung_und_id for a in self.anwendungen),
        }


class Raum(Struktur):
    def __init__(
        self,
        *args,
        infrastrukturen: set[Infrastruktur] | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._infrastrukturen: set[Infrastruktur] = infrastrukturen or set()

    @property
    def infrastrukturen(self) -> set[Infrastruktur]:
        infrastrukturen = set()
        for i in self._infrastrukturen:
            infrastrukturen.add(i)
            infrastrukturen |= i.untergeordnet
        return infrastrukturen

    def to_dict(self):
        return {
            **super().to_dict(),
            "Infrastrukturen": "; ".join(
                i.bezeichnung_und_id for i in self.infrastrukturen
            ),
        }


class Gebaeude(Struktur):
    def __init__(self, *args, raeume: set[Raum] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._raeume: set[Raum] = raeume or set()

    @property
    def raeume(self) -> set[Raum]:
        raeume = set()
        for r in self._raeume:
            raeume.add(r)
            raeume |= r.untergeordnet
        return raeume

    def to_dict(self):
        return {
            **super().to_dict(),
            "Raeume": "; ".join(r.bezeichnung_und_id for r in self.raeume),
        }
