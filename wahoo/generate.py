#!/usr/bin/env python3
"""Erzeugt die Wahoo-Workouts als .fit (strukturierte Workout-Datei) und .zwo.

Alle Leistungsziele sind in % FTP hinterlegt. Der Wahoo bzw. intervals.icu /
TrainingPeaks rechnet sie automatisch mit der dort eingetragenen FTP in Watt um.
FTP unten nur fuer die Watt-Angaben in der Uebersicht (PLAN.md).

Aufruf:  python3 wahoo/generate.py [FTP]
Keine externen Abhaengigkeiten (FIT-Encoder ist hier minimal implementiert).
"""
import datetime as dt
import os
import struct
import sys
from xml.sax.saxutils import escape

FTP = int(sys.argv[1]) if len(sys.argv) > 1 else 225
OUT = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------
# Workout-Definitionen
# Schritt: (name, dauer_s, low_pct, high_pct, intensity)
#   - steady: low == high (fuer FIT wird +-3 % Korridor gesetzt)
#   - Rampe (Warmup/Cooldown): low != high
# intensity: active | warmup | cooldown | rest | interval
# --------------------------------------------------------------------------
def wu(minutes, lo=50, hi=75):
    return ("Einfahren", minutes * 60, lo, hi, "warmup")

def cd(minutes, lo=60, hi=45):
    return ("Ausfahren", minutes * 60, lo, hi, "cooldown")

def st(name, seconds, pct, intensity="active"):
    return (name, seconds, pct, pct, intensity)

def rep(n, *block):
    out = []
    for i in range(1, n + 1):
        for name, dur, lo, hi, inten in block:
            out.append((f"{name} {i}/{n}", dur, lo, hi, inten))
    return out

WORKOUTS = [
    {
        "file": "00_Einrollen_50",
        "date": dt.date(2026, 11, 20),
        "title": "Lockeres Einrollen 50 min (optional)",
        "core": False,
        "desc": "Ganz lockerer erster Kontakt mit dem Rad, am Abend vor dem 3-h-Geburtstags-Padel. "
                "Nur Z1/Z2 (60-65 %), dazu 3 x 1 min hohe Trittfrequenz. Du solltest danach "
                "frischer sein als vorher - nichts drueckt, nichts brennt.",
        "steps": [
            wu(10, 50, 63),
            st("Grundlage", 15 * 60, 63),
            *rep(3, st("TF 100-110 rpm", 60, 60, "interval"), st("locker", 3 * 60, 62)),
            st("Grundlage", 8 * 60, 63),
            cd(5, 58, 45),
        ],
    },
    {
        "file": "01_Wiedereinstieg_90",
        "date": dt.date(2026, 11, 22),
        "title": "Wiedereinstieg 90 min (optional)",
        "core": False,
        "desc": "Erste Fahrt nach der Radpause, am Tag nach dem Geburtstags-Padel: 90 min ganz "
                "ruhig in Z2 (65-68 %), dazu 4 x 1 min hohe Trittfrequenz (100-110 rpm) bei "
                "lockerer Last. Wenn du nach Samstag platt bist: weglassen, Montag ist wichtiger.",
        "steps": [
            wu(10, 50, 65),
            st("Z2 Grundlage", 25 * 60, 66),
            *rep(4, st("TF 100-110 rpm", 60, 62, "interval"), st("Z2", 4 * 60, 66)),
            st("Z2 Grundlage", 30 * 60, 67),
            cd(5),
        ],
    },
    {
        "file": "02_Lange_Ausfahrt_3h",
        "date": dt.date(2026, 11, 23),
        "title": "Lange Ausfahrt 3 h",
        "core": True,
        "desc": "Wichtigste Einheit vor der Abreise: 3 h Z2 mit 2 x 10 min Sweet Spot (88 %) "
                "am Anstieg (z. B. Koenigstuhl). Sitzfleisch und Essen ueben: 60-80 g "
                "Kohlenhydrate pro Stunde ab Minute 30. Wenn die Zeit nicht reicht: mindestens 2:15 h.",
        "steps": [
            wu(15),
            st("Z2 Grundlage", 60 * 60, 68),
            st("SS Anstieg 1", 10 * 60, 88, "interval"),
            st("Z2 locker", 10 * 60, 63, "rest"),
            st("SS Anstieg 2", 10 * 60, 88, "interval"),
            st("Z2 Grundlage", 65 * 60, 67),
            cd(10),
        ],
    },
    {
        "file": "03_Tempo_3x10",
        "date": dt.date(2026, 11, 24),
        "title": "Tempo 3x10 min",
        "core": True,
        "desc": "3 x 10 min Tempo @ 83 % FTP, 5 min locker dazwischen, 80-90 rpm. Letzte Radeinheit "
                "vor der Abreise - danach haben die Beine bis Sonntag Zeit, sich zu erholen. Sind sie "
                "nach Montag noch schwer: nur 2 x 10 min.",
        "steps": [
            wu(10),
            st("Z2", 5 * 60, 65),
            *rep(3, st("Tempo 80-90 rpm", 10 * 60, 83, "interval"), st("locker", 5 * 60, 58, "rest")),
            st("Z2", 5 * 60, 65),
            cd(5),
        ],
    },
    {
        "file": "04_Kapstadt_Ankommen_60",
        "date": dt.date(2026, 11, 29),
        "title": "Ankommen in Kapstadt: 60 min locker (optional)",
        "core": False,
        "desc": "Nach der Anreise die Beine lockern und schauen, ob am Rad alles passt (Schaltung, "
                "Bremsen, Sattelhoehe nach dem Transport). Ganz locker, mit 3 x 1 min hoher Trittfrequenz.",
        "steps": [
            wu(5, 45, 58),
            st("locker", 15 * 60, 60),
            *rep(3, st("TF 100-110 rpm", 60, 62, "interval"), st("locker", 4 * 60, 60)),
            st("locker", 20 * 60, 60),
            cd(5, 55, 45),
        ],
    },
    {
        "file": "05_Kapstadt_Grundlage_2h",
        "date": dt.date(2026, 11, 30),
        "title": "Kapstadt-Grundlage 2 h",
        "core": True,
        "desc": "Erste richtige Runde in Kapstadt, z. B. Sea Point -> Camps Bay -> Hout Bay -> "
                "Chapman's Peak und zurueck. 2 h Z2, die zwei Tempo-Abschnitte (8 min @ 82 %) "
                "an Suikerbossie und Chapman's legen. Waerme: mehr trinken als in Heidelberg, mit Salz.",
        "steps": [
            wu(10),
            st("Z2 Grundlage", 40 * 60, 67),
            st("Tempo Anstieg 1", 8 * 60, 82, "interval"),
            st("Z2 locker", 5 * 60, 63, "rest"),
            st("Tempo Anstieg 2", 8 * 60, 82, "interval"),
            st("Z2 Grundlage", 42 * 60, 67),
            cd(7),
        ],
    },
    {
        "file": "06_SweetSpot_Chapmans_3x10",
        "date": dt.date(2026, 12, 1),
        "title": "Sweet Spot 'Chapman's Peak' 3x10 min",
        "core": True,
        "desc": "3 x 10 min @ 89 % FTP mit Kletter-Trittfrequenz 70-80 rpm, 5 min Pause. "
                "Gern direkt am Chapman's Peak (je eine Auffahrt pro Intervall). Mit Wattmessung "
                "fahren und in Strava hochladen - daran pruefen wir, ob FTP 225 W passt.",
        "steps": [
            wu(10),
            *rep(2, st("Aktivierung", 60, 100, "interval"), st("locker", 120, 55, "rest")),
            *rep(3, st("SS 70-80 rpm", 10 * 60, 89, "interval"), st("Pause", 5 * 60, 55, "rest")),
            st("Z2", 6 * 60, 65),
            cd(8),
        ],
    },
]

# --------------------------------------------------------------------------
# FIT-Encoder (nur was fuer Workout-Dateien gebraucht wird)
# --------------------------------------------------------------------------
_CRC_TABLE = [0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
              0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400]

def fit_crc(data, crc=0):
    for byte in data:
        tmp = _CRC_TABLE[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ _CRC_TABLE[byte & 0xF]
        tmp = _CRC_TABLE[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ _CRC_TABLE[(byte >> 4) & 0xF]
    return crc

# Base types: (fit_base_type_byte, struct_fmt, size)
ENUM = (0x00, "B", 1)
UINT16 = (0x84, "H", 2)
UINT32 = (0x86, "I", 4)
UINT32Z = (0x8C, "I", 4)
def STRING(n):
    return (0x07, f"{n}s", n)

INTENSITY = {"active": 0, "rest": 1, "warmup": 2, "cooldown": 3, "recovery": 4, "interval": 5}
FIT_EPOCH = dt.datetime(1989, 12, 31, tzinfo=dt.timezone.utc)
NAME_LEN = 32

class FitWriter:
    def __init__(self):
        self.records = bytearray()

    def define(self, local, global_num, fields):
        self.fields = getattr(self, "fields", {})
        self.fields[local] = fields
        rec = struct.pack("<BBBHB", 0x40 | local, 0, 0, global_num, len(fields))
        for num, (base, _fmt, size) in fields:
            rec += struct.pack("<BBB", num, size, base)
        self.records += rec

    def data(self, local, values):
        fields = self.fields[local]
        rec = bytes([local])
        for (num, (base, fmt, size)), val in zip(fields, values):
            if base == 0x07:
                raw = val.encode("utf-8")[: size - 1]
                val = raw + b"\x00" * (size - len(raw))
            rec += struct.pack("<" + fmt, val)
        self.records += rec

    def to_bytes(self):
        header = struct.pack("<BBHI4s", 14, 0x20, 2132, len(self.records), b".FIT")
        header += struct.pack("<H", fit_crc(header))
        body = header + bytes(self.records)
        return body + struct.pack("<H", fit_crc(body))


def build_fit(w, created):
    steps = w["steps"]
    f = FitWriter()
    # file_id
    f.define(0, 0, [(0, ENUM), (1, UINT16), (2, UINT16), (3, UINT32Z), (4, UINT32)])
    ts = int((created - FIT_EPOCH).total_seconds())
    f.data(0, [5, 255, 0, 0x5A1E0000 + len(w["file"]), ts])  # type 5 = workout, 255 = development
    # workout
    f.define(1, 26, [(4, ENUM), (6, UINT16), (8, STRING(NAME_LEN))])
    f.data(1, [2, len(steps), w["file"].replace("_", " ")[3:]])  # sport 2 = cycling
    # workout_step
    f.define(2, 27, [(254, UINT16), (0, STRING(NAME_LEN)), (1, ENUM), (2, UINT32),
                     (3, ENUM), (4, UINT32), (5, UINT32), (6, UINT32), (7, ENUM)])
    for i, (name, dur, lo, hi, inten) in enumerate(steps):
        if lo == hi:
            band = 3 if lo < 120 else 15
            lo_t, hi_t = lo - band, hi + band
        else:
            lo_t, hi_t = min(lo, hi), max(lo, hi)
        # duration_type 0 = time (ms); target_type 4 = power; target_value 0 = custom range
        # custom power 0..1000 = % FTP
        f.data(2, [i, name, 0, dur * 1000, 4, 0, lo_t, hi_t, INTENSITY[inten]])
    return f.to_bytes()


# --------------------------------------------------------------------------
# ZWO (Zwift-Format, wird von intervals.icu und TrainingPeaks importiert)
# --------------------------------------------------------------------------
def build_zwo(w):
    lines = [
        "<workout_file>",
        "  <author>Training Plan</author>",
        f"  <name>{escape(w['file'].replace('_', ' ')[3:])}</name>",
        f"  <description>{escape(w['desc'])}</description>",
        "  <sportType>bike</sportType>",
        "  <tags/>",
        "  <workout>",
    ]
    for name, dur, lo, hi, inten in w["steps"]:
        if inten == "warmup":
            lines.append(f'    <Warmup Duration="{dur}" PowerLow="{lo/100:.2f}" PowerHigh="{hi/100:.2f}"/>')
        elif inten == "cooldown":
            lines.append(f'    <Cooldown Duration="{dur}" PowerLow="{lo/100:.2f}" PowerHigh="{hi/100:.2f}"/>')
        else:
            lines.append(f'    <SteadyState Duration="{dur}" Power="{lo/100:.2f}">'
                         f'<textevent timeoffset="0" message="{escape(name)}"/></SteadyState>')
    lines += ["  </workout>", "</workout_file>", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Kennzahlen + Uebersicht
# --------------------------------------------------------------------------
def stats(w):
    total = sum(s[1] for s in w["steps"])
    # TSS ueber normierte Leistung (Rampen ueber Mittelwert)
    w4 = sum(s[1] * (((s[2] + s[3]) / 200) ** 4) for s in w["steps"])
    np_ = (w4 / total) ** 0.25
    tss = total / 3600 * np_ ** 2 * 100
    return total, np_, tss

WD = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

def watts(pct):
    return round(FTP * pct / 100)

def plan_md():
    out = [
        "# Wahoo-Workouts: Fit fuer die Kapstadt-Saison (20.11. - 01.12.2026)",
        "",
        f"Alle Ziele sind in **% FTP** hinterlegt. Die Watt-Angaben unten gelten fuer **FTP {FTP} W**;",
        "der Wahoo rechnet automatisch mit der FTP, die in deiner Wahoo-App eingetragen ist.",
        "",
        "| # | Datum | Workout | Dauer | IF | TSS | Pflicht? |",
        "|---|-------|---------|-------|----|-----|----------|",
    ]
    for w in WORKOUTS:
        i = int(w["file"][:2])
        total, np_, tss = stats(w)
        d = f"{WD[w['date'].weekday()]} {w['date']:%d.%m.}" if w["date"] else "Vortag Rennen"
        core = "Kern" if w["core"] else "optional"
        out.append(f"| {i} | {d} | {w['title']} | {total // 60} min | {np_:.2f} | {tss:.0f} | {core} |")
    out += [
        "",
        "## Ausgangslage laut Strava",
        "",
        "| Monat | Radfahrten | km (ca.) | Bemerkung |",
        "|---|---|---|---|",
        "| Juni | 15 | 850 | 170 km (05.06.), 149 km / 3.100 hm (13.06.) |",
        "| Juli | 6 | 250 | |",
        "| August | 13 | 635 | bis 95 km |",
        "| September | 12 | 520 | bis 83 km, ab Mitte Sept. 4-5x/Woche Padel |",
        "| Oktober | 5 | 175 | letzte Fahrt mit Watt: 16.10., letzte Fahrt: 28.10. |",
        "| November | 0 | 0 | nur Padel (4-5x/Woche, je 1,5-2 h) |",
        "",
        "- **Letzte Leistungswerte:** 02.10. 20 min 263 W; 16.10. Koenigstuhl 40 min @ 217 W, 20 min 243 W.",
        "- **FTP in Strava:** 239 W (manuell). Nach gut 3 Wochen ohne Rad rechne ich mit 5-8 % weniger",
        f"  radspezifischer Leistung -> fuer diesen Block **FTP {FTP} W**. Bitte so in der Wahoo-App eintragen.",
        "- **Gut:** solide Sommer-Grundlage und durch Padel eine gute Herz-Kreislauf-Fitness.",
        "- **Fehlt:** Sitzfleisch und Dauerleistung auf dem Rad - genau das braucht die 150-km-Runde.",
        "",
        "## Ablauf",
        "",
        "| Tag | Was |",
        "|---|---|",
        "| Fr 20.11. | Rad 0: Lockeres Einrollen 50 min (optional, abends) |",
        "| Sa 21.11. | Geburtstag: 3 h Padel (12-15 Uhr) - harte Einheit, kein Rad |",
        "| So 22.11. | Rad 1: Wiedereinstieg 90 min (optional) |",
        "| Mo 23.11. | Rad 2: Lange Ausfahrt 3 h |",
        "| Di 24.11. | Rad 3: Tempo 3x10 min |",
        "| Mi 25.11. | frei, abends Abreise |",
        "| Do 26.11. | frei |",
        "| Fr 27.11. | Padel (max. 2 h, moderat) |",
        "| Sa 28.11. | Padel optional (max. 1,5 h) oder frei |",
        "| So 29.11. | Ankunft Kapstadt - Rad 4: 60 min locker (optional) |",
        "| Mo 30.11. | Rad 5: Kapstadt-Grundlage 2 h |",
        "| Di 01.12. | Rad 6: Sweet Spot an Chapman's Peak |",
        "",
        "**Aufbau:** Drei Radtage in Heidelberg (22.-24.11.) als kleiner Block - danach erholen sich",
        "die Beine bis Sonntag. Das Padel am Fr/Sa haelt die Herz-Kreislauf-Fitness, ersetzt aber",
        "keine Radkilometer. In Kapstadt erst locker ankommen, dann Grundlage, dann Sweet Spot.",
        "Zeitverschiebung ist nur 1 h, also kein Jetlag - aber der Flug macht muede: am Ankunftstag nichts erzwingen.",
        "",
        "**Nur 4 Einheiten?** Fahr die Kern-Einheiten 2, 3, 5 und 6. **5 oder 6?** Nimm 1 und/oder 4 dazu.",
        "",
        "**Erste Sonntagsrunde (06.12.):** Nach diesem Block sind 3 h sicher, 150 km (5+ h) noch",
        "grenzwertig. Plan eine Abkuerzung ein oder fahr die erste Runde konsequent im Windschatten",
        "und am unteren Ende der Wattbereiche unten.",
        "",
        "## Sonntagsrunde 150 km - Pacing",
        "",
        f"- **Flach / in der Gruppe:** 60-72 % FTP = **{watts(60)}-{watts(72)} W**. Im Windschatten ruhig darunter.",
        f"- **Anstiege (Chapman's, Suikerbossie, Smitswinkel):** max. 85-90 % = **{watts(85)}-{watts(90)} W**.",
        f"  Nicht ueber {watts(100)} W gehen, auch wenn die Gruppe anzieht - lieber kurz abreissen lassen und oben wieder ran.",
        f"- **Ziel-Normalized-Power** fuer 5+ h: ca. 65-70 % = **{watts(65)}-{watts(70)} W**.",
        "- **Essen:** 60-80 g Kohlenhydrate pro Stunde ab Minute 30, 500-750 ml pro Stunde trinken",
        "  (bei Kapstadt-Hitze und Suedostwind eher mehr, mit Salz).",
        "- **Coffee Rides unter der Woche** (Sea Point <-> Chapman's): als Grundlage zaehlen sie, wenn du die",
        "  Anstiege im Sweet-Spot-Bereich faehrst - dann ersetzen sie Einheit 2 oder 6.",
        "",
    ]
    for w in WORKOUTS:
        i = int(w["file"][:2])
        total, _, _ = stats(w)
        out += [f"## {i}. {w['title']} - {total // 60} min", "", w["desc"], "",
                "| Abschnitt | Dauer | % FTP | Watt |", "|---|---|---|---|"]
        # Wiederholungen fuer die Uebersicht zusammenfassen
        for name, dur, lo, hi, _ in w["steps"]:
            d = f"{dur // 60}:{dur % 60:02d}"
            p = f"{lo}" if lo == hi else f"{lo} -> {hi}"
            wt = f"{watts(lo)}" if lo == hi else f"{watts(lo)} -> {watts(hi)}"
            out.append(f"| {name} | {d} | {p} | {wt} |")
        out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------
# intervals.icu Text-Format (zum Reinkopieren in den Workout-Builder am Handy)
# --------------------------------------------------------------------------
import re

def _dur(sec):
    m, s_ = divmod(sec, 60)
    if m and s_:
        return f"{m}m{s_}s"
    return f"{m}m" if m else f"{s_}s"

def _line(name, dur, lo, hi):
    name = re.sub(r" \d+/\d+$", "", name)
    cad = ""
    m = re.search(r"(\d+-\d+) rpm", name)
    if m:
        cad = f" {m.group(1)}rpm"
        name = name.replace(m.group(0), "").strip()
    name = re.sub(r"(Anstieg) \d+$", r"\1", name)
    name = re.sub(r"^Z2\b\s*", "", name).strip() or "Grundlage"
    power = f"{lo}%" if lo == hi else f"ramp {lo}-{hi}%"
    return f"- {name} {_dur(dur)} {power}{cad}"

def build_icu(w):
    steps, out, i = w["steps"], [], 0
    while i < len(steps):
        m = re.search(r" 1/(\d+)$", steps[i][0])
        if m:
            n = int(m.group(1))
            k = 1
            while i + k < len(steps) and not steps[i + k][0].endswith(f" 2/{n}"):
                k += 1
            out += ["", f"{n}x"] + [_line(*st_[:4]) for st_ in steps[i:i + k]] + [""]
            i += k * n
        else:
            out.append(_line(*steps[i][:4]))
            i += 1
    text = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip()

def icu_md():
    out = [
        "# Workouts fuer intervals.icu (zum Reinkopieren)",
        "",
        "Pro Workout: in intervals.icu im Kalender auf den Tag tippen -> neues Workout (Radfahren) ->",
        "Name eintragen -> den Text-Block unten komplett in das Beschreibungsfeld kopieren -> speichern.",
        "intervals.icu baut daraus automatisch die Intervalle.",
        "",
    ]
    for w in WORKOUTS:
        i = int(w["file"][:2])
        d = f"{WD[w['date'].weekday()]} {w['date']:%d.%m.}"
        out += [f"## {i}. {d} - {w['title']}", "", f"Name: `{w['title']}`", "", "```", build_icu(w), "```", ""]
    return "\n".join(out)


def main():
    created = dt.datetime(2026, 11, 20, 12, 0, tzinfo=dt.timezone.utc)
    for sub in ("fit", "zwo"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    for w in WORKOUTS:
        with open(os.path.join(OUT, "fit", w["file"] + ".fit"), "wb") as fh:
            fh.write(build_fit(w, created))
        with open(os.path.join(OUT, "zwo", w["file"] + ".zwo"), "w", encoding="utf-8") as fh:
            fh.write(build_zwo(w))
    with open(os.path.join(OUT, "PLAN.md"), "w", encoding="utf-8") as fh:
        fh.write(plan_md())
    with open(os.path.join(OUT, "INTERVALS_ICU.md"), "w", encoding="utf-8") as fh:
        fh.write(icu_md())
    for w in WORKOUTS:
        total, np_, tss = stats(w)
        print(f"{w['file']:32s} {total // 60:4d} min  IF {np_:.2f}  TSS {tss:5.0f}  steps {len(w['steps'])}")


if __name__ == "__main__":
    main()
