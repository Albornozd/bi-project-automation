import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

with open("data/linear_issues.json") as f:
    data = json.load(f)

issues = data["data"]["issues"]["nodes"]

text = ""
for i in issues:
    text += f"""
Title: {i['title']}
Due: {i['dueDate']}
Priority: {i['priority']}
Status: {i['state']['name']}
Labels: {', '.join([l['name'] for l in i['labels']]) if i['labels'] else 'None'}
"""

prompt = f"""
Genera un roadmap visual y organizado de proyectos BI basado en el siguiente backlog:

{text}
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":prompt}]
)

roadmap = response.choices[0].message.content

with open("reports/roadmap.md","w") as f:
    f.write(roadmap)

print("✅ Roadmap generado")
