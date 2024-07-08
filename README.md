# Strukturanalyse und Schutzbedarfsableitung mit `ismodel`

Das Python-Modul `ismodel` (für "Informationssicherheit + Modell") soll dabei unterstützen, eine Strukturanalyse und Schutzbedarfsableitung (z.B. nach BSI-Standard 200-2) durchzuführen. Ziel ist es, ein Modell zu erstellen, das die verschiedenen Strukturen innerhalb einer Struktur und deren Beziehungen untereinander abbildet. Im zweiten Schritt können den Strukturen Schutzbedarfe zugeordnet werden, die innerhalb des Modells nach dem Maximumprinzip abgeleitet werden können. Die Ergebnisse können in CSV-Dateien geschrieben und anschließend weiterverarbeitet werden.

### Vorbereitung

Um `ismodel` zu verwenden, laden Sie den Inhalt dieses Repositorys als ZIP-Datei herunter oder klonen Sie das Repository mit Git, indem Sie den folgenden Befehl in Ihre Kommandozeile eingeben:

```bash
git clone https://github.com/hutschen/ismodel.git
```

Öffnen Sie dann das Wurzelverzeichnis des Projekts/Repositories und erstellen Sie eine neue Python-Datei (z.B. `modell.py`), in der Sie Ihr Modell erstellen können, wie in den folgenden Abschnitten beschrieben ist. Fügen Sie zuerst am Anfang der Datei den folgenden Import hinzu:

```python
from ismodel import *
```

### Erstellung der Informationen

Beginnen Sie mit der Erstellung der Informationen, indem Sie Instanzen der Klasse `Information` erzeugen. Jede Information muss einen eindeutigen Namen besitzen und kann optional Schutzbedarfe für Integrität, Verfügbarkeit und Vertraulichkeit enthalten.

```python
i1 = Information(
    "Personaldaten",
    integrity=ProtectionNeed(HIGH, "Kritische Daten zur Mitarbeiterverwaltung"),
    availability=ProtectionNeed(HIGH, "Erforderlich für tägliche Geschäftsabläufe"),
    confidentiality=ProtectionNeed(VERY_HIGH, "Enthält persönliche und sensible Daten"),
)
i2 = Information(
    "Kundendaten",
    integrity=ProtectionNeed(NORMAL, "Regelmäßige Backups vorhanden"),
    availability=ProtectionNeed(HIGH, "Zugriff durch Kundenbetreuung erforderlich"),
    confidentiality=ProtectionNeed(HIGH, "Enthält personenbezogene Daten der Kunden"),
)
i3 = Information(
    "Finanzdaten",
    parent=i2,
    integrity=ProtectionNeed(VERY_HIGH, "Wichtige finanzielle Transaktionen"),
    availability=ProtectionNeed(HIGH, "Benötigt für das tägliche Geschäft"),
    confidentiality=ProtectionNeed(VERY_HIGH, "Enthält vertrauliche finanzielle Informationen"),
)
```

### Erstellung der Geschäftsprozesse

Erstellen Sie Geschäftsprozesse und verknüpfen Sie diese mit Informationen, die für die Ausführung der jeweiligen Prozesse relevant sind. Die Verknüpfung erfolgt über den Parameter `dependent`, der eine Menge von Informationen enthält:

```python
p1 = BusinessProcess("Mitarbeiterverwaltung", dependent={i1})
p2 = BusinessProcess("Kundenbetreuung", dependent={i2})
p3 = BusinessProcess("Finanzmanagement", dependent={i3})
```

### Erstellung der Anwendungen

Fügen Sie die Anwendungen hinzu, die für die Ausführung der Geschäftsprozesse erforderlich sind. Verknüpfen Sie die Anwendungen mit den Geschäftsprozessen:

```python
a1 = Application("HR-Software", dependent={p1})
a2 = Application("CRM-System", dependent={p2})
a3 = Application("Buchhaltungssoftware", dependent={p3})
```

### Erstellung der Infrastrukturen

Erstellen Sie die (IT-)Infrastrukturen, die benötigt werden, um die Anwendungen auszuführen und verknüpfen Sie diese mit den Anwendungen:

```python
it1 = Infrastructure("Server-Cluster 1", dependent={a1, a2})
it2 = Infrastructure("Server-Cluster 2", dependent={a3})
```

### Erstellung der Räume

Infrastrukturen sind üblicherweise in Räumen untergebracht. Erstellen Sie Räume und verknüpfen Sie diese mit den Infrastrukturen:

```python
r1 = Room("Rechenzentrum 1", dependent={it1})
r2 = Room("Rechenzentrum 2", dependent={it2})
```

### Erstellung der Gebäude

Schließlich können Sie Gebäude erstellen und Räume darin platzieren:

```python
g1 = Building("Hauptsitz", dependent={r1, r2})
```

### Erstellung des Modells

Erstellen Sie das Modell, indem Sie alle erstellten Objekte hinzufügen:

```python
m = Model(
    informations=[i1, i2, i3],
    processes=[p1, p2, p3],
    applications=[a1, a2, a3],
    infrastructures=[it1, it2],
    rooms=[r1, r2],
    buildings=[g1],
)
```

### Exportieren der CSV-Dateien

Rufen Sie die Methode `write_csvs` auf der Instanz Ihres Modells auf, um die Strukturen in CSV-Dateien zu exportieren. Die Ableitung der Schutzbedarfe für die einzelnen Strukturen erfolgt automatisch nach dem Maximumprinzip:

```python
m.write_csvs("output_directory")
```

## Lizenz

Der Quellcode dieses Projekts ist unter der AGPL-3.0-Lizenz lizenziert. Weitere Informationen finden Sie in der [Lizenzdatei](LICENSE).
