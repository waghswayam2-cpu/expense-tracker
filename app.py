from flask import Flask, request, jsonify, session, redirect, url_for, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"   # 🔐 change in production

DB_PATH = "expenses.db"
BUDGET = 50000.00


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        # USERS TABLE
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        """)

        # EXPENSES TABLE (linked to user)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                category TEXT,
                note TEXT,
                date TEXT
            )
        """)
        conn.commit()


# ---------------- AUTH ROUTES ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.form
        username = data.get("username")
        password = data.get("password")

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password)
            ).fetchone()

        if user:
            session["user_id"] = user["id"]
            return redirect(url_for("index"))
        else:
            return "Invalid credentials"

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = request.form
        username = data.get("username")
        password = data.get("password")

        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, password)
                )
                conn.commit()
            return redirect(url_for("login"))
        except:
            return "User already exists"

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- MAIN PAGE ----------------

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")


# ---------------- API ----------------

@app.route("/api/expenses")
def get_expenses():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]

    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE user_id=? ORDER BY date DESC",
            (user_id,)
        ).fetchall()


    return jsonify({
        "expenses": [dict(r) for r in rows],
        "budget": BUDGET
    })


@app.route("/api/add", methods=["POST"])
def add_expense():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 4

    data = request.json
    user_id = session["user_id"]

    with get_db() as conn:
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, note, date) VALUES (?, ?, ?, ?, ?)",
            (user_id, data["amount"], data["category"], data["note"], data["date"])
        )
        conn.commit()

    return jsonify({"message": "Added"})


@app.route("/api/delete/<int:id>", methods=["DELETE"])
def delete_expense(id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    with get_db() as conn:
        conn.execute("DELETE FROM expenses WHERE id=?", (id,))
        conn.commit()

    return jsonify({"message": "Deleted"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)