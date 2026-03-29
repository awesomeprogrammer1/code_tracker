import csv
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash, Response
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

# Create the Flask app instance. __name__ tells Flask where to look for
# templates and static files (relative to this file's location).
app = Flask(__name__)
conn = sqlite3.connect('users.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (username TEXT PRIMARY KEY, password_hash TEXT)''')
conn.commit()




# Secret key is required for session cookies to work. Change this to something
# random and private before deploying anywhere beyond your local machine.
app.secret_key = os.environ.get("SECRET_KEY", "fallback-for-development-only")


# Build an absolute path to todos.csv so it always resolves correctly
# regardless of which directory you run the script from.
LOG_FILE = os.path.join(os.path.dirname(__file__), "todos.csv")

@app.route('/')
def homepage():
    if session.get("logged_in"):
        return redirect(url_for("home"))
    return render_template('homepage.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()
        if row and check_password_hash(row[0], password):
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("home"))
        flash("Invalid username or password.")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE username = ?", (username,))
        existing = c.fetchone()
        if existing:
            flash("Username already exists.")
        else:
            c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                      (username, generate_password_hash(password)))
            conn.commit()
            conn.commit()
            flash("Registration successful. You can now log in.")
            conn.close()
            return redirect(url_for("login"))
        conn.close()
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/home")
def home():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("home.html")


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
    with open(LOG_FILE, "r") as f:
        todos = [row for row in csv.reader(f) if row]

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
    # pinned is column 4; default to "No" for older rows that predate the column.
    return jsonify([
        {"id": i, "name": t[0], "difficulty": t[1], "date": t[2], "status": t[3],
         "pinned": t[4] if len(t) > 4 else "No",
         "tags":   t[5] if len(t) > 5 else "",
         "due":    t[6] if len(t) > 6 else ""}
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
    tags = data.get("tags", "").strip()
    due  = data.get("due",  "").strip()

    # Reject the request early if required fields are missing or invalid.
    if not name or difficulty not in ("Easy", "Medium", "Hard"):
        return jsonify({"error": "Invalid input"}), 400

    log_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow([name, difficulty, log_date, "Pending", "No", tags, due])

    # 201 Created is the conventional HTTP status for a successful POST.
    return jsonify({"message": "To-do added successfully"}), 201


@app.route("/todos/<int:todo_id>/done", methods=["PATCH"])
def mark_done(todo_id):
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    with open(LOG_FILE, "r") as f:
        todos = [row for row in csv.reader(f) if row]

    # Guard against an out-of-range id sent by the client.
    if todo_id < 0 or todo_id >= len(todos):
        return jsonify({"error": "Invalid ID"}), 404

    # Update the status column (index 3) in-memory, then persist the change.
    todos[todo_id][3] = "Done"
    with open(LOG_FILE, "w", newline="") as f:
        csv.writer(f).writerows(todos)
    return jsonify({"message": "To-do marked as done"})


@app.route("/todos/<int:todo_id>/pin", methods=["PATCH"])
def pin_todo(todo_id):
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    with open(LOG_FILE, "r") as f:
        todos = [row for row in csv.reader(f) if row]
    if todo_id < 0 or todo_id >= len(todos):
        return jsonify({"error": "Invalid ID"}), 404
    # Pad row to 5 columns if it predates the pinned column
    while len(todos[todo_id]) < 5:
        todos[todo_id].append("No")
    todos[todo_id][4] = "No" if todos[todo_id][4] == "Yes" else "Yes"
    with open(LOG_FILE, "w", newline="") as f:
        csv.writer(f).writerows(todos)
    return jsonify({"pinned": todos[todo_id][4]})


@app.route("/todos/<int:todo_id>/rename", methods=["PATCH"])
def rename_todo(todo_id):
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    new_name = data.get("name", "").strip()
    if not new_name:
        return jsonify({"error": "Invalid name"}), 400
    with open(LOG_FILE, "r") as f:
        todos = [row for row in csv.reader(f) if row]
    if todo_id < 0 or todo_id >= len(todos):
        return jsonify({"error": "Invalid ID"}), 404
    todos[todo_id][0] = new_name
    with open(LOG_FILE, "w", newline="") as f:
        csv.writer(f).writerows(todos)
    return jsonify({"message": "To-do renamed"})


@app.route("/todos/<int:todo_id>", methods=["DELETE"])
def remove_todo(todo_id):
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    with open(LOG_FILE, "r") as f:
        todos = [row for row in csv.reader(f) if row]

    # Guard against an out-of-range id sent by the client.
    if todo_id < 0 or todo_id >= len(todos):
        return jsonify({"error": "Invalid ID"}), 404

    # Remove the entry from the list, then rewrite the whole CSV.
    todos.pop(todo_id)
    with open(LOG_FILE, "w", newline="") as f:
        csv.writer(f).writerows(todos)
    return jsonify({"message": "To-do removed successfully"})


def ics_escape(text):
    return str(text).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


@app.route("/todos/export.ics")
def export_ics():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    with open(LOG_FILE, "r") as f:
        todos = [row for row in csv.reader(f) if row]

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//TodoTracker//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for i, t in enumerate(todos):
        due = t[6].strip() if len(t) > 6 else ""
        if not due:
            continue
        try:
            dt_start = datetime.strptime(due, "%Y-%m-%dT%H:%M")
            dt_end   = dt_start + timedelta(hours=1)
            dtstart  = dt_start.strftime("%Y%m%dT%H%M%S")
            dtend    = dt_end.strftime("%Y%m%dT%H%M%S")
        except ValueError:
            continue

        lines += [
            "BEGIN:VEVENT",
            f"UID:todo-{i}@todotracker",
            f"SUMMARY:{ics_escape(t[0])}",
            f"DTSTART:{dtstart}",
            f"DTEND:{dtend}",
            f"DESCRIPTION:Difficulty: {ics_escape(t[1])}\\nStatus: {ics_escape(t[3])}",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")
    content = "\r\n".join(lines) + "\r\n"

    return Response(
        content,
        mimetype="text/calendar",
        headers={"Content-Disposition": "attachment; filename=todos.ics"}
    )


# Only start the development server when this file is run directly
# (not when it's imported as a module). debug=True enables auto-reload
# and the interactive debugger in the browser.
if __name__ == "__main__":
    app.run(debug=True)
