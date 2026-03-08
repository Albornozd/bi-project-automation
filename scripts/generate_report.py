import os
import json
from datetime import datetime
from openai import OpenAI

INPUT_FILE = os.environ.get("INPUT_FILE", "data/linear_issues.json")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "reports/backlog_report.md")

# Cargar issues de Linear
with open(INPUT_FILE) as f:
    data = json.load(f)

issues = data.get("data", {}).get("issues", {}).get("nodes", [])

report_text = ""

for i in issues:
    labels_dict = {}
    for lbl in i.get("labels", {}).get("nodes", []):
        cat = lbl.get("description", "Otros")
        labels_dict[cat] = lbl.get("name")
    
    report_text += f"- **Título:** {i.get('title')}\n"
    report_text += f"  - Estado: {i.get('state', {}).get('name')}\n"
    report_text += f"  - Asignado a: {i.get('assignee', {}).get('name', 'Sin asignar')}\n"
    report_text += f"  - Due Date: {i.get('dueDate', 'Sin fecha')}\n"
    for cat in ["Departamento","Esfuerzo Estimado","Impacto en Negocio","Prioridad","Sociedad","Tipo de Proyecto","Tipo de Trabajo"]:
        report_text += f"  - {cat}: {labels_dict.get(cat, '-')}\n"
    report_text += "\n"

# Generación con OpenAI (fallback automático)
report = ""
try:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    prompt = f"Genera un reporte de BI detallado usando estos issues:\n{report_text}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )
    report = response.choices[0].message.content
except Exception:
    report = "# Reporte BI básico\n\n" + report_text
    report += f"\nGenerado: {datetime.now()} (fallback automático)\n"

# Guardar reporte
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w") as f:
    f.write(report)

print("Reporte generado:", OUTPUT_FILE)
