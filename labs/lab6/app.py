from flask import Flask, jsonify, render_template


app = Flask(__name__)

projects_db = [
    {
        "id": 1,
        "title": "NBA Player Stats Tracker",
        "description": "a command-line tool for looking up player stats",
        "likes": 0,
    },
    {
        "id": 2,
        "title": "Autonomous Navigational Robot",
        "description": "a robot that finds its own way around",
        "likes": 0,
    },
    {
        "id": 3,
        "title": "LeetCode Assistant (planned)",
        "description": "a tool to help with studying practice problems",
        "likes": 0,
    },
     {
        "id": 4, # hand-edited by SM
        "title": "Smart Watering System", # hand-edited by SM
        "description": "a robot that waters plants based on environmental factors", # hand-edited by SM
        "likes": 0, # hand-edited by SM
    },
]


@app.route("/")
def index():
    return render_template("index.html", projects=projects_db)


@app.post("/api/projects/<int:project_id>/upvote")
def upvote_project(project_id):
    project = next(
        (project for project in projects_db if project["id"] == project_id),
        None,
    )
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    project["likes"] += 1
    return jsonify({"id": project["id"], "likes": project["likes"]})


if __name__ == "__main__":
    app.run(debug=True)
