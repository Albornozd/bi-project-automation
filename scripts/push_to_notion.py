import os
import json
import requests

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("BI_INITIATIVES_DB")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

with open("data/linear_issues.json") as f:
    data = json.load(f)

for issue in data["issues"]:

    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {

            "Title": {
                "title": [{
                    "text": {
                        "content": issue["title"]
                    }
                }]
            },

            "Team": {
                "select": {"name": issue["team"]}
            },

            "Project": {
                "select": {"name": issue["project"]}
            },

            "Status": {
                "status": {"name": issue["status"]}
            },

            "Due Date": {
                "date": {"start": issue["dueDate"]}
            } if issue["dueDate"] else None

        }
    }

    requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json=payload
    )

print("Issues pushed to Notion")
