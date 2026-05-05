from flask import render_template, request, redirect, session
from datetime import date, timedelta
import uuid
import shutil
import os

from server.loader import load_questions
from server.saver import save_questions
from server.scheduler import get_due, update_interval
from server.db import get_connection


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        users = {
            "admin": "123",
            "user1": "111",
            "user2": "222"
        }

        if username in users and users[username] == password:
            session["user_id"] = username
            return redirect("/")

        return "Invalid Login"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= ADMIN =================
@app.route("/admin", methods=["GET", "POST"])
def admin():

    if session.get("user_id") != "admin":
        return "Access Denied"

    if request.method == "POST":

        subject = request.form.get("subject")
        question = request.form.get("question")
        option1 = request.form.get("option1")
        option2 = request.form.get("option2")
        option3 = request.form.get("option3")
        option4 = request.form.get("option4")
        correct = request.form.get("correct")

        conn = get_connection(subject)
        cursor = conn.cursor()

        q_id = subject + "_" + str(uuid.uuid4())[:8]

        cursor.execute("""
        INSERT INTO questions (
            id, question, option1, option2, option3, option4,
            correct, interval, next_date, last_result, subject
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            q_id,
            question,
            option1,
            option2,
            option3,
            option4,
            correct,
            1,
            "",
            "",
            subject
        ))

        conn.commit()
        conn.close()

        return "Question Added"

    return render_template("admin.html")


# ================= HOME =================
@app.route("/")
def home():

    if not session.get("user_id"):
        return redirect("/login")

    return render_template("subject.html")


# ================= START =================
@app.route("/start", methods=["POST"])
def start():

    if not session.get("user_id"):
        return redirect("/login")

    session["results"] = []

    subject = request.form.get("subject")
    subject = str(subject).strip().lower().replace(" ", "_")

    session["subject"] = subject

    questions = load_questions(subject)

    if not questions:
        return "No questions found"

    due = get_due(questions)

    if not due:
        return "No due questions available"

    session["today_ids"] = [q["id"] for q in due]
    session["index"] = 0

    return redirect("/mcq")


# ================= MCQ =================
@app.route("/mcq")
def mcq():

    if not session.get("user_id"):
        return redirect("/login")

    subject = session.get("subject")
    ids = session.get("today_ids", [])
    idx = session.get("index", 0)

    if idx >= len(ids):
        return redirect("/result")

    questions = load_questions(subject)
    id_map = {q["id"]: q for q in questions}

    q = id_map.get(ids[idx])

    if not q:
        session["index"] = idx + 1
        return redirect("/mcq")

    return render_template("index.html", q=q)


# ================= ANSWER =================
@app.route("/answer", methods=["POST"])
def answer():

    if not session.get("user_id"):
        return redirect("/login")

    subject = session.get("subject")
    user_id = session.get("user_id")

    selected = int(request.form.get("answer"))

    options = ["A", "B", "C", "D"]

    ids = session.get("today_ids", [])
    idx = session.get("index", 0)

    questions = load_questions(subject)
    id_map = {q["id"]: q for q in questions}

    q = id_map.get(ids[idx])

    correct = (options[selected] == q["correct"])

    update_interval(q, correct)

    interval = int(q.get("interval", 1))
    q["next_date"] = date.today() + timedelta(days=interval)

    session["results"].append({
        "id": q["id"],
        "status": "correct" if correct else "wrong"
    })

    # SAVE USER PROGRESS
    save_questions(user_id, [q], subject)

    session["index"] = idx + 1

    return redirect("/mcq")


# ================= RESULT =================
@app.route("/result")
def result():

    if not session.get("user_id"):
        return redirect("/login")

    results = session.get("results", [])

    score = len([r for r in results if r["status"] == "correct"])
    total = len(results)

    return render_template("result.html", score=score, total=total)
