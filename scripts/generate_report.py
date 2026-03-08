import json
import os
from openai import OpenAI

# cargar datos de Linear
with open("data/linear_issues.json") as f:
    data = json.load(f)

issues = data["data"]["issues"]["nodes"]

# preparar texto para OpenAI
issues_text = "\n".join([f"- {issue['title']} ({issue['state']['name']})" for issue in issues])

prompt = f"""
Analiza el siguiente backlog de BI y genera un resumen ejecutivo:

{issues_text}
"""

report = ""

try:
    print("Intentando generar reporte con OpenAI...")

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    report = response.choices[0].message.content
    print("Reporte generado con OpenAI")

except Exception as e:

    print("OpenAI no disponible. Generando reporte básico.")
    print("Error:", e)

    # generar reporte básico
    report = "# Backlog Report\n\n"
    report += "OpenAI no disponible. Reporte generado automáticamente.\n\n"

    for issue in issues:
        report += f"- {issue['title']} ({issue['state']['name']})\n"

# guardar reporte
with open("reports/backlog_report.md", "w") as f:
    f.write(report)

print("Reporte guardado en reports/backlog_report.md")
