import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request


app = Flask(__name__)

PROJECTS_FILE = Path(__file__).resolve().parent / "projects.json"


def load_projects():
    with PROJECTS_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def save_projects(projects):
    with PROJECTS_FILE.open("w", encoding="utf-8") as file:
        json.dump(projects, file, indent=2)


projects_db = load_projects()


@app.route("/")
def index():
    global projects_db
    projects_db = load_projects()
    return render_template("index.html", projects=projects_db)


@app.post("/api/projects/<int:project_id>/upvote")
def upvote_project(project_id):
    global projects_db
    projects_db = load_projects()
    project = next(
        (project for project in projects_db if project["id"] == project_id),
        None,
    )
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    project["likes"] += 1
    save_projects(projects_db)
    return jsonify({"id": project["id"], "likes": project["likes"]})


@app.post("/api/projects")
def create_project():
    data = request.get_json(silent=True)
    title = data.get("title") if isinstance(data, dict) else None
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "Project title is required"}), 400

    global projects_db
    projects_db = load_projects()
    new_project = {
        "id": max((project["id"] for project in projects_db), default=0) + 1,
        "title": title.strip(),
        "description": "",
        "likes": 0,
    }
    projects_db.append(new_project)
    save_projects(projects_db)
    return jsonify(new_project), 201


if __name__ == "__main__":
    app.run(debug=True)
