import os
import json
from openai import OpenAI

INPUT_FILE = os.getenv("INPUT_FILE", "data/linear_issues.json")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "reports/roadmap.md")

with open(INPUT_FILE, encoding="utf-8") as f:
    issues = json.load(f)

try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt_text = f"Genera un roadmap de BI agrupado por Team, Proyecto, Prioridad y Estado:\n{json.dumps(issues, indent=2)}"

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un analista de BI"},
            {"role": "user", "content": prompt_text},
        ],
    )
    report_text = response.choices[0].message.content

except Exception:
    report_text = "Roadmap BI\nNota: OpenAI falló, reporte estándar.\n\n"
    for i in issues:
        assignee_name = i.get("assignee")
        if isinstance(assignee_name, dict):
            assignee_name = assignee_name.get("name", "Sin asignar")
        elif isinstance(assignee_name, str):
            assignee_name = assignee_name
        else:
            assignee_name = "Sin asignar"

        team = i.get("team", "Sin Team")
        project = i.get("project", "Sin Project")
        status = i.get("status", "Sin status")
        due = i.get("dueDate", "Sin fecha")
        labels = ", ".join([l["name"] for l in i.get("labels", [])]) if i.get("labels") else "Sin labels"

        report_text += f"- [{team}/{project}] {i.get('name')} | Status: {status} | Due: {due} | Assignee: {assignee_name} | Labels: {labels}\n"

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(report_text)
