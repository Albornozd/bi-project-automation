import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

with open("data/linear_issues.json") as f:
    data = json.load(f)

issues = data["data"]["issues"]["nodes"]

issues_text = "\n".join([issue["title"] for issue in issues])

prompt = f"""
Analiza el siguiente backlog de BI y genera un resumen ejecutivo:

{issues_text}
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":prompt}]
)

report = response.choices[0].message.content

with open("reports/backlog_report.md","w") as f:
    f.write(report)

print("Reporte generado en reports/backlog_report.md")
