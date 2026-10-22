from flask import Flask, render_template


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
        "title": "Autonomous Robot",
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


if __name__ == "__main__":
    app.run(debug=True)
