import os
import uuid
import sqlite3
import base64
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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max (signatures base64)

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contrats.db")
PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs")

COACH_PASSWORD = os.environ.get("COACH_PASSWORD", "MNS-12345-MNS")

# Hardcoded coach info
COACH = {
    "prenom": "ALAN",
    "nom": "SENNOUN",
    "raison_sociale": "E-PartnerPro",
    "siret": "98124052600013",
    "adresse": "159 Avenue du Marechal Foch - Neuilly-Plaisance (93360)",
    "email": "contact@protocolemns.com",
    "telephone": "07 83 78 92 39",
}


def get_db():
    conn = sqlite3.connect(DATABASE)
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
            pdf_path TEXT
        )
    """)
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

    conn = get_db()
    conn.execute("""
        INSERT INTO contrats (id, contrat_date, date_debut, poids_actuel, poids_min,
            poids_max, perte_min, perte_max, prix, coach_signature, coach_date_sig)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (contrat_id, contrat_date, date_debut, poids_actuel, poids_min,
          poids_max, perte_min, perte_max, prix, coach_signature, coach_date_sig))
    conn.commit()
    conn.close()

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
    conn = get_db()
    contrat = conn.execute("SELECT * FROM contrats WHERE id = ?", (contrat_id,)).fetchone()
    conn.close()

    if not contrat:
        abort(404)

    if contrat["status"] == "signe":
        return render_template("confirmation.html", contrat_id=contrat_id, already_signed=True)

    return render_template("client_form.html", contrat=dict(contrat), coach=COACH)


@app.route("/finaliser/<contrat_id>", methods=["POST"])
def finaliser(contrat_id):
    conn = get_db()
    contrat = conn.execute("SELECT * FROM contrats WHERE id = ?", (contrat_id,)).fetchone()

    if not contrat:
        conn.close()
        abort(404)

    if contrat["status"] == "signe":
        conn.close()
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

    safe_name = f"{client_prenom}_{client_nom}".replace(" ", "_")
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in "_-")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"contrat_{safe_name}_{timestamp}.pdf"
    pdf_path = os.path.join(PDF_DIR, filename)

    generate_contract_pdf(contrat_data, COACH, pdf_path)

    conn.execute("""
        UPDATE contrats SET
            status = 'signe',
            client_prenom = ?, client_nom = ?, client_adresse = ?,
            client_email = ?, client_tel = ?, client_lieu = ?,
            client_date_sig = ?, client_prenom_sig = ?, client_nom_sig = ?,
            client_signature = ?, pdf_path = ?
        WHERE id = ?
    """, (client_prenom, client_nom, client_adresse, client_email, client_tel,
          client_lieu, client_date_sig, client_prenom_sig, client_nom_sig,
          client_signature, pdf_path, contrat_id))
    conn.commit()
    conn.close()

    return render_template("confirmation.html", contrat_id=contrat_id, already_signed=False)


@app.route("/telecharger/<contrat_id>")
def telecharger(contrat_id):
    conn = get_db()
    contrat = conn.execute("SELECT * FROM contrats WHERE id = ?", (contrat_id,)).fetchone()
    conn.close()

    if not contrat or not contrat["pdf_path"]:
        abort(404)

    return send_file(contrat["pdf_path"], as_attachment=True,
                     download_name=os.path.basename(contrat["pdf_path"]))


@app.route("/mes-contrats")
def mes_contrats():
    if not coach_logged_in():
        return redirect(url_for("index"))
    conn = get_db()
    contrats = conn.execute("SELECT * FROM contrats ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("mes_contrats.html", contrats=contrats)


@app.route("/logout")
def logout():
    session.pop("coach_logged_in", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
