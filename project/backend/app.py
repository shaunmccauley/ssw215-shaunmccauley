import os
import json
from datetime import datetime, timezone

from flask import Flask, send_from_directory


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
DATA_FILE = os.path.join(BASE_DIR, "data.json")
SEED_FILE = os.path.join(BASE_DIR, "seed_data.json")
EDITABLE_FIELDS = (
    "problem_name",
    "source",
    "topic",
    "difficulty",
    "result",
    "time_minutes",
    "approach",
    "struggles",
)

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_entries():
    if not os.path.exists(DATA_FILE):
        with open(SEED_FILE, "r", encoding="utf-8") as seed_file:
            entries = json.load(seed_file)
        _save_entries(entries)
        return entries

    with open(DATA_FILE, "r", encoding="utf-8") as data_file:
        return json.load(data_file)


def _save_entries(entries):
    with open(DATA_FILE, "w", encoding="utf-8") as data_file:
        json.dump(entries, data_file, indent=2)


def get_all_entries():
    return _load_entries()


def get_entry(entry_id):
    for entry in _load_entries():
        if entry.get("id") == entry_id:
            return entry
    return None


def create_entry(data):
    entries = _load_entries()
    next_id = max((entry.get("id", 0) for entry in entries), default=0) + 1
    entry = {field: data.get(field, "") for field in EDITABLE_FIELDS}
    entry["id"] = next_id
    entry["ai_review"] = None
    entry["created_at"] = now_iso()
    entries.append(entry)
    _save_entries(entries)
    return entry


def update_entry(entry_id, data):
    entries = _load_entries()
    for entry in entries:
        if entry.get("id") == entry_id:
            for field in EDITABLE_FIELDS:
                entry[field] = data.get(field, "")
            _save_entries(entries)
            return entry
    return None


def delete_entry(entry_id):
    entries = _load_entries()
    for index, entry in enumerate(entries):
        if entry.get("id") == entry_id:
            del entries[index]
            _save_entries(entries)
            return True
    return False


def save_review(entry_id, review):
    entries = _load_entries()
    for entry in entries:
        if entry.get("id") == entry_id:
            entry["ai_review"] = review
            _save_entries(entries)
            return entry
    return None


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=False)
