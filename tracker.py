import csv
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash

# Create the Flask app instance. __name__ tells Flask where to look for
# templates and static files (relative to this file's location).
app = Flask(__name__)

# Secret key is required for session cookies to work. Change this to something
# random and private before deploying anywhere beyond your local machine.
app.secret_key = os.environ.get("SECRET_KEY", "fallback-for-development-only")

# Single-user credentials are loaded from the .env file (never commit plain passwords).
# Change TODO_USERNAME and TODO_PASSWORD in .env to whatever you want.
USERNAME = os.environ.get("TODO_USERNAME", "admin")
PASSWORD_HASH = generate_password_hash(os.environ.get("TODO_PASSWORD", "password"))

# Build an absolute path to todos.csv so it always resolves correctly
# regardless of which directory you run the script from.
LOG_FILE = os.path.join(os.path.dirname(__file__), "todos.csv")


def read_todos():
    # If the CSV doesn't exist yet (no todos added), return an empty list
    # instead of crashing on a missing file.
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        # Skip blank rows that csv.reader may produce for empty lines.
        return [row for row in csv.reader(f) if row]


def write_todos(todos):
    # Overwrite the entire CSV with the current list. newline="" is required
    # on Windows to prevent csv.writer from adding extra blank lines.
    with open(LOG_FILE, "w", newline="") as f:
        csv.writer(f).writerows(todos)


# --- Routes ---

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == USERNAME and check_password_hash(PASSWORD_HASH, password):
            session["logged_in"] = True
            return redirect(url_for("index"))
        flash("Invalid username or password.")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == USERNAME:
            flash("Username already exists.")
        else:
            # In a real application, you would want to validate the password strength
            # and possibly implement additional security measures.
            global PASSWORD_HASH
            PASSWORD_HASH = generate_password_hash(password)
            flash("Registration successful. You can now log in.")
    return render_template("register.html") 


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    # Redirect to login if the user has no active session.
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/todos", methods=["GET"])
def get_todos():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    todos = read_todos()

    # Optional query parameters let the caller filter and sort the results.
    # e.g. GET /todos?difficulty=Hard&sort=date
    difficulty = request.args.get("difficulty")
    sort = request.args.get("sort")

    # Filter by difficulty if a specific value was provided (ignore "All").
    if difficulty and difficulty != "All":
        todos = [t for t in todos if t[1] == difficulty]

    # Sort by the date column (index 2) or the difficulty column (index 1).
    if sort == "date":
        todos = sorted(todos, key=lambda x: datetime.strptime(x[2], "%Y-%m-%d %H:%M:%S"))
    elif sort == "difficulty":
        todos = sorted(todos, key=lambda x: x[1])

    # Convert each CSV row into a dict and attach a numeric id so the
    # front-end can reference individual todos in PATCH/DELETE requests.
    return jsonify([
        {"id": i, "name": t[0], "difficulty": t[1], "date": t[2], "status": t[3]}
        for i, t in enumerate(todos)
    ])


@app.route("/todos", methods=["POST"])
def add_todo():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    # Expect a JSON body: { "name": "...", "difficulty": "Easy|Medium|Hard" }
    data = request.get_json()
    name = data.get("name", "").strip()
    difficulty = data.get("difficulty", "").strip()

    # Reject the request early if required fields are missing or invalid.
    if not name or difficulty not in ("Easy", "Medium", "Hard"):
        return jsonify({"error": "Invalid input"}), 400

    log_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Append a single new row to the CSV. Using "a" (append) mode means
    # existing todos are never overwritten.
    with open(LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow([name, difficulty, log_date, "Pending"])

    # 201 Created is the conventional HTTP status for a successful POST.
    return jsonify({"message": "To-do added successfully"}), 201


@app.route("/todos/<int:todo_id>/done", methods=["PATCH"])
def mark_done(todo_id):
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    todos = read_todos()

    # Guard against an out-of-range id sent by the client.
    if todo_id < 0 or todo_id >= len(todos):
        return jsonify({"error": "Invalid ID"}), 404

    # Update the status column (index 3) in-memory, then persist the change.
    todos[todo_id][3] = "Done"
    write_todos(todos)
    return jsonify({"message": "To-do marked as done"})


@app.route("/todos/<int:todo_id>", methods=["DELETE"])
def remove_todo(todo_id):
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    todos = read_todos()

    # Guard against an out-of-range id sent by the client.
    if todo_id < 0 or todo_id >= len(todos):
        return jsonify({"error": "Invalid ID"}), 404

    # Remove the entry from the list, then rewrite the whole CSV.
    todos.pop(todo_id)
    write_todos(todos)
    return jsonify({"message": "To-do removed successfully"})


# Only start the development server when this file is run directly
# (not when it's imported as a module). debug=True enables auto-reload
# and the interactive debugger in the browser.
if __name__ == "__main__":
    app.run(debug=True)
