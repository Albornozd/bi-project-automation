import os
import json
import openai

INPUT_FILE = os.environ.get("INPUT_FILE", "data/linear_issues.json")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "reports/backlog_report.md")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

os.makedirs("reports", exist_ok=True)

with open(INPUT_FILE, encoding="utf-8") as f:
    data = json.load(f)

issues = data.get("data", {}).get("issues", {}).get("nodes", [])

report_text = "# Backlog / BI Report\n\n"

for i in issues:
    labels_dict = {lbl.get("description","Otros"): lbl.get("name") for lbl in i.get("labels", {}).get("nodes", [])}

    assignee = i.get("assignee")
    assignee_name = assignee.get("name") if assignee else "Sin asignar"
    state_name = i.get("state", {}).get("name", "-")
    due_date = i.get("dueDate", "Sin fecha")
    project = i.get("project", {})
    project_name = project.get("name", "-")
    team_name = project.get("team", {}).get("name", "-")

    report_text += f"- **Título:** {i.get('title')}\n"
    report_text += f"  - Estado: {state_name}\n"
    report_text += f"  - Asignado a: {assignee_name}\n"
    report_text += f"  - Due Date: {due_date}\n"
    report_text += f"  - Team: {team_name}\n"
    report_text += f"  - Project: {project_name}\n"

    for cat in ["Departamento","Esfuerzo Estimado","Impacto en Negocio","Prioridad","Sociedad","Tipo de Proyecto","Tipo de Trabajo"]:
        report_text += f"  - {cat}: {labels_dict.get(cat,'-')}\n"
    report_text += "\n"

try:
    openai.api_key = OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un asistente que resume reportes BI."},
            {"role": "user", "content": report_text}
        ],
        max_tokens=1000
    )
    report_text += "\n\n# Resumen AI\n\n" + response.choices[0].message.content
except Exception as e:
    report_text += f"\n\n# Nota: OpenAI falló, reporte estándar.\nError: {str(e)}\n"

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(report_text)

print(f"Backlog report generated: {OUTPUT_FILE}")
