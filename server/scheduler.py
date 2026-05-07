from datetime import date


def get_due(questions, used_ids=None):

    today = date.today()

    # ensure used_ids is a set
    if used_ids is None:
        used_ids = set()
    else:
        used_ids = set(used_ids)

    due = []

    # collect only due + not already used today
    for q in questions:

        try:
            next_date = q.get("next_date")

            # if empty date -> show question
            if not next_date:

                if str(q.get("id")) not in used_ids:
                    due.append(q)

                continue

            # convert string to date
            if isinstance(next_date, str):
                next_date = date.fromisoformat(next_date)

            # due today or older
            if (
                next_date <= today
                and str(q.get("id")) not in used_ids
            ):
                due.append(q)

        except Exception:
            continue

    # no due questions
    if not due:
        return []

    # wrong answers first
    wrong = []
    correct = []

    for q in due:

        if q.get("last_result") == "wrong":
            wrong.append(q)
        else:
            correct.append(q)

    final = wrong + correct

    # max 120 per day
    return final[:120]


def update_interval(q, correct):

    # safe interval read
    try:
        interval = int(q.get("interval", 1))
    except Exception:
        interval = 1

    if correct:

        # spaced repetition logic
        if interval <= 1:
            q["interval"] = 7

        elif interval <= 7:
            q["interval"] = 15

        else:
            q["interval"] = 30

        q["last_result"] = "correct"

    else:

        # wrong → repeat tomorrow
        q["interval"] = 1
        q["last_result"] = "wrong"
