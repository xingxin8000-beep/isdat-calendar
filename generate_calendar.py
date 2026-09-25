import csv
from datetime import datetime, date, timedelta

COLORS = {
    "obligatoire": "#FFFFFF",
    "au choix": "#8B73D6",
    "facultatif": "#B7A6E6",
}

HOLIDAYS = [
    (date(2026, 12, 21), date(2027, 1, 3), "Vacances de Noël"),
    (date(2027, 2, 8), date(2027, 2, 21), "Vacances d’hiver"),
    (date(2027, 4, 12), date(2027, 4, 18), "Vacances de printemps"),
]

SCHOOL_EVENTS = [
    ("Rentrée administrative & pédagogique — Semestres 3 et 5", "2026-09-23", "08:30", "2026-09-23", "12:00", "obligatoire", "Design Graphique — Semestre 3"),
    ("Bilan sem. 3", "2027-01-14", "09:00", "2027-01-15", "12:00", "obligatoire", "Design Graphique"),
    ("Préparation des ateliers pour les Journées Portes Ouvertes", "2027-02-02", "09:00", "2027-02-04", "18:00", "facultatif", "Les 3 départements"),
    ("Journées Portes Ouvertes", "2027-02-05", "09:00", "2027-02-06", "18:00", "facultatif", "Vendredi 5 et samedi 6 février"),
    ("Fin du semestre d’hiver", "2027-02-05", "09:00", "2027-02-05", "18:00", "obligatoire", "16 semaines"),
    ("Début du semestre d’été", "2027-02-22", "09:00", "2027-02-22", "18:00", "obligatoire", "16 semaines"),
    ("Présentation des départements aux étudiant·es de l’année 1", "2027-02-25", "14:00", "2027-02-25", "16:00", "facultatif", "Jeudi 25 février à 14h"),
    ("Rendu écrit DNA", "2027-03-03", "09:00", "2027-03-03", "12:00", "obligatoire", "Avant 12h"),
    ("Préselection des dossiers pour les commissions d’équivalence", "2027-03-03", "09:00", "2027-03-10", "18:00", "facultatif", "Du 3 au 10 mars"),
    ("Commissions d’équivalence / entrée 2d cycle / changement d’option", "2027-03-31", "09:00", "2027-04-02", "18:00", "facultatif", "31 mars, 1er et 2 avril"),
    ("Rencontre DNSEP", "2027-04-01", "14:00", "2027-04-02", "12:00", "facultatif", "Design Graphique"),
    ("Bilan sem. 6 — liste définitive DNA", "2027-04-28", "14:00", "2027-04-30", "12:00", "obligatoire", "Design Graphique"),
    ("Concours d’entrée", "2027-05-03", "09:00", "2027-05-05", "18:00", "facultatif", "3 au 5 mai"),
    ("Semaine de préparation des programmes 2027 / 2028 — cours suspendus", "2027-05-11", "09:00", "2027-05-14", "18:00", "obligatoire", "Cours suspendus, présence de tous les enseignant·es"),
]

def esc(value):
    return str(value).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def dt_local(day, time_text):
    return f"{day:%Y%m%d}T{time_text.replace(':','')}00"

def in_holiday(day):
    return any(start <= day <= end for start, end, _ in HOLIDAYS)

stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

ics = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//ISDAT//L2 Design graphique 2026-2027//FR",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:ISDAT L2 Design graphique",
    "X-WR-TIMEZONE:Europe/Paris",
    "REFRESH-INTERVAL;VALUE=DURATION:P1D",
    "X-PUBLISHED-TTL:P1D",
]

uid = 1

with open("courses.csv", encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        anchor = datetime.strptime(row["anchor_date"], "%Y-%m-%d").date()
        typ = row["type"]
        repeat = row["repeat"].strip().lower()
        interval = 1 if repeat == "weekly" else 2
        description = ""
        if row["teacher"].strip():
            description = "Enseignant·e : " + row["teacher"]

        ics += [
            "BEGIN:VEVENT",
            f"UID:isdat-course-{uid}@calendar",
            f"DTSTAMP:{stamp}",
            f"DTSTART;TZID=Europe/Paris:{dt_local(anchor, row['start'])}",
            f"DTEND;TZID=Europe/Paris:{dt_local(anchor, row['end'])}",
            f"SUMMARY:{esc(row['course'])}",
            "LOCATION:ISDAT",
            f"DESCRIPTION:{esc(description)}",
            f"CATEGORIES:{esc(typ.upper())}",
            f"COLOR:{COLORS[typ]}",
            f"RRULE:FREQ=WEEKLY;INTERVAL={interval};UNTIL=20270205T235959Z",
        ]

        step = timedelta(days=7 * interval)
        exdates = []
        day = anchor
        while day <= date(2027, 2, 5):
            if in_holiday(day):
                exdates.append(dt_local(day, row["start"]))
            day += step
        if exdates:
            ics.append("EXDATE;TZID=Europe/Paris:" + ",".join(exdates))

        ics.append("END:VEVENT")
        uid += 1

for title, start_date, start_time, end_date, end_time, typ, note in SCHOOL_EVENTS:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    ics += [
        "BEGIN:VEVENT",
        f"UID:isdat-school-{uid}@calendar",
        f"DTSTAMP:{stamp}",
        f"DTSTART;TZID=Europe/Paris:{dt_local(start, start_time)}",
        f"DTEND;TZID=Europe/Paris:{dt_local(end, end_time)}",
        f"SUMMARY:{esc(title)}",
        "LOCATION:ISDAT",
        f"DESCRIPTION:{esc(note)}",
        f"CATEGORIES:{esc('ÉVÉNEMENT SCOLAIRE / ' + typ.upper())}",
        f"COLOR:{COLORS[typ]}",
        "END:VEVENT",
    ]
    uid += 1

for start, end, title in HOLIDAYS:
    end_exclusive = end + timedelta(days=1)
    ics += [
        "BEGIN:VEVENT",
        f"UID:isdat-holiday-{start:%Y%m%d}@calendar",
        f"DTSTAMP:{stamp}",
        f"DTSTART;VALUE=DATE:{start:%Y%m%d}",
        f"DTEND;VALUE=DATE:{end_exclusive:%Y%m%d}",
        f"SUMMARY:{esc(title)}",
        "LOCATION:ISDAT",
        "DESCRIPTION:Vacances officielles du calendrier ISDAT 2026–2027.",
        "CATEGORIES:VACANCES",
        "COLOR:#6A8F8A",
        "END:VEVENT",
    ]

ics.append("END:VCALENDAR")

with open("ISDAT.ics", "w", encoding="utf-8", newline="") as f:
    f.write("\r\n".join(ics) + "\r\n")
