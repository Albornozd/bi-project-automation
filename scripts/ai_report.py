import json
import os
from openai import OpenAI
from datetime import datetime

INPUT_FILE = os.environ.get("INPUT_FILE")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE")

with open(INPUT_FILE) as f:
    data = json.load(f)

items = data["data"]["issues"]["nodes"]

text = "\n".join([f"- {i['title']}" for i in items])

prompt = f"""
Generate a BI backlog summary:

{text}
"""

report = ""

try:

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    report = response.choices[0].message.content

except Exception as e:

    report = "# Automatic Backlog Report\n\n"
    report += "OpenAI unavailable. Basic report generated.\n\n"
    report += f"Generated: {datetime.now()}\n\n"

    for item in items:
        report += f"- {item['title']}\n"

with open(OUTPUT_FILE,"w") as f:
    f.write(report)

print("Report generated:", OUTPUT_FILE)
