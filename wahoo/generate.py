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

FTP = int(sys.argv[1]) if len(sys.argv) > 1 else 239
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
        "file": "01_Grundlage_Tempo_2h30",
        "date": dt.date(2026, 11, 21),
        "title": "Grundlage 2:30 h + Tempo",
        "core": True,
        "desc": "Wiedereinstieg aufs Rad nach der Pause: 2:30 h ruhige Grundlage (Z2) mit "
                "3 x 6 min Tempo (85 %). Gern draussen und bergig. Ab der ersten Stunde "
                "60 g Kohlenhydrate pro Stunde essen/trinken - das ueben wir fuer die 150 km.",
        "steps": [
            wu(10),
            st("Z2 Grundlage", 60 * 60, 68),
            *rep(3, st("Tempo", 6 * 60, 85, "interval"), st("locker", 4 * 60, 62, "rest")),
            st("Z2 Grundlage", 45 * 60, 67),
            cd(5),
        ],
    },
    {
        "file": "02_SweetSpot_Chapmans_3x10",
        "date": dt.date(2026, 11, 24),
        "title": "Sweet Spot 'Chapman's Peak' 3x10 min",
        "core": True,
        "desc": "3 x 10 min @ 89 % FTP mit Kletter-Trittfrequenz 70-80 rpm, 5 min Pause. "
                "Entspricht ungefaehr dem Anstieg auf Chapman's Peak im Gruppentempo.",
        "steps": [
            wu(10),
            *rep(2, st("Aktivierung", 60, 100, "interval"), st("locker", 120, 55, "rest")),
            *rep(3, st("SS 70-80 rpm", 10 * 60, 89, "interval"), st("Pause", 5 * 60, 55, "rest")),
            st("Z2", 6 * 60, 65),
            cd(8),
        ],
    },
    {
        "file": "03_VO2max_Attacken_5x3",
        "date": dt.date(2026, 11, 26),
        "title": "VO2max 5x3 min (Attacken am Anstieg)",
        "core": False,
        "desc": "5 x 3 min @ 112 % FTP, 3 min Pause. Fuer die Momente, in denen die Gruppe "
                "am Suikerbossie oder an Chapman's anzieht. Wegen der Radpause bewusst etwas "
                "unter dem ueblichen Niveau (112 statt 118 %).",
        "steps": [
            wu(12),
            *rep(3, st("Openers", 30, 110, "interval"), st("locker", 30, 55, "rest")),
            st("locker", 4 * 60, 55, "rest"),
            *rep(5, st("VO2max", 3 * 60, 112, "interval"), st("Pause", 3 * 60, 50, "rest")),
            st("Z2", 10 * 60, 65),
            cd(6, 55, 45),
        ],
    },
    {
        "file": "04_Lange_Ausfahrt_3h30",
        "date": dt.date(2026, 11, 28),
        "title": "Lange Ausfahrt 3:30 h",
        "core": True,
        "desc": "Generalprobe fuer die Sonntagsrunde: 3:30 h Z2 mit 2 x 12 min Sweet Spot "
                "(am besten an einem Anstieg). 60-80 g Kohlenhydrate/h, alle 15-20 min "
                "trinken. Draussen fahren, der ROAM zeigt dir die Zielbereiche.",
        "steps": [
            wu(15),
            st("Z2 Grundlage", 75 * 60, 68),
            st("SS Anstieg 1", 12 * 60, 88, "interval"),
            st("Z2 locker", 10 * 60, 63, "rest"),
            st("SS Anstieg 2", 12 * 60, 88, "interval"),
            st("Z2 Grundlage", 75 * 60, 67),
            cd(11),
        ],
    },
    {
        "file": "05_Regeneration_60",
        "date": dt.date(2026, 11, 29),
        "title": "Lockeres Ausrollen (optional)",
        "core": False,
        "desc": "60 min ganz locker (Z1/Z2, unter 62 %). Beine durchbewegen nach dem langen "
                "Samstag. Alternativ: komplett frei oder ein lockeres Padel-Match.",
        "steps": [
            wu(5, 45, 58),
            st("locker Z1-Z2", 50 * 60, 58),
            cd(5, 55, 45),
        ],
    },
    {
        "file": "06_OverUnder_Gruppenfahrt",
        "date": dt.date(2026, 12, 1),
        "title": "Over-Unders (Gruppenfahrt)",
        "core": True,
        "desc": "3 Bloecke a 12 min: jeweils 4 x (2 min @ 92 % / 1 min @ 110 %), 5 min Pause. "
                "Simuliert das Tempo in der Gruppe: am Anstieg knapp unter der Schwelle "
                "mitfahren und bei jedem Antritt kurz drueber gehen.",
        "steps": [
            wu(15),
            *rep(2, st("Aktivierung", 60, 105, "interval"), st("locker", 120, 55, "rest")),
            *[s for b in range(1, 4) for s in (
                *[(f"B{b} {n}", d, lo, hi, it) for n, d, lo, hi, it in rep(
                    4, st("Under", 120, 92, "interval"), st("Over", 60, 110, "interval"))],
                (f"B{b} Pause", 5 * 60, 55, 55, "rest"),
            )],
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
        "# Wahoo-Workouts: Fit fuer die Kapstadt-Saison (21.11. - 01.12.2026)",
        "",
        f"Alle Ziele sind in **% FTP** hinterlegt. Die Watt-Angaben unten gelten fuer **FTP {FTP} W**;",
        "der Wahoo rechnet automatisch mit der FTP, die in deiner Wahoo-App eingetragen ist.",
        "",
        "| # | Datum | Workout | Dauer | IF | TSS | Pflicht? |",
        "|---|-------|---------|-------|----|-----|----------|",
    ]
    for i, w in enumerate(WORKOUTS, 1):
        total, np_, tss = stats(w)
        d = f"{WD[w['date'].weekday()]} {w['date']:%d.%m.}" if w["date"] else "Vortag Rennen"
        core = "Kern" if w["core"] else "optional"
        out.append(f"| {i} | {d} | {w['title']} | {total // 60} min | {np_:.2f} | {tss:.0f} | {core} |")
    out += [
        "",
        f"FTP {FTP} W aus Strava (manuell gesetzt). 20-min-Bestwert 2026: 263 W (02.10.) -> die FTP ist eher",
        "konservativ. Letzte Radfahrt laut Strava: 28.10., seitdem 3-5x/Woche Padel. Deshalb startet der Plan",
        "mit Grundlage und etwas reduzierter VO2max-Intensitaet.",
        "",
        "**Nur 4 Einheiten?** Fahr die Kern-Einheiten 1, 2, 4 und 6 (die langen Fahrten sind fuer die 150 km",
        "am wichtigsten). **5 oder 6?** Nimm 3 und/oder 5 dazu.",
        "",
        "Freie Tage fuers Rad: So 22., Mo 23., Mi 25., Fr 27., Mo 30.11. Padel passt gut auf Mo/Mi -",
        "aber **kein langes Padel am Tag vor Einheit 1, 4 oder 6**, und nie zwei harte Einheiten",
        "(2, 3, 6) an aufeinanderfolgenden Tagen.",
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
    for i, w in enumerate(WORKOUTS, 1):
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
    for w in WORKOUTS:
        total, np_, tss = stats(w)
        print(f"{w['file']:32s} {total // 60:4d} min  IF {np_:.2f}  TSS {tss:5.0f}  steps {len(w['steps'])}")


if __name__ == "__main__":
    main()
