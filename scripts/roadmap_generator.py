import os
import json
from openai import OpenAI, error

INPUT_FILE = os.getenv("INPUT_FILE", "data/linear_issues.json")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "reports/backlog_report.md")

# Leer issues de Linear
try:
    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)
    issues = data.get("issues", [])
except Exception as e:
    print(f"Error leyendo {INPUT_FILE}: {e}")
    issues = []

# Preparar texto para OpenAI
prompt = "Genera un reporte detallado del backlog de BI basado en estos issues:\n"
prompt += json.dumps(issues, indent=2)

report_text = "# Backlog / BI Report\n\n"

try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    report_text += response.choices[0].message.content
except Exception as e:
    print(f"OpenAI falló: {e}")
    # Fallback: reporte estándar
    if not issues:
        report_text += "No se encontraron issues para mostrar.\n"
    else:
        for i in issues:
            report_text += f"- [{i.get('team', 'Sin Team')}/{i.get('project', 'Sin Project')}] {i.get('title', 'Sin título')} | "
            report_text += f"Estado: {i.get('status', 'Sin estado')} | Due Date: {i.get('dueDate', 'No asignado')} | "
            report_text += f"Labels: {', '.join([l['name'] for l in i.get('labels', [])])}\n"

# Guardar reporte
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(report_text)

print(f"Reporte generado en {OUTPUT_FILE}")
