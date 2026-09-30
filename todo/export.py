"""Export tasks to CSV."""
import csv

FIELDS = ["id", "title", "done", "priority", "due", "tag", "created"]


def to_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        for r in rows:
            writer.writerow([r[k] for k in FIELDS])
    return len(rows)
