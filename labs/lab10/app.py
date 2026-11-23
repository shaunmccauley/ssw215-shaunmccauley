import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import inspect, text

from ai_service import (
    AIProviderError,
    AIRefusalError,
    draft_github_project,
    extract_project_details,
    get_github_draft,
    refine_github_project_blind,
    refine_github_project,
)
from github_service import (
    GitHubReadmeTooShortError,
    GitHubRepositoryError,
    GitHubRepositoryNotFoundError,
    fetch_repository_readme,
)


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{(Path(app.instance_path) / 'portfolio.db').as_posix()}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
SEED_FILE = Path(__file__).resolve().parent / "projects_seed.json"


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.String(500), nullable=False, default="")
    summary = db.Column(db.String(1000), nullable=False, default="")
    technologies = db.Column(db.String(500), nullable=False, default="")
    difficulty = db.Column(db.String(20), nullable=False, default="")
    likes = db.Column(db.Integer, nullable=False, default=0)
    author_id = db.Column(
        db.Integer, db.ForeignKey("authors.id"), nullable=False
    )

    def to_dict(self):
        technology_list = [
            item.strip()
            for item in self.technologies.split(",")
            if item.strip()
        ] if self.technologies else []
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "summary": self.summary or self.description,
            "technologies": technology_list,
            "difficulty": self.difficulty or "",
            "likes": self.likes,
            "author": self.author.name,
        }


class Author(db.Model):
    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    projects = db.relationship("Project", backref="author")


def init_seed_data():
    if db.session.query(Project).count() != 0:
        return

    with SEED_FILE.open(encoding="utf-8") as file:
        seed_projects = json.load(file)

    author = Author(name="Shaun McCauley")
    db.session.add(author)
    db.session.flush()
    db.session.add_all(
        Project(
            id=project["id"],
            title=project["title"],
            description=project.get("description", ""),
            summary=project.get("description", ""),
            technologies="",
            likes=project.get("likes", 0),
            author_id=author.id,
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
    table_columns = {
        column["name"] for column in inspect(db.engine).get_columns("projects")
    }
    if "summary" not in table_columns:
        db.session.execute(text(
            "ALTER TABLE projects ADD COLUMN summary VARCHAR(1000) "
            "NOT NULL DEFAULT ''"
        ))
        db.session.commit()
    if "technologies" not in table_columns:
        db.session.execute(text(
            "ALTER TABLE projects ADD COLUMN technologies VARCHAR(500) "
            "NOT NULL DEFAULT ''"
        ))
        db.session.commit()
    if "difficulty" not in table_columns:
        db.session.execute(text(
            "ALTER TABLE projects ADD COLUMN difficulty VARCHAR(20) "
            "NOT NULL DEFAULT ''"
        ))
        db.session.commit()
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

    author = db.session.query(Author).first()
    if author is None:
        return jsonify({"error": "Project author is unavailable"}), 400

    project = Project(
        title=title.strip(),
        description="",
        likes=0,
        author_id=author.id,
    )
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


@app.post("/api/projects/smart")
def create_smart_project():
    data = request.get_json(silent=True)
    notes = data.get("notes") if isinstance(data, dict) else None
    if not isinstance(notes, str) or len(notes.strip()) < 20:
        return jsonify({"error": "Notes must be at least 20 characters"}), 400

    try:
        extracted = extract_project_details(notes.strip())
    except AIRefusalError:
        return jsonify({"error": "The AI provider refused the request"}), 422
    except AIProviderError:
        return jsonify({"error": "The AI provider could not be reached"}), 503

    author = db.session.query(Author).first()
    if author is None:
        return jsonify({"error": "Project author is unavailable"}), 400

    title = extracted.title.strip()
    if not title:
        return jsonify({"error": "The extracted project title is required"}), 400

    summary = extracted.summary.strip()
    technologies = ", ".join(
        technology.strip()
        for technology in extracted.technologies
        if technology.strip()
    )
    project = Project(
        title=title,
        description=summary,
        summary=summary,
        technologies=technologies,
        likes=0,
        author_id=author.id,
    )
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


@app.post("/api/projects/git-start")
def git_start_project():
    data = request.get_json(silent=True)
    owner = data.get("owner") if isinstance(data, dict) else None
    repo = data.get("repo") if isinstance(data, dict) else None
    if not isinstance(owner, str) or not owner.strip():
        return jsonify({"error": "Repository owner is required"}), 400
    if not isinstance(repo, str) or not repo.strip():
        return jsonify({"error": "Repository name is required"}), 400

    try:
        readme = fetch_repository_readme(owner, repo)
    except GitHubRepositoryNotFoundError:
        return jsonify({"error": "Repository or README not found"}), 404
    except GitHubReadmeTooShortError:
        return jsonify({"error": "README is shorter than 20 characters"}), 400
    except GitHubRepositoryError:
        return jsonify({"error": "GitHub could not be reached"}), 503

    try:
        session_id, draft = draft_github_project(readme)
    except AIRefusalError:
        return jsonify({"error": "The AI provider refused the request"}), 422
    except AIProviderError:
        return jsonify({"error": "The AI provider could not be reached"}), 503

    return jsonify({"session_id": session_id, "draft": draft}), 201


@app.post("/api/projects/git-refine")
def git_refine_project():
    data = request.get_json(silent=True)
    session_id = data.get("session_id") if isinstance(data, dict) else None
    feedback = data.get("feedback") if isinstance(data, dict) else None

    if not isinstance(session_id, str):
        return jsonify({"error": "Session not found"}), 404
    try:
        draft = refine_github_project(session_id, str(feedback or "").strip())
    except KeyError:
        return jsonify({"error": "Session not found"}), 404
    except AIRefusalError:
        return jsonify({"error": "The AI provider refused the request"}), 422
    except AIProviderError:
        return jsonify({"error": "The AI provider could not be reached"}), 503

    return jsonify(draft), 200


@app.post("/api/projects/git-refine-blind")
def git_refine_blind_project():
    data = request.get_json(silent=True)
    session_id = data.get("session_id") if isinstance(data, dict) else None
    feedback = data.get("feedback") if isinstance(data, dict) else None

    if not isinstance(session_id, str):
        return jsonify({"error": "Session not found"}), 404
    try:
        draft = refine_github_project_blind(
            session_id, str(feedback or "").strip()
        )
    except KeyError:
        return jsonify({"error": "Session not found"}), 404
    except AIRefusalError:
        return jsonify({"error": "The AI provider refused the request"}), 422
    except AIProviderError:
        return jsonify({"error": "The AI provider could not be reached"}), 503

    return jsonify(draft), 200


@app.post("/api/projects/git-commit")
def git_commit_project():
    data = request.get_json(silent=True)
    session_id = data.get("session_id") if isinstance(data, dict) else None
    if not isinstance(session_id, str):
        return jsonify({"error": "Session not found"}), 404

    try:
        draft = get_github_draft(session_id)
    except KeyError:
        return jsonify({"error": "Session not found"}), 404

    author = db.session.query(Author).first()
    if author is None:
        return jsonify({"error": "Project author is unavailable"}), 400

    title = draft["title"].strip()
    if not title:
        return jsonify({"error": "The draft title is required"}), 400
    technologies = ", ".join(
        technology.strip()
        for technology in draft["technologies"]
        if technology.strip()
    )
    project = Project(
        title=title,
        description=draft["summary"],
        summary=draft["summary"],
        technologies=technologies,
        difficulty=draft["difficulty"],
        likes=0,
        author_id=author.id,
    )
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
