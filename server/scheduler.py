from datetime import date


def get_due(questions, used_ids=None):
    today = date.today()

    # ✅ ensure used_ids is a set
    if used_ids is None:
        used_ids = set()

    due = []

    # 👉 collect only truly due + not already used today
    for q in questions:
        try:
            if (
                q.get("next_date")
                and q["next_date"] <= today
                and q["id"] not in used_ids   # ✅ prevent same-day repeat
            ):
                due.append(q)
        except:
            continue

    # ❌ no fallback (only due questions allowed)
    if not due:
        return []

    # 🔥 priority: wrong first
    wrong = [q for q in due if q.get("last_result") == "wrong"]
    correct = [q for q in due if q.get("last_result") != "wrong"]

    final = wrong + correct

    # ✅ limit to 120 questions per day
    return final[:120]


def update_interval(q, correct):
    # ✅ safe interval read
    try:
        interval = int(q.get("interval", 1))
    except:
        interval = 1

    if correct:
        # ✅ spaced repetition progression
        if interval == 1:
            q["interval"] = 7
        elif interval == 7:
            q["interval"] = 15
        else:
            q["interval"] = 30

        q["last_result"] = "correct"

    else:
        # ❌ wrong → repeat next day
        q["interval"] = 1
        q["last_result"] = "wrong"
