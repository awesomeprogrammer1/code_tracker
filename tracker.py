import csv
import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
LOG_FILE = os.path.join(os.path.dirname(__file__), "todos.csv")


def read_todos():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        return [row for row in csv.reader(f) if row]


def write_todos(todos):
    with open(LOG_FILE, "w", newline="") as f:
        csv.writer(f).writerows(todos)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/todos", methods=["GET"])
def get_todos():
    todos = read_todos()
    difficulty = request.args.get("difficulty")
    sort = request.args.get("sort")

    if difficulty and difficulty != "All":
        todos = [t for t in todos if t[1] == difficulty]
    if sort == "date":
        todos = sorted(todos, key=lambda x: datetime.strptime(x[2], "%Y-%m-%d %H:%M:%S"))
    elif sort == "difficulty":
        todos = sorted(todos, key=lambda x: x[1])

    return jsonify([
        {"id": i, "name": t[0], "difficulty": t[1], "date": t[2], "status": t[3]}
        for i, t in enumerate(todos)
    ])


@app.route("/todos", methods=["POST"])
def add_todo():
    data = request.get_json()
    name = data.get("name", "").strip()
    difficulty = data.get("difficulty", "").strip()

    if not name or difficulty not in ("Easy", "Medium", "Hard"):
        return jsonify({"error": "Invalid input"}), 400

    log_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow([name, difficulty, log_date, "Pending"])

    return jsonify({"message": "To-do added successfully"}), 201


@app.route("/todos/<int:todo_id>/done", methods=["PATCH"])
def mark_done(todo_id):
    todos = read_todos()
    if todo_id < 0 or todo_id >= len(todos):
        return jsonify({"error": "Invalid ID"}), 404
    todos[todo_id][3] = "Done"
    write_todos(todos)
    return jsonify({"message": "To-do marked as done"})


@app.route("/todos/<int:todo_id>", methods=["DELETE"])
def remove_todo(todo_id):
    todos = read_todos()
    if todo_id < 0 or todo_id >= len(todos):
        return jsonify({"error": "Invalid ID"}), 404
    todos.pop(todo_id)
    write_todos(todos)
    return jsonify({"message": "To-do removed successfully"})


if __name__ == "__main__":
    app.run(debug=True)
