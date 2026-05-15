import os
from decimal import Decimal, InvalidOperation
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from mysql.connector import pooling, Error
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "moneypal"),
    "autocommit": False,
}

pool = pooling.MySQLConnectionPool(pool_name="moneypal_pool", pool_size=5, **DB_CONFIG)


def get_conn():
    return pool.get_connection()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def parse_amount(raw_value):
    try:
        amount = Decimal(raw_value).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        return None
    return amount if amount > 0 else None


def current_user():
    if "user_id" not in session:
        return None
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT u.user_id, u.first_name, u.last_name, u.username, w.bal
        FROM users u
        JOIN wallet w ON w.wallet_id = u.user_id
        WHERE u.user_id = %s
        """,
        (session["user_id"],),
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        if not all([first_name, last_name, username, password]):
            flash("All fields are required.", "danger")
            return render_template("register.html")

        conn = get_conn()
        cur = conn.cursor()
        try:
            # Atomic user creation. The wallet is created by userwallettrigger in the same transaction.
            conn.start_transaction(isolation_level="READ COMMITTED")
            cur.execute(
                "INSERT INTO users(first_name, last_name, username, password_hash) VALUES (%s, %s, %s, %s)",
                (first_name, last_name, username, generate_password_hash(password)),
            )
            conn.commit()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for("login"))
        except Error as exc:
            conn.rollback()
            if exc.errno == 1062:
                flash("Username already exists.", "danger")
            else:
                flash(f"Registration failed: {exc}", "danger")
        finally:
            cur.close()
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT t.*, su.username AS sender_username, ru.username AS receiver_username
        FROM transactions t
        LEFT JOIN users su ON su.user_id = t.sender_id
        LEFT JOIN users ru ON ru.user_id = t.receiver_id
        WHERE t.sender_id = %s OR t.receiver_id = %s
        ORDER BY t.created_at DESC, t.transaction_id DESC
        LIMIT 10
        """,
        (session["user_id"], session["user_id"]),
    )
    recent_transactions = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("dashboard.html", user=user, transactions=recent_transactions)


@app.route("/deposit", methods=["POST"])
@login_required
def deposit():
    amount = parse_amount(request.form.get("amount"))
    if amount is None:
        flash("Enter a valid deposit amount.", "danger")
        return redirect(url_for("dashboard"))

    conn = get_conn()
    cur = conn.cursor()
    try:
        # ACID: one DB transaction updates wallet and writes transaction log together.
        conn.start_transaction(isolation_level="READ COMMITTED")
        cur.execute("SELECT bal FROM wallet WHERE wallet_id = %s FOR UPDATE", (session["user_id"],))
        if cur.fetchone() is None:
            raise Error("Wallet not found")
        cur.execute(
            "UPDATE wallet SET bal = bal + %s, last_transaction_type = 'DEPOSIT', last_receiver_id = NULL WHERE wallet_id = %s",
            (amount, session["user_id"]),
        )
        cur.execute(
            "INSERT INTO transactions(sender_id, receiver_id, amount, transaction_type, note) VALUES (NULL, %s, %s, 'DEPOSIT', %s)",
            (session["user_id"], amount, "Wallet deposit"),
        )
        conn.commit()
        flash("Deposit completed successfully.", "success")
    except Error as exc:
        conn.rollback()
        flash(f"Deposit failed and was rolled back: {exc}", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("dashboard"))


@app.route("/withdraw", methods=["POST"])
@login_required
def withdraw():
    amount = parse_amount(request.form.get("amount"))
    if amount is None:
        flash("Enter a valid withdrawal amount.", "danger")
        return redirect(url_for("dashboard"))

    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction(isolation_level="READ COMMITTED")
        cur.execute("SELECT bal FROM wallet WHERE wallet_id = %s FOR UPDATE", (session["user_id"],))
        wallet = cur.fetchone()
        if not wallet or Decimal(wallet["bal"]) < amount:
            raise ValueError("Insufficient balance")
        cur.execute(
            "UPDATE wallet SET bal = bal - %s, last_transaction_type = 'WITHDRAW', last_receiver_id = NULL WHERE wallet_id = %s",
            (amount, session["user_id"]),
        )
        cur.execute(
            "INSERT INTO transactions(sender_id, receiver_id, amount, transaction_type, note) VALUES (%s, NULL, %s, 'WITHDRAW', %s)",
            (session["user_id"], amount, "Wallet withdrawal"),
        )
        conn.commit()
        flash("Withdrawal completed successfully.", "success")
    except (Error, ValueError) as exc:
        conn.rollback()
        flash(f"Withdrawal failed and was rolled back: {exc}", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("dashboard"))


@app.route("/transfer", methods=["POST"])
@login_required
def transfer():
    receiver_username = request.form.get("receiver_username", "").strip().lower()
    amount = parse_amount(request.form.get("amount"))
    if amount is None or not receiver_username:
        flash("Enter a valid receiver username and amount.", "danger")
        return redirect(url_for("dashboard"))
    if receiver_username == session.get("username"):
        flash("You cannot transfer money to yourself.", "danger")
        return redirect(url_for("dashboard"))

    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        # ACID transfer: sender debit, receiver credit, and transaction log commit or rollback as one unit.
        conn.start_transaction(isolation_level="READ COMMITTED")
        cur.execute("SELECT user_id FROM users WHERE username = %s", (receiver_username,))
        receiver = cur.fetchone()
        if not receiver:
            raise ValueError("Receiver not found")
        receiver_id = receiver["user_id"]

        # Lock rows in deterministic order to reduce deadlocks during simultaneous transfers.
        ids = sorted([session["user_id"], receiver_id])
        cur.execute("SELECT wallet_id, bal FROM wallet WHERE wallet_id IN (%s, %s) FOR UPDATE", (ids[0], ids[1]))
        rows = {row["wallet_id"]: row for row in cur.fetchall()}
        sender_wallet = rows.get(session["user_id"])
        if not sender_wallet or Decimal(sender_wallet["bal"]) < amount:
            raise ValueError("Insufficient balance")

        cur.execute(
            "UPDATE wallet SET bal = bal - %s, last_transaction_type = 'TRANSFER_SENT', last_receiver_id = %s WHERE wallet_id = %s",
            (amount, receiver_id, session["user_id"]),
        )
        cur.execute(
            "UPDATE wallet SET bal = bal + %s, last_transaction_type = 'TRANSFER_RECEIVED', last_receiver_id = NULL WHERE wallet_id = %s",
            (amount, receiver_id),
        )
        cur.execute(
            "INSERT INTO transactions(sender_id, receiver_id, amount, transaction_type, note) VALUES (%s, %s, %s, 'USER_TO_USER', %s)",
            (session["user_id"], receiver_id, amount, f"Transfer to {receiver_username}"),
        )
        conn.commit()
        flash("Transfer completed successfully.", "success")
    except (Error, ValueError) as exc:
        conn.rollback()
        flash(f"Transfer failed and was rolled back: {exc}", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("dashboard"))


@app.route("/transactions")
@login_required
def transactions():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT t.*, su.username AS sender_username, ru.username AS receiver_username
        FROM transactions t
        LEFT JOIN users su ON su.user_id = t.sender_id
        LEFT JOIN users ru ON ru.user_id = t.receiver_id
        WHERE t.sender_id = %s OR t.receiver_id = %s
        ORDER BY t.created_at DESC, t.transaction_id DESC
        """,
        (session["user_id"], session["user_id"]),
    )
    records = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("transactions.html", transactions=records)


@app.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    user_id = session["user_id"]
    conn = get_conn()
    cur = conn.cursor()
    try:
        conn.start_transaction(isolation_level="READ COMMITTED")
        cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()
        session.clear()
        flash("Account deleted. Wallet was removed by cascading foreign key.", "info")
        return redirect(url_for("index"))
    except Error as exc:
        conn.rollback()
        flash(f"Account deletion failed: {exc}", "danger")
        return redirect(url_for("dashboard"))
    finally:
        cur.close()
        conn.close()


@app.context_processor
def inject_user():
    return {"logged_in_username": session.get("username")}


if __name__ == "__main__":
    app.run(debug=True)
