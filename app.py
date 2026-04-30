from flask import Flask, request, jsonify, session, redirect, url_for, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"   # 🔐 change in production

DB_PATH = "expenses.db"
DEFAULT_BUDGET = 50000.00


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        # USERS TABLE  (budget column added)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                budget   REAL DEFAULT 50000.00
            )
        """)

        # Add budget column if upgrading an existing DB that doesn't have it
        try:
            conn.execute("ALTER TABLE users ADD COLUMN budget REAL DEFAULT 50000.00")
        except Exception:
            pass   # column already exists — ignore

        # EXPENSES TABLE (linked to user)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id  INTEGER,
                amount   REAL,
                category TEXT,
                note     TEXT,
                date     TEXT
            )
        """)
        conn.commit()


# ─── helpers ────────────────────────────────────────────────────────────────

def get_user_budget(user_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT budget FROM users WHERE id=?", (user_id,)
        ).fetchone()
    # fallback if the column is NULL (old row)
    return row["budget"] if row and row["budget"] is not None else DEFAULT_BUDGET


# ─── AUTH ROUTES ────────────────────────────────────────────────────────────

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
                    "INSERT INTO users (username, password, budget) VALUES (?, ?, ?)",
                    (username, password, DEFAULT_BUDGET)
                )
                conn.commit()
            return redirect(url_for("login"))
        except Exception:
            return "User already exists"

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ─── MAIN PAGES ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/analytics")
def analytics():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("analytics.html")


# ─── API ────────────────────────────────────────────────────────────────────

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
        "budget": get_user_budget(user_id)
    })


@app.route("/api/add", methods=["POST"])
def add_expense():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

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


# ─── BUDGET API  (NEW) ───────────────────────────────────────────────────────

@app.route("/api/budget", methods=["GET"])
def get_budget():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({"budget": get_user_budget(session["user_id"])})


@app.route("/api/budget", methods=["POST"])
def update_budget():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    new_budget = data.get("budget")

    if new_budget is None or float(new_budget) <= 0:
        return jsonify({"error": "Invalid budget amount"}), 400

    with get_db() as conn:
        conn.execute(
            "UPDATE users SET budget=? WHERE id=?",
            (float(new_budget), session["user_id"])
        )
        conn.commit()

    return jsonify({"message": "Budget updated", "budget": float(new_budget)})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)