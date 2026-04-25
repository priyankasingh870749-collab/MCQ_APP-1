import csv
import io


def save_questions(file_name, questions, subject):
    # 🔥 newline='' fixes blank row issue
    with io.open(file_name, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)

        # header
        writer.writerow([
            "id", "question", "option1", "option2",
            "option3", "option4", "correct",
            "interval", "next_date", "last_result", "subject"
        ])

        # data rows
        for q in questions:
            writer.writerow([
                q.get("id", ""),
                q.get("question", ""),
                q.get("options", ["", "", "", ""])[0],
                q.get("options", ["", "", "", ""])[1],
                q.get("options", ["", "", "", ""])[2],
                q.get("options", ["", "", "", ""])[3],
                q.get("correct", ""),
                q.get("interval", 1),
                q.get("next_date").strftime("%m/%d/%Y") if q.get("next_date") else "",
                q.get("last_result", ""),
                subject
            ])