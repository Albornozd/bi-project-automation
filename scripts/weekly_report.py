import json
import os
from openai import OpenAI
import datetime

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

with open("data/linear_issues.json") as f:
    data = json.load(f)

issues = data["data"]["issues"]["nodes"]

# Filtrar por semana actual
today = datetime.date.today()
start_week = today - datetime.timedelta(days=today.weekday())  # lunes
end_week = start_week + datetime.timedelta(days=6)

text = ""
for i in issues:
    due = i['dueDate']
    if due:
        due_date = datetime.date.fromisoformat(due[:10])
        if start_week <= due_date <= end_week:
            text += f"{i['title']} - Due: {due_date} - Status: {i['state']['name']}\n"

prompt = f"""
Genera un reporte semanal de avances de proyectos BI para esta semana:

{text}
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":prompt}]
)

summary = response.choices[0].message.content

with open("reports/weekly_report.md","w") as f:
    f.write(summary)

print("✅ Reporte semanal generado")
