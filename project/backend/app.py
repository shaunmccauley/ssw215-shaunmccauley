import os
import json
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException


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


@app.errorhandler(Exception)
def handle_exception(error):
    if isinstance(error, HTTPException):
        return jsonify({"error": error.description}), error.code

    app.logger.exception("Unhandled exception")
    return jsonify({"error": "Internal server error."}), 500


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/api/entries")
def list_entries():
    return jsonify(get_all_entries()), 200


@app.get("/api/entries/<int:entry_id>")
def read_entry(entry_id):
    entry = get_entry(entry_id)
    if entry is None:
        return jsonify({"error": "Entry not found."}), 404
    return jsonify(entry), 200


@app.post("/api/entries")
def add_entry():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    cleaned, errors = validate_entry(payload)
    if errors:
        return jsonify({"error": "Validation failed.", "fields": errors}), 400

    return jsonify(create_entry(cleaned)), 201


@app.put("/api/entries/<int:entry_id>")
def edit_entry(entry_id):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    cleaned, errors = validate_entry(payload)
    if errors:
        return jsonify({"error": "Validation failed.", "fields": errors}), 400

    entry = update_entry(entry_id, cleaned)
    if entry is None:
        return jsonify({"error": "Entry not found."}), 404
    return jsonify(entry), 200


@app.delete("/api/entries/<int:entry_id>")
def remove_entry(entry_id):
    if not delete_entry(entry_id):
        return jsonify({"error": "Entry not found."}), 404
    return "", 204


@app.post("/api/entries/<int:entry_id>/review")
def review_entry(entry_id):
    entry = get_entry(entry_id)
    if entry is None:
        return jsonify({"error": "Entry not found."}), 404
    approach = entry.get("approach", "")
    if not isinstance(approach, str) or not approach.strip():
        return jsonify({"error": "Add approach text to enable AI review."}), 400

    review = build_canned_review(entry)
    return jsonify(save_review(entry_id, review)), 200


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_entry(payload):
    payload = payload if isinstance(payload, dict) else {}
    cleaned = {}
    errors = {}
    allowed_sources = ("LeetCode", "HackerRank", "NeetCode", "Other")
    allowed_difficulties = ("Easy", "Medium", "Hard")
    allowed_results = ("Solved", "Partial", "Failed")

    problem_name = payload.get("problem_name")
    if not isinstance(problem_name, str):
        errors["problem_name"] = "Problem name must be a string."
        cleaned["problem_name"] = ""
    else:
        cleaned["problem_name"] = problem_name.strip()
        if not cleaned["problem_name"]:
            errors["problem_name"] = "Problem name is required."
        elif len(cleaned["problem_name"]) > 100:
            errors["problem_name"] = (
                "Problem name must be 100 characters or fewer."
            )

    for field, allowed, label in (
        ("source", allowed_sources, "Source"),
        ("difficulty", allowed_difficulties, "Difficulty"),
        ("result", allowed_results, "Result"),
    ):
        value = payload.get(field)
        if not isinstance(value, str):
            errors[field] = f"{label} must be a string."
            cleaned[field] = ""
        else:
            cleaned[field] = value.strip()
            if cleaned[field] not in allowed:
                errors[field] = (
                    f"{label} must be one of: {', '.join(allowed)}."
                )

    time_minutes = payload.get("time_minutes")
    if (
        isinstance(time_minutes, bool)
        or not isinstance(time_minutes, int)
        or not 1 <= time_minutes <= 600
    ):
        errors["time_minutes"] = "Time must be a whole number from 1 to 600."
        cleaned["time_minutes"] = None
    else:
        cleaned["time_minutes"] = time_minutes

    for field in ("topic", "approach", "struggles"):
        value = payload.get(field, "")
        if not isinstance(value, str):
            errors[field] = f"{field.replace('_', ' ').capitalize()} must be a string."
            cleaned[field] = ""
        else:
            cleaned[field] = value.strip()

    return cleaned, errors


def build_canned_review(entry):
    problem_name = entry.get("problem_name", "")
    return {
        "key_concept": (
            f"The central pattern in {problem_name} is to break the problem "
            "into smaller, testable decisions."
        ),
        "knowledge_gap": (
            "Connect the chosen data structure to the operation that must stay "
            "efficient."
        ),
        "takeaway": (
            "State the invariant before coding, then use it to guide each "
            "implementation step."
        ),
        "area_for_review": (
            "Time complexity, edge cases, and the tradeoffs of alternative "
            "approaches."
        ),
    }


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
