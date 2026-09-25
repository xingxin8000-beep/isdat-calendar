import csv
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

TZ = "Europe/Paris"
OUT_MAIN = "ISDAT_Courses.ics"
OUT_ATELIER = "ISDAT_Atelier_Recherches.ics"

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
    return (str(value).replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def dt(day, time_text):
    return f"{day:%Y%m%d}T{time_text.replace(':', '')}00"


def in_holiday(day):
    return any(start <= day <= end for start, end, _ in HOLIDAYS)


def header(name):
    return [
        "BEGIN:VCALENDAR", "VERSION:2.0",
        "PRODID:-//ISDAT//L2 Design graphique 2026-2027//FR",
        "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
        f"X-WR-CALNAME:{name}", f"X-WR-TIMEZONE:{TZ}",
        "REFRESH-INTERVAL;VALUE=DURATION:P1D", "X-PUBLISHED-TTL:P1D",
    ]


def add_course(ics, row, uid, stamp):
    anchor = datetime.strptime(row["anchor_date"], "%Y-%m-%d").date()
    repeat = row["repeat"].strip().lower()
    interval = 1 if repeat == "weekly" else 2
    teacher = row["teacher"].strip()
    description = f"Enseignant·e : {teacher}" if teacher else ""
    summary = row["course"]
    day = anchor
    occurrence = 0
    while day <= date(2027, 2, 5):
        if not in_holiday(day):
            suffix = f"-{day:%Y%m%d}"
            ics.extend([
                "BEGIN:VEVENT",
                f"UID:isdat-course-{uid}{suffix}@calendar",
                f"DTSTAMP:{stamp}",
                f"DTSTART;TZID={TZ}:{dt(day, row['start'])}",
                f"DTEND;TZID={TZ}:{dt(day, row['end'])}",
                f"SUMMARY:{esc(summary)}", "LOCATION:ISDAT",
                f"DESCRIPTION:{esc(description)}",
                f"CATEGORIES:{esc(row['type'].upper())}",
                "END:VEVENT",
            ])
            occurrence += 1
        day += timedelta(days=7 * interval)


def add_school_event(ics, item, uid, stamp):
    title, sd, st, ed, et, typ, note = item
    ics.extend([
        "BEGIN:VEVENT", f"UID:isdat-school-{uid}@calendar", f"DTSTAMP:{stamp}",
        f"DTSTART;TZID={TZ}:{dt(date.fromisoformat(sd), st)}",
        f"DTEND;TZID={TZ}:{dt(date.fromisoformat(ed), et)}",
        f"SUMMARY:{esc(title)}", "LOCATION:ISDAT",
        f"DESCRIPTION:{esc(note)}",
        f"CATEGORIES:{esc('ÉVÉNÉMENT SCOLAIRE / ' + typ.upper())}",
        "END:VEVENT",
    ])


def add_holiday(ics, item, uid, stamp):
    start, end, title = item
    ics.extend([
        "BEGIN:VEVENT", f"UID:isdat-holiday-{start:%Y%m%d}@calendar", f"DTSTAMP:{stamp}",
        f"DTSTART;VALUE=DATE:{start:%Y%m%d}",
        f"DTEND;VALUE=DATE:{(end + timedelta(days=1)):%Y%m%d}",
        f"SUMMARY:{esc(title)}", "LOCATION:ISDAT",
        "DESCRIPTION:Vacances officielles du calendrier ISDAT 2026–2027.",
        "CATEGORIES:VACANCES", "END:VEVENT",
    ])


def build():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rows = list(csv.DictReader(open("courses.csv", encoding="utf-8-sig", newline="")))
    atelier_name = "ISDAT — Atelier / Recherches"
    main_name = "ISDAT L2 Design graphique — Cours"
    main, atelier = header(main_name), header(atelier_name)
    uid = 1
    for row in rows:
        if row["course"].strip() == "Travail en atelier / Recherches":
            # atelier calendar: same recurrence, separate subscription color
            add_course(atelier, row, uid, stamp)
        else:
            add_course(main, row, uid, stamp)
        uid += 1
    for item in SCHOOL_EVENTS:
        add_school_event(main, item, uid, stamp); uid += 1
    for item in HOLIDAYS:
        add_holiday(main, item, uid, stamp); uid += 1
    main.append("END:VCALENDAR")
    atelier.append("END:VCALENDAR")
    Path(OUT_MAIN).write_text("\r\n".join(main) + "\r\n", encoding="utf-8")
    Path(OUT_ATELIER).write_text("\r\n".join(atelier) + "\r\n", encoding="utf-8")


if __name__ == "__main__":
    build()
