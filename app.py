import os
import uuid
import io
import base64
import tempfile
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, send_file, abort
)
from dotenv import load_dotenv

from utils.pdf_generator import generate_contract_pdf

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "contrat-coaching-secret-key-change-me")
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

DATABASE_URL = os.environ.get("DATABASE_URL", "")
PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs")

COACH_PASSWORD = os.environ.get("COACH_PASSWORD", "MNS-12345-MNS")

COACH = {
    "prenom": "ALAN",
    "nom": "SENNOUN",
    "raison_sociale": "E-PartnerPro",
    "siret": "98124052600013",
    "adresse": "159 Avenue du Marechal Foch - Neuilly-Plaisance (93360)",
    "email": "contact@protocolemns.com",
    "telephone": "07 83 78 92 39",
}

# ─── Database ───

use_postgres = bool(DATABASE_URL)

if use_postgres:
    import psycopg2
    import psycopg2.extras

    def get_db():
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        # Remove pgbouncer param if present (not supported by psycopg2)
        if "?pgbouncer=true" in url:
            url = url.replace("?pgbouncer=true", "")
        elif "&pgbouncer=true" in url:
            url = url.replace("&pgbouncer=true", "")
        conn = psycopg2.connect(url)
        return conn

    def init_db():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS contrats (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'en_attente',
                contrat_date TEXT,
                date_debut TEXT,
                poids_actuel TEXT,
                poids_min TEXT,
                poids_max TEXT,
                perte_min TEXT,
                perte_max TEXT,
                prix TEXT,
                coach_signature TEXT,
                coach_date_sig TEXT,
                client_prenom TEXT,
                client_nom TEXT,
                client_adresse TEXT,
                client_email TEXT,
                client_tel TEXT,
                client_lieu TEXT,
                client_date_sig TEXT,
                client_prenom_sig TEXT,
                client_nom_sig TEXT,
                client_signature TEXT,
                pdf_data BYTEA
            )
        """)
        conn.commit()
        cur.close()
        conn.close()

    def db_execute(query, params=None):
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Convert ? placeholders to %s for PostgreSQL
        query = query.replace("?", "%s")
        cur.execute(query, params or ())
        conn.commit()
        return conn, cur

    def db_fetchone(query, params=None):
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = query.replace("?", "%s")
        cur.execute(query, params or ())
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row

    def db_fetchall(query, params=None):
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = query.replace("?", "%s")
        cur.execute(query, params or ())
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def db_insert(query, params=None):
        conn = get_db()
        cur = conn.cursor()
        query = query.replace("?", "%s")
        cur.execute(query, params or ())
        conn.commit()
        cur.close()
        conn.close()

    def db_update(query, params=None):
        conn = get_db()
        cur = conn.cursor()
        query = query.replace("?", "%s")
        cur.execute(query, params or ())
        conn.commit()
        cur.close()
        conn.close()

else:
    import sqlite3

    SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contrats.db")

    def get_db():
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db():
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS contrats (
                id TEXT PRIMARY KEY,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'en_attente',
                contrat_date TEXT,
                date_debut TEXT,
                poids_actuel TEXT,
                poids_min TEXT,
                poids_max TEXT,
                perte_min TEXT,
                perte_max TEXT,
                prix TEXT,
                coach_signature TEXT,
                coach_date_sig TEXT,
                client_prenom TEXT,
                client_nom TEXT,
                client_adresse TEXT,
                client_email TEXT,
                client_tel TEXT,
                client_lieu TEXT,
                client_date_sig TEXT,
                client_prenom_sig TEXT,
                client_nom_sig TEXT,
                client_signature TEXT,
                pdf_data BLOB
            )
        """)
        conn.commit()
        conn.close()

    def db_fetchone(query, params=None):
        conn = get_db()
        row = conn.execute(query, params or ()).fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def db_fetchall(query, params=None):
        conn = get_db()
        rows = conn.execute(query, params or ()).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def db_insert(query, params=None):
        conn = get_db()
        conn.execute(query, params or ())
        conn.commit()
        conn.close()

    def db_update(query, params=None):
        conn = get_db()
        conn.execute(query, params or ())
        conn.commit()
        conn.close()


init_db()
os.makedirs(PDF_DIR, exist_ok=True)


def coach_logged_in():
    return session.get("coach_logged_in", False)


# ─── Routes ───


@app.route("/")
def index():
    return render_template("login.html", error=None)


@app.route("/login", methods=["POST"])
def login():
    password = request.form.get("password", "")
    if password == COACH_PASSWORD:
        session["coach_logged_in"] = True
        return redirect(url_for("nouveau"))
    return render_template("login.html", error="Mot de passe incorrect.")


@app.route("/nouveau")
def nouveau():
    if not coach_logged_in():
        return redirect(url_for("index"))
    return render_template("coach_form.html", coach=COACH)


@app.route("/creer", methods=["POST"])
def creer():
    if not coach_logged_in():
        return redirect(url_for("index"))

    contrat_id = str(uuid.uuid4())[:8]

    contrat_date = request.form.get("contrat_date", "")
    date_debut = request.form.get("date_debut", "")
    poids_actuel = request.form.get("poids_actuel", "")
    poids_min = request.form.get("poids_min", "")
    poids_max = request.form.get("poids_max", "")
    perte_min = request.form.get("perte_min", "")
    perte_max = request.form.get("perte_max", "")
    prix = request.form.get("prix", "")
    coach_signature = request.form.get("coach_signature", "")
    coach_date_sig = request.form.get("coach_date_sig", "")

    db_insert("""
        INSERT INTO contrats (id, contrat_date, date_debut, poids_actuel, poids_min,
            poids_max, perte_min, perte_max, prix, coach_signature, coach_date_sig)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (contrat_id, contrat_date, date_debut, poids_actuel, poids_min,
          poids_max, perte_min, perte_max, prix, coach_signature, coach_date_sig))

    return redirect(url_for("lien", contrat_id=contrat_id))


@app.route("/lien/<contrat_id>")
def lien(contrat_id):
    if not coach_logged_in():
        return redirect(url_for("index"))
    base_url = request.host_url.rstrip("/")
    client_url = f"{base_url}/signer/{contrat_id}"
    return render_template("lien.html", client_url=client_url, contrat_id=contrat_id)


@app.route("/signer/<contrat_id>")
def signer(contrat_id):
    contrat = db_fetchone("SELECT * FROM contrats WHERE id = ?", (contrat_id,))

    if not contrat:
        abort(404)

    if contrat["status"] == "signe":
        return render_template("confirmation.html", contrat_id=contrat_id, already_signed=True)

    return render_template("client_form.html", contrat=contrat, coach=COACH)


@app.route("/finaliser/<contrat_id>", methods=["POST"])
def finaliser(contrat_id):
    contrat = db_fetchone("SELECT * FROM contrats WHERE id = ?", (contrat_id,))

    if not contrat:
        abort(404)

    if contrat["status"] == "signe":
        return render_template("confirmation.html", contrat_id=contrat_id, already_signed=True)

    client_prenom = request.form.get("client_prenom", "")
    client_nom = request.form.get("client_nom", "")
    client_adresse = request.form.get("client_adresse", "")
    client_email = request.form.get("client_email", "")
    client_tel = request.form.get("client_tel", "")
    client_lieu = request.form.get("client_lieu", "")
    client_date_sig = request.form.get("client_date_sig", "")
    client_prenom_sig = request.form.get("client_prenom_sig", "")
    client_nom_sig = request.form.get("client_nom_sig", "")
    client_signature = request.form.get("client_signature", "")

    # Generate PDF
    contrat_data = dict(contrat)
    contrat_data.update({
        "client_prenom": client_prenom,
        "client_nom": client_nom,
        "client_adresse": client_adresse,
        "client_email": client_email,
        "client_tel": client_tel,
        "client_lieu": client_lieu,
        "client_date_sig": client_date_sig,
        "client_prenom_sig": client_prenom_sig,
        "client_nom_sig": client_nom_sig,
        "client_signature": client_signature,
    })

    # Generate PDF to temp file, then read bytes
    safe_name = f"{client_prenom}_{client_nom}".replace(" ", "_")
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in "_-")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"contrat_{safe_name}_{timestamp}.pdf"
    pdf_path = os.path.join(PDF_DIR, filename)

    generate_contract_pdf(contrat_data, COACH, pdf_path)

    # Read PDF bytes and store in DB
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # Clean up temp file
    try:
        os.remove(pdf_path)
    except OSError:
        pass

    if use_postgres:
        pdf_param = psycopg2.Binary(pdf_bytes)
    else:
        pdf_param = pdf_bytes

    db_update("""
        UPDATE contrats SET
            status = 'signe',
            client_prenom = ?, client_nom = ?, client_adresse = ?,
            client_email = ?, client_tel = ?, client_lieu = ?,
            client_date_sig = ?, client_prenom_sig = ?, client_nom_sig = ?,
            client_signature = ?, pdf_data = ?
        WHERE id = ?
    """, (client_prenom, client_nom, client_adresse, client_email, client_tel,
          client_lieu, client_date_sig, client_prenom_sig, client_nom_sig,
          client_signature, pdf_param, contrat_id))

    return render_template("confirmation.html", contrat_id=contrat_id, already_signed=False)


@app.route("/telecharger/<contrat_id>")
def telecharger(contrat_id):
    contrat = db_fetchone("SELECT * FROM contrats WHERE id = ?", (contrat_id,))

    if not contrat or not contrat.get("pdf_data"):
        abort(404)

    pdf_bytes = contrat["pdf_data"]
    if isinstance(pdf_bytes, memoryview):
        pdf_bytes = bytes(pdf_bytes)

    safe_name = ""
    if contrat.get("client_prenom") and contrat.get("client_nom"):
        safe_name = f"{contrat['client_prenom']}_{contrat['client_nom']}".replace(" ", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "_-")

    filename = f"contrat_{safe_name or contrat_id}.pdf"

    return send_file(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf"
    )


@app.route("/mes-contrats")
def mes_contrats():
    if not coach_logged_in():
        return redirect(url_for("index"))
    contrats = db_fetchall("SELECT id, created_at, status, contrat_date, prix, client_prenom, client_nom FROM contrats ORDER BY created_at DESC")
    return render_template("mes_contrats.html", contrats=contrats)


@app.route("/supprimer", methods=["POST"])
def supprimer():
    if not coach_logged_in():
        return redirect(url_for("index"))

    ids = request.form.getlist("ids")
    if ids:
        for contrat_id in ids:
            db_update("DELETE FROM contrats WHERE id = ?", (contrat_id,))

    return redirect(url_for("mes_contrats"))


@app.route("/logout")
def logout():
    session.pop("coach_logged_in", None)
    return redirect(url_for("index"))


@app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
