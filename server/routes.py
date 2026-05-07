from flask import Flask, render_template, request, redirect, session
from datetime import date, timedelta
import uuid
import sqlite3
import os

# ================= APP =================
app = Flask(__name__)
app.secret_key = "secret123"


# ================= DATABASE =================
def get_connection(subject):

    db_folder = "databases"

    if not os.path.exists(db_folder):
        os.makedirs(db_folder)

    db_path = os.path.join(db_folder, f"{subject}.db")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    return conn


# ================= LOAD QUESTIONS =================
def load_questions(subject):

    conn = get_connection(subject)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id TEXT PRIMARY KEY,
        question TEXT,
        option1 TEXT,
        option2 TEXT,
        option3 TEXT,
        option4 TEXT,
        correct TEXT,
        interval INTEGER,
        next_date TEXT,
        last_result TEXT,
        subject TEXT
    )
    """)

    conn.commit()

    cursor.execute("SELECT * FROM questions")

    rows = cursor.fetchall()

    conn.close()

    questions = []

    for row in rows:
        questions.append(dict(row))

    return questions


# ================= SAVE QUESTIONS =================
def save_questions(user_id, questions, subject):

    conn = get_connection(subject)
    cursor = conn.cursor()

    for q in questions:

        cursor.execute("""
        UPDATE questions
        SET interval=?,
            next_date=?,
            last_result=?
        WHERE id=?
        """, (
            q["interval"],
            str(q["next_date"]),
            q.get("last_result", ""),
            q["id"]
        ))

    conn.commit()
    conn.close()


# ================= SCHEDULER =================
def get_due(questions):

    today = date.today()

    due = []

    for q in questions:

        next_date = q.get("next_date")

        if not next_date:
            due.append(q)

        else:
            try:
                q_date = date.fromisoformat(next_date)

                if q_date <= today:
                    due.append(q)

            except:
                due.append(q)

    return due


def update_interval(q, correct):

    interval = int(q.get("interval", 1))

    if correct:
        interval *= 2
    else:
        interval = 1

    q["interval"] = interval
    q["last_result"] = "correct" if correct else "wrong"


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


# ================= LOGOUT =================
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# ================= HOME =================
@app.route("/")
def home():

    if not session.get("user_id"):
        return redirect("/login")

    return render_template("subject.html")


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

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id TEXT PRIMARY KEY,
            question TEXT,
            option1 TEXT,
            option2 TEXT,
            option3 TEXT,
            option4 TEXT,
            correct TEXT,
            interval INTEGER,
            next_date TEXT,
            last_result TEXT,
            subject TEXT
        )
        """)

        q_id = subject + "_" + str(uuid.uuid4())[:8]

        cursor.execute("""
        INSERT INTO questions (
            id,
            question,
            option1,
            option2,
            option3,
            option4,
            correct,
            interval,
            next_date,
            last_result,
            subject
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

        return "Question Added Successfully"

    return render_template("admin.html")


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

    return render_template(
        "result.html",
        score=score,
        total=total
    )


# ================= RUN =================
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
