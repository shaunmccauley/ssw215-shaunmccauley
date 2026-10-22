import json
from pathlib import Path

from flask import Flask, jsonify, render_template


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


if __name__ == "__main__":
    app.run(debug=True)
