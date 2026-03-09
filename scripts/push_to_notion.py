import requests
import os
import json

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("BI_INITIATIVES_DB")

# -------------------------
# Linear API query
# -------------------------

query = """
{
  issues(first: 50) {
    nodes {
      id
      title
      description
      dueDate
      state {
        name
      }
      team {
        name
      }
      project {
        name
      }
      labels {
        nodes {
          name
        }
      }
    }
  }
}
"""

headers_linear = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json"
}

response = requests.post(
    "https://api.linear.app/graphql",
    json={"query": query},
    headers=headers_linear
)

data = response.json()

issues = data["data"]["issues"]["nodes"]

print("Issues fetched:", len(issues))

# -------------------------
# Notion headers
# -------------------------

headers_notion = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# -------------------------
# Send to Notion
# -------------------------

for issue in issues:

    title = issue["title"]

    team = issue["team"]["name"] if issue.get("team") else ""
    project = issue["project"]["name"] if issue.get("project") else ""
    status = issue["state"]["name"] if issue.get("state") else ""
    description = issue["description"] if issue.get("description") else ""
    due_date = issue["dueDate"]

    payload = {
        "parent": { "database_id": DATABASE_ID },

        "properties": {

            "Nombre": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },

            "Team": {
                "rich_text": [
                    {
                        "text": {
                            "content": team
                        }
                    }
                ]
            },

            "Proyecto": {
                "rich_text": [
                    {
                        "text": {
                            "content": project
                        }
                    }
                ]
            },

            "Estado": {
                "rich_text": [
                    {
                        "text": {
                            "content": status
                        }
                    }
                ]
            },

            "Descripcion": {
                "rich_text": [
                    {
                        "text": {
                            "content": description[:1000]
                        }
                    }
                ]
            }

        }
    }

    if due_date:
        payload["properties"]["Due Date"] = {
            "date": {
                "start": due_date
            }
        }

    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers_notion,
        json=payload
    )

    print("Notion status:", response.status_code)

    if response.status_code != 200:
        print(response.text)
