from flask import render_template, request, redirect, session
from datetime import date, timedelta
import csv
import io
import time

from server.loader import load_questions
from server.saver import save_questions
from server.scheduler import get_due, update_interval

FILE = "materia_medica.csv"
DAILY_FILE = "daily_sets.csv"


# ================= DAILY SET =================
def get_today_set(today):
    try:
        with io.open(DAILY_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0] == today:
                    ids = row[1].split(",")
                    index = int(row[2]) if len(row) > 2 else 0
                    return ids, index
    except:
        pass
    return [], 0


def save_today_set(today, ids, index):
    rows = []
    try:
        with io.open(DAILY_FILE, "r", encoding="utf-8") as f:
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

    with io.open(DAILY_FILE, "w", encoding="utf-8", newline='') as f:
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

        today = str(date.today())
        ids, saved_index = get_today_set(today)

        # Resume OR create new set
        if ids and saved_index < len(ids):
            session["index"] = saved_index
        else:
            start_time = time.time()

            questions = load_questions(FILE)
            due = get_due(questions)
            ids = [q["id"] for q in due]

            print("NEW SET LOAD TIME:", time.time() - start_time)

            save_today_set(today, ids, 0)
            session["index"] = 0

        session["today_ids"] = ids

        return render_template(
            "summary.html",
            subject="Materia Medica",
            total=len(ids)
        )


    @app.route("/mcq")
    def mcq():
        ids = session.get("today_ids", [])
        idx = session.get("index", 0)

        # ✅ SAFE CHECK
        if idx >= len(ids):
            return redirect("/result")

        start_time = time.time()

        questions = load_questions(FILE)
        id_map = {q["id"]: q for q in questions}

        q = id_map.get(ids[idx]) if idx < len(ids) else None

        print("MCQ LOAD TIME:", time.time() - start_time)

        if not q:
            session["index"] = idx + 1
            save_today_set(str(date.today()), ids, session["index"])
            return redirect("/mcq")

        return render_template(
            "index.html",
            q=q,
            attempted=idx,
            remaining=len(ids) - idx
        )


    @app.route("/answer", methods=["POST"])
    def answer():
        selected = int(request.form["answer"])
        options = ["A", "B", "C", "D"]

        ids = session.get("today_ids", [])
        idx = session.get("index", 0)

        # ✅ VERY IMPORTANT FIX
        if idx >= len(ids):
            return redirect("/result")

        start_time = time.time()

        questions = load_questions(FILE)
        id_map = {q["id"]: q for q in questions}

        q = id_map.get(ids[idx]) if idx < len(ids) else None

        print("ANSWER LOAD TIME:", time.time() - start_time)

        if not q:
            session["index"] = idx + 1
            save_today_set(str(date.today()), ids, session["index"])
            return redirect("/mcq")

        correct = (options[selected] == q["correct"])

        update_interval(q, correct)
        q["next_date"] = date.today() + timedelta(days=q["interval"])

        session["results"].append({
            "id": q["id"],
            "selected": options[selected],
            "correct": q["correct"],
            "status": "correct" if correct else "wrong"
        })

        start_time = time.time()

        save_questions(FILE, questions, "Materia Medica")

        print("SAVE TIME:", time.time() - start_time)

        session["index"] = idx + 1
        save_today_set(str(date.today()), ids, session["index"])

        return redirect("/mcq")


    @app.route("/result")
    def result():
        results = session.get("results", [])

        start_time = time.time()

        questions = load_questions(FILE)
        id_map = {q["id"]: q for q in questions}

        print("RESULT LOAD TIME:", time.time() - start_time)

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