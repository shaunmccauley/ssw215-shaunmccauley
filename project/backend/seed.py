import json
import os

from app import get_db, init_db


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_FILE = os.path.join(BASE_DIR, "seed_data.json")


def seed_database():
    init_db()

    with open(SEED_FILE, "r", encoding="utf-8") as seed_file:
        entries = json.load(seed_file)

    connection = get_db()
    try:
        row = connection.execute("SELECT COUNT(*) AS count FROM entries").fetchone()
        if row["count"] > 0:
            print("Entries table already contains rows; nothing inserted.")
            return

        for entry in entries:
            ai_review = (
                json.dumps(entry["ai_review"])
                if entry.get("ai_review") is not None
                else None
            )
            connection.execute(
                "INSERT INTO entries "
                "(id, problem_name, source, topic, difficulty, result, "
                "time_minutes, approach, struggles, ai_review, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    entry["id"],
                    entry["problem_name"],
                    entry["source"],
                    entry["topic"],
                    entry["difficulty"],
                    entry["result"],
                    entry["time_minutes"],
                    entry["approach"],
                    entry["struggles"],
                    ai_review,
                    entry["created_at"],
                ),
            )

        connection.commit()
        print(f"Inserted {len(entries)} seed entries.")
    finally:
        connection.close()


if __name__ == "__main__":
    seed_database()
