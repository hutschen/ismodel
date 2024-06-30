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
