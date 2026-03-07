import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

with open("data/linear_issues.json") as f:
    data = json.load(f)

issues = data["data"]["issues"]["nodes"]

# Preparar texto para ChatGPT
text = ""
for i in issues:
    text += f"""
Title: {i['title']}
Status: {i['state']['name']}
Priority: {i['priority']}
Due Date: {i['dueDate']}
Labels: {', '.join([l['name'] for l in i['labels']]) if i['labels'] else 'None'}
Assignee: {i['assignee']['name'] if i['assignee'] else 'Unassigned'}
Description: {i['description'] or 'None'}
"""

prompt = f"""
Analiza este backlog de proyectos BI y genera:

1. Resumen del estado del backlog
2. Riesgos principales
3. Prioridades recomendadas
4. Recomendaciones de gestión

Backlog:
{text}
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":prompt}]
)

summary = response.choices[0].message.content

# Guardar resumen en Markdown
with open("reports/backlog_summary.md","w") as f:
    f.write(summary)

print("✅ Resumen de backlog generado")
