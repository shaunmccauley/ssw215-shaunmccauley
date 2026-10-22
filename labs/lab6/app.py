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
        "title": "Lebron James Tracker",
        "description": "a robot that finds its own way around",
        "likes": 0,
    },
    {
        "id": 3,
        "title": "LeetCode Assistant (planned)",
        "description": "a tool to help with studying practice problems",
        "likes": 0,
    },
]


@app.route("/")
def index():
    return render_template("index.html", projects=projects_db)


if __name__ == "__main__":
    app.run(debug=True)
