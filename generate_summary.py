from fpdf import FPDF

# A simple script to generate a PDF with a single paragraph summarizing the project.

pdf = FPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_font("Arial", size=12)

paragraph = (
    "Ce projet vise à développer un moteur d'analyse de retours utilisateurs en s'appuyant sur "
    "l'API OpenAI. Les données de test sont générées sous forme de CSV, l'IA extrait le "
    "sentiment général et des thèmes spécifiques en produisant un JSON structuré. "
    "L'objectif est de rendre ces informations exploitables dans un tableau de bord Streamlit, "
    "tout en maîtrisant le format de sortie pour garantir la robustesse et la scalabilité."
)

pdf.multi_cell(0, 10, paragraph)

output_path = "mon-projet/resume_projet.pdf"
pdf.output(output_path)
print(f"PDF généré et enregistré sous : {output_path}")
