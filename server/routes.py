from flask import render_template, request, redirect, session
from datetime import date, timedelta
import csv
import io
import time
import os
import shutil

from server.loader import load_questions
from server.saver import save_questions
from server.scheduler import get_due, update_interval


# ================= SUBJECT FILE MAP =================
SUBJECT_FILES = {
    "materia": "materia_medica.csv",
    "repertory": "repertory.csv",
    "organon": "organon.csv"
}

DATA_PATH = "data"

if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)


def get_file_path(filename):
    return os.path.join(DATA_PATH, filename)


def ensure_file(filename):
    src = filename
    dst = get_file_path(filename)

    if not os.path.exists(dst):
        if os.path.exists(src):
            shutil.copy(src, dst)

    return dst


# ================= DAILY SET =================
def get_today_set(today, daily_file):
    try:
        with io.open(daily_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0] == today:
                    ids = row[1].split(",")
                    index = int(row[2]) if len(row) > 2 else 0
                    return ids, index
    except:
        pass
    return [], 0


def save_today_set(today, ids, index, daily_file):
    rows = []
    try:
        with io.open(daily_file, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
    except:
        pass

    updated = False

    for i in range(len(rows)):
        if rows[i] and rows[i][0] == today:
            rows[i] = [today, ",".join(ids), str(index)]
            updated = True

    if not updated:
        rows.append([today, ",".join(ids), str(index)])

    with io.open(daily_file, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)


# ================= ROUTES =================
def register_routes(app):

    @app.route("/")
    def home():
        return render_template("subject.html")


    @app.route("/start", methods=["POST"])
    def start():
        session["results"] = []

        subject = request.form.get("subject")
        session["subject"] = subject

        filename = SUBJECT_FILES.get(subject, "materia_medica.csv")
        FILE = ensure_file(filename)

        DAILY_FILE = get_file_path("daily_sets.csv")

        today = str(date.today())
        ids, saved_index = get_today_set(today, DAILY_FILE)

        if ids and saved_index < len(ids):
            session["index"] = saved_index
        else:
            questions = load_questions(FILE)
            due = get_due(questions)
            ids = [q["id"] for q in due]

            save_today_set(today, ids, 0, DAILY_FILE)
            session["index"] = 0

        session["today_ids"] = ids

        return render_template(
            "summary.html",
            subject=subject,
            total=len(ids)
        )


    @app.route("/mcq")
    def mcq():
        subject = session.get("subject", "materia")
        filename = SUBJECT_FILES.get(subject, "materia_medica.csv")
        FILE = ensure_file(filename)

        DAILY_FILE = get_file_path("daily_sets.csv")

        ids = session.get("today_ids", [])
        idx = session.get("index", 0)

        if idx >= len(ids):
            return redirect("/result")

        questions = load_questions(FILE)
        id_map = {q["id"]: q for q in questions}

        q = id_map.get(ids[idx]) if idx < len(ids) else None

        if not q:
            session["index"] = idx + 1
            save_today_set(str(date.today()), ids, session["index"], DAILY_FILE)
            return redirect("/mcq")

        return render_template(
            "index.html",
            q=q,
            attempted=idx,
            remaining=len(ids) - idx
        )


    @app.route("/answer", methods=["POST"])
    def answer():
        subject = session.get("subject", "materia")
        filename = SUBJECT_FILES.get(subject, "materia_medica.csv")
        FILE = ensure_file(filename)

        DAILY_FILE = get_file_path("daily_sets.csv")

        # ✅ SAFE INPUT
        answer_val = request.form.get("answer")
        if answer_val is None:
            return redirect("/mcq")

        try:
            selected = int(answer_val)
        except:
            return redirect("/mcq")

        options = ["A", "B", "C", "D"]

        ids = session.get("today_ids", [])
        idx = session.get("index", 0)

        if idx >= len(ids):
            return redirect("/result")

        questions = load_questions(FILE)
        id_map = {q["id"]: q for q in questions}

        q = id_map.get(ids[idx]) if idx < len(ids) else None

        if not q:
            session["index"] = idx + 1
            save_today_set(str(date.today()), ids, session["index"], DAILY_FILE)
            return redirect("/mcq")

        correct = (options[selected] == q["correct"])

        update_interval(q, correct)

        # ✅ SAFE interval
        try:
            interval = int(q.get("interval", 1))
        except:
            interval = 1

        q["next_date"] = date.today() + timedelta(days=interval)

        session["results"].append({
            "id": q["id"],
            "selected": options[selected],
            "correct": q["correct"],
            "status": "correct" if correct else "wrong"
        })

        # ✅ SAFE SAVE
        try:
            save_questions(FILE, questions, subject)
        except Exception as e:
            print("SAVE ERROR:", e)

        session["index"] = idx + 1
        save_today_set(str(date.today()), ids, session["index"], DAILY_FILE)

        return redirect("/mcq")


    @app.route("/result")
    def result():
        subject = session.get("subject", "materia")
        filename = SUBJECT_FILES.get(subject, "materia_medica.csv")
        FILE = ensure_file(filename)

        results = session.get("results", [])

        questions = load_questions(FILE)
        id_map = {q["id"]: q for q in questions}

        wrong_list = []

        for r in results:
            if r["status"] == "wrong":
                q = id_map.get(r["id"])
                if q:
                    wrong_list.append({
                        "question": q["question"],
                        "options": q["options"],
                        "selected": r["selected"],
                        "correct": r["correct"]
                    })

        total = len(results)
        score = len([r for r in results if r["status"] == "correct"])

        return render_template(
            "result.html",
            total=total,
            score=score,
            wrong=wrong_list
        )
