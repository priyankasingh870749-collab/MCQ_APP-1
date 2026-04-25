import csv
import io
from datetime import date
from server.utils import parse_date

def load_questions(file_name):
    questions = []

    with io.open(file_name, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        next(reader, None)

        for row in reader:
            if len(row) < 2:
                continue

            question = row[1]
            if not question.strip():
                continue

            options = row[2:6]
            while len(options) < 4:
                options.append("")

            valid = [o for o in options if o.strip()]
            if len(valid) < 2:
                continue

            try:
                interval = int(row[7]) if len(row) > 7 else 1
            except:
                interval = 1

            next_date = parse_date(row[8]) if len(row) > 8 else date.today()

            correct = "A"
            if len(row) > 6:
                c = row[6].strip().upper()
                if c in ["A","B","C","D"]:
                    correct = c

            questions.append({
                "id": str(row[0]).strip(),
                "question": question,
                "options": options,
                "correct": correct,
                "interval": interval,
                "next_date": next_date,
                "last_result": row[9] if len(row) > 9 else ""
            })

    return questions