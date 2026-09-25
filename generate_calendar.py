import csv
from datetime import datetime
from pathlib import Path

CSV = Path("courses.csv")
OUT = Path("ISDAT.ics")

def esc(s):
    return str(s or "").replace("\\","\\\\").replace(";","\\;").replace(",","\\,").replace("\n","\\n")

lines = [
    "BEGIN:VCALENDAR","VERSION:2.0",
    "PRODID:-//ISDAT//L2 Design graphique//FR",
    "CALSCALE:GREGORIAN","X-WR-CALNAME:ISDAT L2 Design graphique",
    "X-WR-TIMEZONE:Europe/Paris"
]

with CSV.open(encoding="utf-8-sig", newline="") as f:
    for i, r in enumerate(csv.DictReader(f), 1):
        d = r["anchor_date"]
        start = datetime.strptime(f'{d} {r["start"]}', "%Y-%m-%d %H:%M")
        end = datetime.strptime(f'{d} {r["end"]}', "%Y-%m-%d %H:%M")
        teacher = r.get("teacher","")
        desc = f'Enseignant·e : {teacher}' if teacher else ""
        lines += [
            "BEGIN:VEVENT",
            f"UID:isdat-{i}-{start.strftime('%Y%m%dT%H%M%S')}@calendar",
            f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART;TZID=Europe/Paris:{start.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND;TZID=Europe/Paris:{end.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{esc(r['course'])}",
            f"LOCATION:{esc(r.get('location',''))}",
            f"DESCRIPTION:{esc(desc)}",
        ]
        if r.get("repeat","").lower() == "biweekly":
            lines.append("RRULE:FREQ=WEEKLY;INTERVAL=2;COUNT=40")
        lines.append("END:VEVENT")

lines.append("END:VCALENDAR")
OUT.write_text("\r\n".join(lines)+"\r\n", encoding="utf-8")
print(f"Wrote {OUT}")
