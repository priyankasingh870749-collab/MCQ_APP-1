from datetime import date

def get_due(questions):
    today = date.today()

    due = []

    # 👉 collect only truly due questions (no early repetition)
    for q in questions:
        try:
            if q.get("next_date") and q["next_date"] <= today:
                due.append(q)
        except:
            continue

    # ❌ removed fallback → no early questions
    if not due:
        return []

    # 🔥 better learning: wrong first
    wrong = [q for q in due if q.get("last_result") == "wrong"]
    correct = [q for q in due if q.get("last_result") != "wrong"]

    final = wrong + correct

    return final[:120]


def update_interval(q, correct):
    # SAFE interval handling
    try:
        interval = int(q.get("interval", 1))
    except:
        interval = 1

    if correct:
        if interval == 1:
            q["interval"] = 7
        elif interval == 7:
            q["interval"] = 15
        else:
            q["interval"] = 30

        q["last_result"] = "correct"

    else:
        q["interval"] = 1
        q["last_result"] = "wrong"