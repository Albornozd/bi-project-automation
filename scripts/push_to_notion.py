import json
import requests
import os

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("BI_INITIATIVES_DB")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

with open("linear_issues.json") as f:
    issues = json.load(f)

for issue in issues:

    labels = [l["name"] for l in issue.get("labels", {}).get("nodes", [])]

    payload = {
        "parent": { "database_id": DATABASE_ID },
        "properties": {

            "Nombre": {
                "title": [
                    {
                        "text": {
                            "content": issue["title"]
                        }
                    }
                ]
            },

            "Team": {
                "rich_text": [
                    {
                        "text": {
                            "content": issue["team"]["name"] if issue.get("team") else ""
                        }
                    }
                ]
            },

            "Proyecto": {
                "rich_text": [
                    {
                        "text": {
                            "content": issue["project"]["name"] if issue.get("project") else ""
                        }
                    }
                ]
            },

            "Estado": {
                "rich_text": [
                    {
                        "text": {
                            "content": issue["state"]["name"] if issue.get("state") else ""
                        }
                    }
                ]
            },

            "Descripcion": {
                "rich_text": [
                    {
                        "text": {
                            "content": issue["description"][:1000] if issue.get("description") else ""
                        }
                    }
                ]
            },

            "Due Date": {
                "date": {
                    "start": issue["dueDate"]
                } if issue.get("dueDate") else None
            }

        }
    }

    url = "https://api.notion.com/v1/pages"

    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    print(response.status_code)

    if response.status_code != 200:
        print(response.text)
