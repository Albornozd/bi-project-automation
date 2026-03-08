import json
import os
from datetime import datetime
from openai import OpenAI

INPUT_FILE = os.environ.get("INPUT_FILE", "data/linear_issues.json")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "reports/roadmap.md")

# cargar issues de Linear
with open(INPUT_FILE) as f:
    data = json.load(f)

issues = data.get("data", {}).get("issues", {}).get("nodes", [])

# preparar texto para AI
issues_text = "\n".join([f"- {i['title']} ({i['state']['name']})" for i in issues])

prompt = f"Genera un roadmap de BI usando estos tickets:\n{issues_text}"

report = ""

try:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )
    report = response.choices[0].message.content

except Exception as e:
    report = "# Roadmap básico\n\n"
    report += "OpenAI no disponible. Generando roadmap simple.\n\n"
    report += f"Generated: {datetime.now()}\n\n"
    for i in issues:
        report += f"- {i['title']} ({i['state']['name']})\n"

# guardar resultado
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w") as f:
    f.write(report)

print("Roadmap generado:", OUTPUT_FILE)
