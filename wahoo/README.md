# Wahoo ROAM – Workouts für die Kapstadt-Saison

- [PLAN.md](PLAN.md): Ablauf, alle Intervalle mit Watt, Pacing für die 150 km
- [INTERVALS_ICU.md](INTERVALS_ICU.md): alle Workouts als Text zum Reinkopieren in intervals.icu (Handy)
- `zwo/`: dieselben Workouts als .zwo-Dateien (Upload in intervals.icu oder TrainingPeaks am Computer)
- `fit/`: strukturierte FIT-Workout-Dateien (für Tools, die FIT-Workouts importieren)
- `generate.py`: erzeugt alles neu: `python3 wahoo/generate.py [FTP]`

Alle Ziele sind in **% FTP** gespeichert. Der ROAM rechnet mit der FTP aus deinem Wahoo-Profil.

## So kommen die Workouts auf den ROAM (alles am Handy)

Wahoo nimmt geplante Workouts nur von einem verbundenen Trainingsdienst an. Eine Workout-Datei
direkt in die Wahoo-App zu laden, ist nicht vorgesehen (das geht nur mit Routen). Der Weg führt
deshalb über **intervals.icu**. Das ist kostenlos und funktioniert im Handy-Browser.

### Einmalig einrichten (ca. 10 min)
1. **intervals.icu** im Handy-Browser öffnen und ein Konto anlegen (Anmeldung mit Strava geht auch).
2. In intervals.icu unter **Settings** zu **Wahoo** scrollen → **Connect** → mit deinem
   Wahoo-Konto anmelden und **alle Berechtigungen erlauben** (auch Schreiben, sonst kommen
   keine Workouts an).
3. Im Wahoo-Bereich der Settings den Haken beim **Hochladen geplanter Workouts** setzen
   (sinngemäß „Upload planned workouts“).
4. In den Settings bei **Radfahren** die **FTP auf 225 W** setzen und die **Zeitzone** prüfen:
   Europe/Berlin, ab Kapstadt Africa/Johannesburg. Bei falscher Zeitzone landen Workouts
   sonst am falschen Tag.
5. In der **Wahoo-App** (ROAM 3) bzw. der **ELEMNT-App** (ROAM / ROAM 2) im Profil ebenfalls
   **FTP 225 W** eintragen.

### Workouts eintragen (pro Workout ca. 1 min)
6. `INTERVALS_ICU.md` öffnen. Für jedes Workout in intervals.icu im **Kalender auf den Tag tippen**
   → neues **Workout** (Radfahren) → Namen eintragen → den Text-Block in die Beschreibung
   kopieren → speichern. intervals.icu macht daraus automatisch die Intervall-Grafik.

### Auf den ROAM
7. intervals.icu schickt die geplanten Workouts der **nächsten ~7 Tage** automatisch an Wahoo.
   Die Kapstadt-Workouts kommen also von selbst nach, sobald sie in dieses Fenster rutschen.
8. Wahoo- bzw. ELEMNT-App öffnen und den ROAM synchronisieren (ROAM einschalten, App offen,
   Bluetooth an). Die Workouts erscheinen dort unter den **geplanten Workouts**.
9. Am ROAM im Menü bei den Workouts/Plänen das Workout des Tages auswählen und starten.
   Der ROAM zeigt dir dann pro Abschnitt die Zielwatt an.

**Klappt etwas nicht?** Meist fehlt die Schreib-Berechtigung (Wahoo in intervals.icu trennen
und neu verbinden) oder die Zeitzone stimmt nicht. Gibt es nach 15 min nichts zu sehen: die
App einmal schließen und neu öffnen, den ROAM neu synchronisieren.

### Alternative am Computer
Die `.zwo`-Dateien aus `zwo/` per Drag & Drop direkt auf die Tage im intervals.icu-Kalender
ziehen. Schritt 6 entfällt dann.
