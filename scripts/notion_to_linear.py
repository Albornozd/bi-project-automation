import requests
import os
import json

NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")

DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers)

try:
    data = response.json()
except Exception:
    data = {}

# Validación segura
if "results" not in data:
    print("⚠️ Notion API error. Generating fallback report.")

    os.makedirs("reports", exist_ok=True)

    with open("reports/notion_sync_report.md", "w") as f:
        f.write("# Notion Sync Report\n\n")
        f.write("Status: API Error\n")
        f.write("Fallback report generated automatically.\n")

    exit(0)

pages = data["results"]

print(f"Found {len(pages)} pages in Notion")

for page in pages:

    props = page.get("properties", {})

    title = "Untitled"

    try:
        title = props["Name"]["title"][0]["text"]["content"]
    except Exception:
        pass

    print("Task:", title)

print("Notion sync completed.")
