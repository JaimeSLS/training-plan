# Wahoo ROAM – Workouts für den Saisoneinstieg

Plan + alle Intervalle mit Watt: siehe [PLAN.md](PLAN.md).

| Ordner | Inhalt | Wofür |
|---|---|---|
| `zwo/` | Workouts im .zwo-Format | Import in **intervals.icu** oder **TrainingPeaks** (empfohlen) |
| `fit/` | Strukturierte FIT-Workout-Dateien | Direkt-Import in die Wahoo-App (Fallback) |
| `generate.py` | Generator | Workouts ändern / neu erzeugen: `python3 wahoo/generate.py 230` (FTP optional, nur für Watt in PLAN.md) |

Alle Ziele sind in **% FTP** gespeichert. Der ROAM rechnet mit der FTP aus deinem
Wahoo-Profil. **Trag deine aktuelle FTP also zuerst in der Wahoo-App ein**
(Profil → Leistungszonen / FTP).

## So kommen die Workouts auf den ROAM

### Weg 1 (empfohlen): intervals.icu – kostenlos, synct automatisch
1. Konto auf intervals.icu anlegen.
2. *Settings → Connections*: **Wahoo** verbinden und das Hochladen geplanter Workouts
   erlauben. Optional auch Strava verbinden (für die Analyse deiner Fahrten).
3. FTP in intervals.icu unter *Settings → Cycling* eintragen.
4. Die `.zwo`-Dateien aus `zwo/` per Drag & Drop **direkt auf den passenden Tag im Kalender**
   ziehen (Daten stehen in PLAN.md).
5. Die Workouts tauchen in der Wahoo-App unter **Geplante Workouts** auf. ROAM mit der App
   synchronisieren, dann am ROAM: *Workouts → Geplant* → Workout starten.

### Weg 2: TrainingPeaks
TrainingPeaks mit der Wahoo-App verbinden, `.zwo` in die Workout-Library importieren und auf
die Tage legen. Geplante Workouts synchronisieren danach auf den ROAM.

### Weg 3 (Fallback): FIT-Datei direkt
`.fit` aus `fit/` auf dem Handy öffnen → *Teilen / Öffnen mit* → **Wahoo**. Wahoo dokumentiert
diesen Weg für Workouts nicht offiziell, er klappt je nach App- und Firmware-Version.
Wenn's nicht geht: Weg 1.
