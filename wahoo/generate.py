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

FTP = int(sys.argv[1]) if len(sys.argv) > 1 else 221
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
        "file": "01_Grundlage_Sprints",
        "date": dt.date(2026, 11, 21),
        "title": "Grundlage + Sprints",
        "core": False,
        "desc": "Lockere Grundlage (Z2) mit 6 kurzen Sprints zum Wachwerden der Beine. "
                "Sprints: 10 s maximal aus ca. 80-90 rpm, dazwischen locker rollen.",
        "steps": [
            wu(10),
            st("Z2 Grundlage", 30 * 60, 68),
            *rep(6, st("Sprint", 10, 160, "interval"), st("locker", 290, 58, "rest")),
            st("Z2 Grundlage", 15 * 60, 68),
            cd(5),
        ],
    },
    {
        "file": "02_SweetSpot_3x12",
        "date": dt.date(2026, 11, 24),
        "title": "Sweet Spot 3x12 min",
        "core": True,
        "desc": "3 x 12 min Sweet Spot (90-91 % FTP), 5 min Pause. Gleichmaessig fahren, "
                "Trittfrequenz 85-95 rpm. Baut Schwellen-Ausdauer auf.",
        "steps": [
            wu(10),
            *rep(2, st("Aktivierung", 60, 100, "interval"), st("locker", 120, 55, "rest")),
            *rep(3, st("Sweet Spot", 12 * 60, 91, "interval"), st("Pause", 5 * 60, 55, "rest")),
            cd(8),
        ],
    },
    {
        "file": "03_VO2max_5x3",
        "date": dt.date(2026, 11, 26),
        "title": "VO2max 5x3 min",
        "core": True,
        "desc": "5 x 3 min @ 118 % FTP, 3 min Pause. Die ersten 30 s nicht ueberpacen, "
                "die letzte Minute muss richtig hart sein.",
        "steps": [
            wu(12),
            *rep(3, st("Openers", 30, 110, "interval"), st("locker", 30, 55, "rest")),
            st("locker", 4 * 60, 55, "rest"),
            *rep(5, st("VO2max", 3 * 60, 118, "interval"), st("Pause", 3 * 60, 50, "rest")),
            st("Z2", 10 * 60, 65),
            cd(6, 55, 45),
        ],
    },
    {
        "file": "04_OverUnder_Rennsimulation",
        "date": dt.date(2026, 11, 28),
        "title": "Over-Unders (Rennsimulation)",
        "core": True,
        "desc": "3 Bloecke a 12 min: jeweils 4 x (2 min @ 92 % / 1 min @ 110 %), 5 min Pause. "
                "Simuliert die wechselnde Last im Rennen (Antritte aus Kurven, Anstiege).",
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
    {
        "file": "05_Lange_Grundlage",
        "date": dt.date(2026, 11, 29),
        "title": "Lange Grundlage (optional)",
        "core": False,
        "desc": "2 h ruhige Grundlage (Z2, 65-72 %). Gern auch draussen bzw. auf dem Crosser. "
                "Wenn die Beine nach Samstag schwer sind: auf 75-90 min kuerzen.",
        "steps": [
            wu(10),
            st("Z2 Grundlage", 50 * 60, 68),
            st("Z2 hoehere TF (100 rpm)", 5 * 60, 65),
            st("Z2 Grundlage", 45 * 60, 70),
            cd(10),
        ],
    },
    {
        "file": "06_30-30_Starts",
        "date": dt.date(2026, 12, 1),
        "title": "Starts + 30/30",
        "core": True,
        "desc": "3 Start-Sprints (15 s, aus niedriger TF wie beim Rennstart), danach 2 x 8 x "
                "(30 s @ 130 % / 30 s @ 50 %). Rennspezifisch, aber kurz - gut als letzter "
                "harter Reiz vor dem Saisoneinstieg.",
        "steps": [
            wu(12),
            *rep(3, st("Start-Sprint", 15, 180, "interval"), st("locker", 165, 55, "rest")),
            *rep(8, st("S1 30s on", 30, 130, "interval"), st("S1 30s off", 30, 50, "rest")),
            st("Pause", 5 * 60, 55, "rest"),
            *rep(8, st("S2 30s on", 30, 130, "interval"), st("S2 30s off", 30, 50, "rest")),
            st("Pause", 5 * 60, 55, "rest"),
            st("Z2", 8 * 60, 65),
            cd(5),
        ],
    },
    {
        "file": "07_Opener_Vortag_Rennen",
        "date": None,
        "title": "Opener (Tag vor dem Rennen, Bonus)",
        "core": False,
        "desc": "Kurzer Opener fuer den Tag vor dem ersten Rennen: locker mit 3 x 1 min "
                "@ 105 % und 3 kurzen Sprints. Soll frisch machen, nicht muede.",
        "steps": [
            wu(10),
            st("Z2", 10 * 60, 65),
            *rep(3, st("Opener", 60, 105, "interval"), st("locker", 120, 55, "rest")),
            *rep(3, st("Sprint", 10, 150, "interval"), st("locker", 110, 55, "rest")),
            st("Z2", 5 * 60, 62),
            cd(5),
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
        "# Wahoo-Workouts: Einstieg in die Saison (21.11. - 01.12.2026)",
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
        "**Nur 4 Einheiten?** Fahr die Kern-Einheiten 2, 3, 4 und 6. **5 oder 6?** Nimm 1 und/oder 5 dazu.",
        "Ruhetage: So 22., Mo 23., Mi 25., Fr 27., Mo 30.11. Verschieben um +-1 Tag ist ok, aber",
        "nie zwei harte Einheiten (2, 3, 4, 6) an aufeinanderfolgenden Tagen.",
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
