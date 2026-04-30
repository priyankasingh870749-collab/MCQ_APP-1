import csv
import io
import os
import tempfile


def save_questions(file_name, questions, subject):
    # 🔒 ensure directory exists
    os.makedirs(os.path.dirname(file_name), exist_ok=True)

    # 🔥 safe write using temp file (prevents corruption)
    temp_fd, temp_path = tempfile.mkstemp()

    try:
        with io.open(temp_path, "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)

            # header
            writer.writerow([
                "id", "question", "option1", "option2",
                "option3", "option4", "correct",
                "interval", "next_date", "last_result", "subject"
            ])

            # data rows
            for q in questions:
                options = q.get("options", ["", "", "", ""])
                while len(options) < 4:
                    options.append("")

                writer.writerow([
                    q.get("id", ""),
                    q.get("question", ""),
                    options[0],
                    options[1],
                    options[2],
                    options[3],
                    q.get("correct", ""),
                    q.get("interval", 1),
                    q.get("next_date").strftime("%m/%d/%Y") if q.get("next_date") else "",
                    q.get("last_result", ""),
                    subject
                ])

        # 🔁 replace original file atomically
        os.replace(temp_path, file_name)

    finally:
        try:
            os.close(temp_fd)
        except:
            pass

        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
