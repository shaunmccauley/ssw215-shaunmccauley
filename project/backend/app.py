import os
import json
import sqlite3
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
DB_FILE = os.path.join(BASE_DIR, "reflections.db")
SCHEMA_FILE = os.path.join(BASE_DIR, "schema.sql")
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


def get_db():
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with open(SCHEMA_FILE, "r", encoding="utf-8") as schema_file:
        schema = schema_file.read()

    connection = get_db()
    try:
        connection.executescript(schema)
        connection.commit()
    finally:
        connection.close()


def _row_to_entry(row):
    entry = dict(row)
    entry["ai_review"] = json.loads(row["ai_review"]) if row["ai_review"] else None
    return entry


def get_all_entries():
    connection = get_db()
    try:
        rows = connection.execute(
            "SELECT id, problem_name, source, topic, difficulty, result, "
            "time_minutes, approach, struggles, ai_review, created_at "
            "FROM entries ORDER BY id"
        ).fetchall()
        return [_row_to_entry(row) for row in rows]
    finally:
        connection.close()


def get_entry(entry_id):
    connection = get_db()
    try:
        row = connection.execute(
            "SELECT id, problem_name, source, topic, difficulty, result, "
            "time_minutes, approach, struggles, ai_review, created_at "
            "FROM entries WHERE id = ?",
            (entry_id,),
        ).fetchone()
        return _row_to_entry(row) if row is not None else None
    finally:
        connection.close()


def create_entry(data):
    connection = get_db()
    try:
        cursor = connection.execute(
            "INSERT INTO entries "
            "(problem_name, source, topic, difficulty, result, time_minutes, "
            "approach, struggles, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                data.get("problem_name", ""),
                data.get("source", ""),
                data.get("topic", ""),
                data.get("difficulty", ""),
                data.get("result", ""),
                data.get("time_minutes"),
                data.get("approach", ""),
                data.get("struggles", ""),
                now_iso(),
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT id, problem_name, source, topic, difficulty, result, "
            "time_minutes, approach, struggles, ai_review, created_at "
            "FROM entries WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return _row_to_entry(row)
    finally:
        connection.close()


def update_entry(entry_id, data):
    connection = get_db()
    try:
        cursor = connection.execute(
            "UPDATE entries SET problem_name = ?, source = ?, topic = ?, "
            "difficulty = ?, result = ?, time_minutes = ?, approach = ?, "
            "struggles = ? WHERE id = ?",
            (
                data.get("problem_name", ""),
                data.get("source", ""),
                data.get("topic", ""),
                data.get("difficulty", ""),
                data.get("result", ""),
                data.get("time_minutes"),
                data.get("approach", ""),
                data.get("struggles", ""),
                entry_id,
            ),
        )
        if cursor.rowcount == 0:
            return None

        connection.commit()
        row = connection.execute(
            "SELECT id, problem_name, source, topic, difficulty, result, "
            "time_minutes, approach, struggles, ai_review, created_at "
            "FROM entries WHERE id = ?",
            (entry_id,),
        ).fetchone()
        return _row_to_entry(row)
    finally:
        connection.close()


def delete_entry(entry_id):
    connection = get_db()
    try:
        cursor = connection.execute(
            "DELETE FROM entries WHERE id = ?",
            (entry_id,),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def save_review(entry_id, review):
    connection = get_db()
    try:
        cursor = connection.execute(
            "UPDATE entries SET ai_review = ? WHERE id = ?",
            (json.dumps(review), entry_id),
        )
        if cursor.rowcount == 0:
            return None

        connection.commit()
        row = connection.execute(
            "SELECT id, problem_name, source, topic, difficulty, result, "
            "time_minutes, approach, struggles, ai_review, created_at "
            "FROM entries WHERE id = ?",
            (entry_id,),
        ).fetchone()
        return _row_to_entry(row)
    finally:
        connection.close()


if __name__ == "__main__":
    init_db()
    app.run(host="localhost", port=5000, debug=False)
