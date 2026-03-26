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
    pdf.cell(0, 12, "PERSONNALISÉ", align="C", new_x="LMARGIN", new_y="NEXT")
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
    pdf._field("Prénom :", coach["prenom"])
    pdf._field("Nom :", coach["nom"])
    pdf._field("Raison sociale :", coach["raison_sociale"])
    pdf._field("SIRET :", coach["siret"])
    pdf._field("Adresse :", coach["adresse"])
    pdf._field("Email :", coach["email"])
    pdf._field("Téléphone :", coach["telephone"])
    pdf.ln(3)

    pdf._bold_text("Le Client :")
    pdf._field("Prénom :", data.get("client_prenom", ""))
    pdf._field("Nom :", data.get("client_nom", ""))
    pdf._field("Adresse :", data.get("client_adresse", ""))
    pdf._field("Email :", data.get("client_email", ""))
    pdf._field("Téléphone :", data.get("client_tel", ""))
    pdf.ln(4)

    # ---- PREAMBULE ----
    pdf._check_space(50)
    pdf._section_title("PRÉAMBULE")
    pdf._body_text(
        "Le Coach propose un accompagnement personnalisé en nutrition et activité physique "
        "pour aider le Client a atteindre son objectif de transformation physique."
    )
    pdf._body_text(
        "Le Client confirme avoir échangé avec le Coach lors d'un appel préalable, au cours "
        "duquel le programme, l'objectif et les conditions ont été présentés clairement. "
        "Il s'engage en toute connaissance de cause."
    )

    # ---- ARTICLE 1 ----
    pdf._check_space(60)
    pdf._section_title("ARTICLE 1 -- LE PROGRAMME")
    pdf._body_text(
        "Le Coach fournit au Client un accompagnement sur mesure comprenant :"
    )
    pdf._list_item("Un suivi nutritionnel personnalisé")
    pdf._list_item("Des recommandations d'activité physique")
    pdf._list_item("Un accompagnement et un suivi régulier de la progression")
    pdf.ln(2)
    pdf._body_text(
        "Ce programme n'est pas un acte médical. Le Client est invité à consulter "
        "son médecin avant de commencer."
    )

    # ---- ARTICLE 2 ----
    pdf._check_space(60)
    pdf._section_title("ARTICLE 2 -- OBJECTIF")
    pdf._body_text(
        "L'objectif du Programme est une perte de poids personnalisée, définie comme suit :"
    )
    pdf._field("Poids actuel :", f"{data.get('poids_actuel', '')} kg")
    pdf._field(
        "Poids visé :",
        f"entre {data.get('poids_min', '')} kg et {data.get('poids_max', '')} kg, "
        f"soit une perte de {data.get('perte_min', '')} a {data.get('perte_max', '')} kg "
        f"d'ici les 90 prochains jours."
    )
    pdf.ln(2)
    pdf._body_text(
        "L'atteinte de cet objectif dépend de l'implication du Client. Le Coach met tout en "
        "oeuvre pour l'accompagner, mais reste tenu a une obligation de moyens (et non de résultat)."
    )

    # ---- ARTICLE 3 ----
    pdf._check_space(60)
    pdf._section_title("ARTICLE 3 -- DURÉE")

    pdf._bold_text("3.1 -- Période initiale")
    pdf._body_text(
        f"Le Programme dure 90 jours a compter du {data.get('date_debut', '')} "
        "(ou, a défaut, a compter de la reception du paiement)."
    )

    pdf._check_space(60)
    pdf._bold_text("3.2 -- Prolongation gratuite")
    pdf._body_text(
        "Si l'objectif n'est pas atteint a la fin des 90 jours, le Coach s'engage a poursuivre "
        "l'accompagnement gratuitement, a condition que le Client ait :"
    )
    pdf._body_text(
        "a) Suivi sérieusement et régulièrement les recommandations du Coach "
        "(alimentation, activité physique, rendez-vous de suivi) ;"
    )
    pdf._body_text(
        "b) Participé activement aux échanges prévus dans le Programme ;"
    )
    pdf._body_text(
        "c) Ne pas avoir interrompu le Programme de sa propre initiative pendant plus de "
        "7 jours consécutifs sans raison valable ;"
    )
    pdf.ln(2)
    pdf._body_text(
        "Le Coach apprécie le respect de ces conditions de bonne foi."
    )
    pdf._body_text(
        "Le Coach se réserve le droit de poursuivre l'accompagnement meme dans le cas ou aucune "
        "de ces conditions n'a été respectée par le Client, mais ceci relève de sa seule volonté "
        "et ne constitue en aucun cas une obligation légale."
    )
    pdf._body_text(
        "Cette prolongation est limitée a 90 jours supplémentaires maximum. Au-delà, "
        "l'accompagnement prend fin automatiquement."
    )
    pdf._body_text(
        "Cet engagement de prolongation est un geste commercial volontaire du Coach. "
        "Il ne constitue pas une garantie de résultat."
    )

    # ---- ARTICLE 4 ----
    pdf._check_space(50)
    pdf._section_title("ARTICLE 4 -- PRIX ET PAIEMENT")
    pdf._field("Prix de l'accompagnement :", f"{data.get('prix', '')} euros TTC")
    pdf.ln(2)
    pdf._body_text(
        "Le paiement est dû en une seule fois a la signature du present contrat, "
        "par virement bancaire, carte bancaire ou tout autre moyen convenu."
    )
    pdf._bold_text(
        "Les sommes versées ne sont pas remboursables."
    )
    pdf._body_text(
        "Le Coach engage des moyens, du temps et des ressources dès le démarrage du Programme, "
        "et la prestation est entièrement personnalisée."
    )

    # ---- ARTICLE 5 ----
    pdf._check_space(60)
    pdf._section_title("ARTICLE 5 -- DROIT DE RÉTRACTATION")
    pdf._body_text(
        "Le present contrat étant conclu a distance, le Client dispose en principe d'un droit "
        "de rétractation de 14 jours (articles L. 221-18 et suivants du Code de la consommation)."
    )
    pdf._body_text(
        "Cependant, conformément a l'article L. 221-28 du Code de la consommation, le Programme "
        "débutant immédiatement dès la signature du present contrat, le Client reconnaît et "
        "accepte expressément que cette exécution immediate entraîne la renonciation a son droit "
        "de rétractation."
    )
    pdf._body_text(
        "En signant le present contrat, le Client confirme avoir été informé de cette "
        "renonciation et l'accepter sans réserve."
    )

    # ---- ARTICLE 6 ----
    pdf._check_space(60)
    pdf._section_title("ARTICLE 6 -- ENGAGEMENTS DU CLIENT")
    pdf._body_text("Le Client s'engage a :")
    pdf._body_text(
        "a) Fournir des informations exactes sur son etat de santé, ses antécédents "
        "médicaux et son mode de vie ;"
    )
    pdf._body_text(
        "b) Signaler toute contre-indication médicale, allergie ou traitement en cours ;"
    )
    pdf._body_text(
        "c) Suivre les recommandations du Coach avec sérieux et régularité ;"
    )
    pdf._body_text(
        "d) Participer activement aux échanges et suivis prévus ;"
    )
    pdf._body_text(
        "e) Prevenir le Coach en cas de difficulté ;"
    )
    pdf._body_text(
        "f) Consulter son médecin avant de démarrer et en cas de symptôme inhabituel."
    )
    pdf._body_text(
        "Les résultats dépendent en grande partie de l'implication, la rigueur et la "
        "constance du Client."
    )

    # ---- ARTICLE 7 ----
    pdf._check_space(50)
    pdf._section_title("ARTICLE 7 -- ENGAGEMENTS DU COACH")
    pdf._body_text("Le Coach s'engage a :")
    pdf._body_text("a) Fournir un accompagnement personnalisé et adapté ;")
    pdf._body_text("b) Être disponible et réactif ;")
    pdf._body_text("c) Adapter le Programme selon l'évolution du Client ;")
    pdf._body_text("d) Signaler toute difficulté pouvant affecter le Programme.")

    # ---- ARTICLE 8 ----
    pdf._check_space(60)
    pdf._section_title("ARTICLE 8 -- RESPONSABILITÉ")
    pdf._body_text("Le Coach ne peut etre tenu responsable :")
    pdf._body_text(
        "a) Des résultats obtenus, le Programme reposant sur une obligation de moyens ;"
    )
    pdf._body_text(
        "b) De tout dommage lié au non-respect des recommandations par le Client ;"
    )
    pdf._body_text(
        "c) De tout problème de santé non signalé par le Client ;"
    )
    pdf._body_text(
        "d) De tout dommage indirect, y compris préjudice moral."
    )
    pdf._body_text(
        "La responsabilité du Coach est en tout etat de cause plafonnée au montant total "
        "perçu pour la prestation."
    )
    pdf._body_text(
        "Le Client est seul responsable de l'exactitude de ses informations, de ses décisions "
        "et de la consultation préalable de son médecin."
    )
    pdf._bold_text(
        "Le Programme ne remplace pas un suivi médical. Le Client reconnaît en avoir été informé."
    )

    # ---- ARTICLE 9 ----
    pdf._check_space(60)
    pdf._section_title("ARTICLE 9 -- RÉSILIATION")

    pdf._bold_text("Par le Client")
    pdf._body_text(
        "Le Client peut résilier a tout moment par écrit (email ou courrier). "
        "Aucun remboursement ne sera dû en cas de résiliation anticipée, "
        "les sommes restant acquises au Coach."
    )

    pdf._bold_text("Par le Coach")
    pdf._body_text("Le Coach peut résilier le contrat en cas de :")
    pdf._body_text("a) Comportement irrespectueux ou menaçant du Client ;")
    pdf._body_text("b) Informations volontairement fausses fournies par le Client.")
    pdf._body_text(
        "Ces cas constituent des manquements graves du Client a ses obligations contractuelles. "
        "En cas de résiliation par le Coach pour l'un de ces motifs, aucun remboursement ne sera dû."
    )

    # ---- ARTICLE 10 ----
    pdf._check_space(40)
    pdf._section_title("ARTICLE 10 -- PROPRIÉTÉ INTELLECTUELLE")
    pdf._body_text(
        "Tous les contenus fournis par le Coach (plans, programmes, supports, vidéos) restent sa "
        "propriété exclusive. Le Client a un droit d'usage personnel uniquement, pendant la durée "
        "du Programme. Toute reproduction ou partage est interdit."
    )

    # ---- ARTICLE 11 ----
    pdf._check_space(40)
    pdf._section_title("ARTICLE 11 -- DISPOSITIONS FINALES")
    pdf._body_text("Le present contrat est soumis au droit français.")
    pdf._body_text(
        "Le contrat constitue l'accord complet entre les parties. Toute modification nécessite "
        "un accord écrit des deux parties."
    )
    pdf._body_text(
        "Si une clause est déclarée invalide, les autres restent pleinement applicables."
    )

    # ---- SIGNATURES ----
    pdf._check_space(100)
    pdf._section_title("SIGNATURES")
    pdf._body_text(
        "Lu et approuvé. En signant ci-dessous, le Client confirme avoir pris connaissance "
        "de l'ensemble du present contrat, en accepter toutes les conditions, et renoncer "
        "expressément a son droit de rétractation conformément a l'article 5."
    )
    pdf.ln(6)

    # Coach signature
    pdf._bold_text("Le Coach :")
    pdf._field("Fait à :", "Neuilly-Plaisance")
    pdf._field("Le :", data.get("coach_date_sig", ""))
    pdf._field("Nom :", "SENNOUN")
    pdf._field("Prénom :", "ALAN")
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
    pdf._field("Fait à :", data.get("client_lieu", ""))
    pdf._field("Le :", data.get("client_date_sig", ""))
    pdf._field("Nom :", data.get("client_nom_sig", ""))
    pdf._field("Prénom :", data.get("client_prenom_sig", ""))
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
