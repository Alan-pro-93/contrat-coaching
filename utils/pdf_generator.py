import os
import base64
import tempfile
from fpdf import FPDF


class ContratPDF(FPDF):
    """PDF generator for the coaching contract."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def _section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 30, 80)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(30, 30, 80)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def _body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def _bold_text(self, text):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def _field(self, label, value):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(40, 40, 40)
        w = self.get_string_width(label + " ") + 2
        self.cell(w, 6, label + " ")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(10, 10, 120)
        self.cell(0, 6, str(value), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def _list_item(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.cell(8, 5.5, "-")
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def _check_space(self, needed=40):
        if self.get_y() + needed > self.h - self.b_margin:
            self.add_page()


def generate_contract_pdf(data, coach, pdf_path):
    """
    Generate a PDF contract from form data and save to pdf_path.

    Args:
        data: dict with contract data from DB + client fields
        coach: dict with hardcoded coach info
        pdf_path: str, path to save the PDF
    """
    pdf = ContratPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # ---- Title ----
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(30, 30, 80)
    pdf.cell(0, 12, "CONTRAT D'ACCOMPAGNEMENT", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 12, "PERSONNALISE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Horizontal rule
    pdf.set_draw_color(30, 30, 80)
    pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(6)

    # Date
    pdf._field("Date :", data.get("contrat_date", ""))
    pdf.ln(4)

    # ---- LES PARTIES ----
    pdf._section_title("LES PARTIES")

    pdf._bold_text("Le Coach :")
    pdf._field("Prenom :", coach["prenom"])
    pdf._field("Nom :", coach["nom"])
    pdf._field("Raison sociale :", coach["raison_sociale"])
    pdf._field("SIRET :", coach["siret"])
    pdf._field("Adresse :", coach["adresse"])
    pdf._field("Email :", coach["email"])
    pdf._field("Telephone :", coach["telephone"])
    pdf.ln(3)

    pdf._bold_text("Le Client :")
    pdf._field("Prenom :", data.get("client_prenom", ""))
    pdf._field("Nom :", data.get("client_nom", ""))
    pdf._field("Adresse :", data.get("client_adresse", ""))
    pdf._field("Email :", data.get("client_email", ""))
    pdf._field("Telephone :", data.get("client_tel", ""))
    pdf.ln(4)

    # ---- PREAMBULE ----
    pdf._check_space(50)
    pdf._section_title("PREAMBULE")
    pdf._body_text(
        "Le Coach propose un accompagnement personnalise en nutrition et activite physique "
        "pour aider le Client a atteindre son objectif de transformation physique."
    )
    pdf._body_text(
        "Le Client confirme avoir echange avec le Coach lors d'un appel prealable, au cours "
        "duquel le programme, l'objectif et les conditions ont ete presentes clairement. "
        "Il s'engage en toute connaissance de cause."
    )

    # ---- ARTICLE 1 ----
    pdf._check_space(60)
    pdf._section_title("ARTICLE 1 -- LE PROGRAMME")
    pdf._body_text(
        "Le Coach fournit au Client un accompagnement sur mesure comprenant :"
    )
    pdf._list_item("Un suivi nutritionnel personnalise")
    pdf._list_item("Des recommandations d'activite physique")
    pdf._list_item("Un accompagnement et un suivi regulier de la progression")
    pdf.ln(2)
    pdf._body_text(
        "Ce programme n'est pas un acte medical. Le Client est invite a consulter "
        "son medecin avant de commencer."
    )

    # ---- ARTICLE 2 ----
    pdf._check_space(60)
    pdf._section_title("ARTICLE 2 -- OBJECTIF")
    pdf._body_text(
        "L'objectif du Programme est une perte de poids personnalisee, definie comme suit :"
    )
    pdf._field("Poids actuel :", f"{data.get('poids_actuel', '')} kg")
    pdf._field(
        "Poids vise :",
        f"entre {data.get('poids_min', '')} kg et {data.get('poids_max', '')} kg, "
        f"soit une perte de {data.get('perte_min', '')} a {data.get('perte_max', '')} kg "
        f"d'ici les 90 prochains jours."
    )
    pdf.ln(2)
    pdf._body_text(
        "L'atteinte de cet objectif depend de l'implication du Client. Le Coach met tout en "
        "oeuvre pour l'accompagner, mais reste tenu a une obligation de moyens (et non de resultat)."
    )

    # ---- ARTICLE 3 ----
    pdf._check_space(60)
    pdf._section_title("ARTICLE 3 -- DUREE")

    pdf._bold_text("3.1 -- Periode initiale")
    pdf._body_text(
        f"Le Programme dure 90 jours a compter du {data.get('date_debut', '')} "
        "(ou, a defaut, a compter de la reception du paiement)."
    )

    pdf._check_space(60)
    pdf._bold_text("3.2 -- Prolongation gratuite")
    pdf._body_text(
        "Si l'objectif n'est pas atteint a la fin des 90 jours, le Coach s'engage a poursuivre "
        "l'accompagnement gratuitement, a condition que le Client ait :"
    )
    pdf._body_text(
        "a) Suivi serieusement et regulierement les recommandations du Coach "
        "(alimentation, activite physique, rendez-vous de suivi) ;"
    )
    pdf._body_text(
        "b) Participe activement aux echanges prevus dans le Programme ;"
    )
    pdf._body_text(
        "c) Ne pas avoir interrompu le Programme de sa propre initiative pendant plus de "
        "7 jours consecutifs sans raison valable ;"
    )
    pdf.ln(2)
    pdf._body_text(
        "Le Coach apprecie le respect de ces conditions de bonne foi."
    )
    pdf._body_text(
        "Le Coach se reserve le droit de poursuivre l'accompagnement meme dans le cas ou aucune "
        "de ces conditions n'a ete respectee par le Client, mais ceci releve de sa seule volonte "
        "et ne constitue en aucun cas une obligation legale."
    )
    pdf._body_text(
        "Cette prolongation est limitee a 90 jours supplementaires maximum. Au-dela, "
        "l'accompagnement prend fin automatiquement."
    )
    pdf._body_text(
        "Cet engagement de prolongation est un geste commercial volontaire du Coach. "
        "Il ne constitue pas une garantie de resultat."
    )

    # ---- ARTICLE 4 ----
    pdf._check_space(50)
    pdf._section_title("ARTICLE 4 -- PRIX ET PAIEMENT")
    pdf._field("Prix de l'accompagnement :", f"{data.get('prix', '')} TTC")
    pdf.ln(2)
    pdf._body_text(
        "Le paiement est du en une seule fois a la signature du present contrat, "
        "par virement bancaire, carte bancaire ou tout autre moyen convenu."
    )
    pdf._bold_text(
        "Les sommes versees ne sont pas remboursables."
    )
    pdf._body_text(
        "Le Coach engage des moyens, du temps et des ressources des le demarrage du Programme, "
        "et la prestation est entierement personnalisee."
    )

    # ---- ARTICLE 5 ----
    pdf._check_space(60)
    pdf._section_title("ARTICLE 5 -- DROIT DE RETRACTATION")
    pdf._body_text(
        "Le present contrat etant conclu a distance, le Client dispose en principe d'un droit "
        "de retractation de 14 jours (articles L. 221-18 et suivants du Code de la consommation)."
    )
    pdf._body_text(
        "Cependant, conformement a l'article L. 221-28 du Code de la consommation, le Programme "
        "debutant immediatement des la signature du present contrat, le Client reconnait et "
        "accepte expressement que cette execution immediate entraine la renonciation a son droit "
        "de retractation."
    )
    pdf._body_text(
        "En signant le present contrat, le Client confirme avoir ete informe de cette "
        "renonciation et l'accepter sans reserve."
    )

    # ---- ARTICLE 6 ----
    pdf._check_space(60)
    pdf._section_title("ARTICLE 6 -- ENGAGEMENTS DU CLIENT")
    pdf._body_text("Le Client s'engage a :")
    pdf._body_text(
        "a) Fournir des informations exactes sur son etat de sante, ses antecedents "
        "medicaux et son mode de vie ;"
    )
    pdf._body_text(
        "b) Signaler toute contre-indication medicale, allergie ou traitement en cours ;"
    )
    pdf._body_text(
        "c) Suivre les recommandations du Coach avec serieux et regularite ;"
    )
    pdf._body_text(
        "d) Participer activement aux echanges et suivis prevus ;"
    )
    pdf._body_text(
        "e) Prevenir le Coach en cas de difficulte ;"
    )
    pdf._body_text(
        "f) Consulter son medecin avant de demarrer et en cas de symptome inhabituel."
    )
    pdf._body_text(
        "Les resultats dependent en grande partie de l'implication, la rigueur et la "
        "constance du Client."
    )

    # ---- ARTICLE 7 ----
    pdf._check_space(50)
    pdf._section_title("ARTICLE 7 -- ENGAGEMENTS DU COACH")
    pdf._body_text("Le Coach s'engage a :")
    pdf._body_text("a) Fournir un accompagnement personnalise et adapte ;")
    pdf._body_text("b) Etre disponible et reactif ;")
    pdf._body_text("c) Adapter le Programme selon l'evolution du Client ;")
    pdf._body_text("d) Signaler toute difficulte pouvant affecter le Programme.")

    # ---- ARTICLE 8 ----
    pdf._check_space(60)
    pdf._section_title("ARTICLE 8 -- RESPONSABILITE")
    pdf._body_text("Le Coach ne peut etre tenu responsable :")
    pdf._body_text(
        "a) Des resultats obtenus, le Programme reposant sur une obligation de moyens ;"
    )
    pdf._body_text(
        "b) De tout dommage lie au non-respect des recommandations par le Client ;"
    )
    pdf._body_text(
        "c) De tout probleme de sante non signale par le Client ;"
    )
    pdf._body_text(
        "d) De tout dommage indirect, y compris prejudice moral."
    )
    pdf._body_text(
        "La responsabilite du Coach est en tout etat de cause plafonnee au montant total "
        "percu pour la prestation."
    )
    pdf._body_text(
        "Le Client est seul responsable de l'exactitude de ses informations, de ses decisions "
        "et de la consultation prealable de son medecin."
    )
    pdf._bold_text(
        "Le Programme ne remplace pas un suivi medical. Le Client reconnait en avoir ete informe."
    )

    # ---- ARTICLE 9 ----
    pdf._check_space(60)
    pdf._section_title("ARTICLE 9 -- RESILIATION")

    pdf._bold_text("Par le Client")
    pdf._body_text(
        "Le Client peut resilier a tout moment par ecrit (email ou courrier). "
        "Aucun remboursement ne sera du en cas de resiliation anticipee, "
        "les sommes restant acquises au Coach."
    )

    pdf._bold_text("Par le Coach")
    pdf._body_text("Le Coach peut resilier le contrat en cas de :")
    pdf._body_text("a) Comportement irrespectueux ou menacant du Client ;")
    pdf._body_text("b) Informations volontairement fausses fournies par le Client.")
    pdf._body_text(
        "Ces cas constituent des manquements graves du Client a ses obligations contractuelles. "
        "En cas de resiliation par le Coach pour l'un de ces motifs, aucun remboursement ne sera du."
    )

    # ---- ARTICLE 10 ----
    pdf._check_space(40)
    pdf._section_title("ARTICLE 10 -- PROPRIETE INTELLECTUELLE")
    pdf._body_text(
        "Tous les contenus fournis par le Coach (plans, programmes, supports, videos) restent sa "
        "propriete exclusive. Le Client a un droit d'usage personnel uniquement, pendant la duree "
        "du Programme. Toute reproduction ou partage est interdit."
    )

    # ---- ARTICLE 11 ----
    pdf._check_space(40)
    pdf._section_title("ARTICLE 11 -- DISPOSITIONS FINALES")
    pdf._body_text("Le present contrat est soumis au droit francais.")
    pdf._body_text(
        "Le contrat constitue l'accord complet entre les parties. Toute modification necessite "
        "un accord ecrit des deux parties."
    )
    pdf._body_text(
        "Si une clause est declaree invalide, les autres restent pleinement applicables."
    )

    # ---- SIGNATURES ----
    pdf._check_space(100)
    pdf._section_title("SIGNATURES")
    pdf._body_text(
        "Lu et approuve. En signant ci-dessous, le Client confirme avoir pris connaissance "
        "de l'ensemble du present contrat, en accepter toutes les conditions, et renoncer "
        "expressement a son droit de retractation conformement a l'article 5."
    )
    pdf.ln(6)

    # Coach signature
    pdf._bold_text("Le Coach :")
    pdf._field("Fait a :", "Neuilly-Plaisance")
    pdf._field("Le :", data.get("coach_date_sig", ""))
    pdf._field("Nom :", "SENNOUN")
    pdf._field("Prenom :", "ALAN")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Signature :", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Embed coach signature image
    coach_sig = data.get("coach_signature", "")
    if coach_sig:
        _embed_signature(pdf, coach_sig)
    else:
        pdf.ln(20)

    pdf.ln(8)

    # Client signature
    pdf._check_space(60)
    pdf._bold_text("Le Client :")
    pdf._field("Fait a :", data.get("client_lieu", ""))
    pdf._field("Le :", data.get("client_date_sig", ""))
    pdf._field("Nom :", data.get("client_nom_sig", ""))
    pdf._field("Prenom :", data.get("client_prenom_sig", ""))
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Signature :", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Embed client signature image
    client_sig = data.get("client_signature", "")
    if client_sig:
        _embed_signature(pdf, client_sig)
    else:
        pdf.ln(20)

    pdf.output(pdf_path)


def _embed_signature(pdf, data_url):
    """Embed a base64 data URL signature image into the PDF."""
    try:
        # data_url format: data:image/png;base64,AAAA...
        if "," in data_url:
            img_data = base64.b64decode(data_url.split(",")[1])
        else:
            img_data = base64.b64decode(data_url)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(img_data)
            tmp_path = tmp.name

        pdf.image(tmp_path, x=pdf.get_x(), y=pdf.get_y(), w=60, h=25)
        pdf.ln(28)

        os.unlink(tmp_path)
    except Exception:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 6, "[Signature non disponible]", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
