import os
import json
from openai import OpenAI

INPUT_FILE = os.getenv("INPUT_FILE", "data/linear_issues.json")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "reports/backlog_report.md")

# Cargar issues de Linear
with open(INPUT_FILE, encoding="utf-8") as f:
    issues = json.load(f)

try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt_text = f"Genera un resumen de BI basado en estos issues:\n{json.dumps(issues, indent=2)}"

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un analista de BI"},
            {"role": "user", "content": prompt_text},
        ],
    )
    report_text = response.choices[0].message.content

except Exception as e:
    # Fallback: reporte estándar si OpenAI falla
    report_text = "Backlog / BI Report\nNota: OpenAI falló, reporte estándar.\n\n"
    for i in issues:
        report_text += (
            f"- [{i.get('team', 'Sin Team')}/{i.get('project', 'Sin Project')}] "
            f"{i.get('name')} | Status: {i.get('status')} | Due: {i.get('dueDate', 'Sin fecha')} | "
            f"Assignee: {i.get('assignee', {}).get('name', 'Sin asignar')} | "
            f"Labels: {', '.join([l['name'] for l in i.get('labels', [])])}\n"
        )

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(report_text)
