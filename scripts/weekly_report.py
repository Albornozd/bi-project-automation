import os
import json
from pathlib import Path
import openai

INPUT_FILE = os.getenv("INPUT_FILE", "data/linear_issues.json")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "reports/weekly_report.md")

Path("reports").mkdir(parents=True, exist_ok=True)

try:
    with open(INPUT_FILE, encoding="utf-8") as f:
        issues = json.load(f)
except FileNotFoundError:
    issues = []

def generar_reporte_estandar(issues):
    report = "# Weekly BI Report - Estándar\n\n"
    for i in issues:
        report += f"- {i.get('name','Sin nombre')} - {i.get('status','Sin estado')} - Due: {i.get('due_date','No asignado')}\n"
    return report

report_text = ""
try:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"Genera un reporte semanal de BI en Markdown basado en:\n{json.dumps(issues, indent=2)}"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}],
        temperature=0
    )
    report_text = response.choices[0].message.content
except openai.OpenAIError as e:
    print(f"OpenAI falló, usando reporte estándar: {e}")
    report_text = generar_reporte_estandar(issues)
except Exception as e:
    print(f"Error inesperado: {e}")
    report_text = generar_reporte_estandar(issues)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(report_text)

print(f"Reporte guardado en {OUTPUT_FILE}")
