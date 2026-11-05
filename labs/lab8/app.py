import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{(Path(app.instance_path) / 'portfolio.db').as_posix()}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
SEED_FILE = Path(__file__).resolve().parent / "projects_seed.json"


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.String(500), nullable=False, default="")
    likes = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "likes": self.likes,
        }


def init_seed_data():
    if db.session.query(Project).count() != 0:
        return

    with SEED_FILE.open(encoding="utf-8") as file:
        seed_projects = json.load(file)

    db.session.add_all(
        Project(
            id=project["id"],
            title=project["title"],
            description=project.get("description", ""),
            likes=project.get("likes", 0),
        )
        for project in seed_projects
    )
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise


Path(app.instance_path).mkdir(parents=True, exist_ok=True)
with app.app_context():
    db.create_all()
    init_seed_data()


@app.route("/")
def index():
    projects = db.session.query(Project).order_by(Project.id).all()
    return render_template("index.html", projects=projects)


@app.get("/api/projects")
def get_projects():
    projects = db.session.query(Project).order_by(Project.id).all()
    return jsonify([project.to_dict() for project in projects])


@app.post("/api/projects/<int:project_id>/upvote")
def upvote_project(project_id):
    project = db.session.get(Project, project_id)
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    project.likes += 1
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Unable to save project"}), 400

    return jsonify({"id": project.id, "likes": project.likes})


@app.post("/api/projects")
def create_project():
    data = request.get_json(silent=True)
    title = data.get("title") if isinstance(data, dict) else None
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "Project title is required"}), 400

    project = Project(title=title.strip(), description="", likes=0)
    db.session.add(project)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A project with that title already exists"}), 400
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Unable to save project"}), 400

    return jsonify(project.to_dict()), 201


if __name__ == "__main__":
    app.run(debug=True)
