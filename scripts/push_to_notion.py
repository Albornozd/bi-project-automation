import os
import requests

# --------------------
# Configuración
# --------------------
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("BI_INITIATIVES_DB")

# --------------------
# Fetch issues from Linear
# --------------------
query = """
{
  issues(first: 50) {
    nodes {
      id
      title
      description
      dueDate
      state { name }
      team { name }
      project { name }
      labels { nodes { name } }
      assignee { name }
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

issues = response.json()["data"]["issues"]["nodes"]
print("Issues fetched:", len(issues))

# --------------------
# Map labels to Notion fields
# --------------------
def map_labels(labels):
    mapping = {
        "Departamento": "",
        "Sociedad": "",
        "Esfuerzo": "",
        "Impacto": "",
        "Prioridad": "",
        "Tipo de Proyecto": "",
        "Tipo de Trabajo": ""
    }
    for label in labels:
        name = label["name"]
        if name.startswith("Departamento"):
            mapping["Departamento"] = name
        elif name.startswith("Sociedad"):
            mapping["Sociedad"] = name
        elif name.startswith("Esfuerzo"):
            mapping["Esfuerzo"] = name
        elif name.startswith("Impacto"):
            mapping["Impacto"] = name
        elif name.startswith("Prioridad"):
            mapping["Prioridad"] = name
        elif name.startswith("Tipo de Proyecto"):
            mapping["Tipo de Proyecto"] = name
        elif name.startswith("Tipo de Trabajo"):
            mapping["Tipo de Trabajo"] = name
    return mapping

# --------------------
# Push to Notion
# --------------------
headers_notion = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

for issue in issues:
    labels_map = map_labels(issue.get("labels", {}).get("nodes", []))

    properties = {
        "Nombre": {"title": [{"text": {"content": issue["title"]}}]},
        "Team": {"rich_text": [{"text": {"content": issue.get("team", {}).get("name", "")}}]},
        "Proyecto": {"rich_text": [{"text": {"content": issue.get("project", {}).get("name", "")}}]},
        "Estado": {"rich_text": [{"text": {"content": issue.get("state", {}).get("name", "")}}]},
        "Departamento": {"rich_text": [{"text": {"content": labels_map["Departamento"]}}]},
        "Sociedad": {"rich_text": [{"text": {"content": labels_map["Sociedad"]}}]},
        "Prioridad": {"rich_text": [{"text": {"content": labels_map["Prioridad"]}}]},
        "Impacto": {"rich_text": [{"text": {"content": labels_map["Impacto"]}}]},
        "Esfuerzo": {"rich_text": [{"text": {"content": labels_map["Esfuerzo"]}}]},
        "Tipo de Trabajo": {"rich_text": [{"text": {"content": labels_map["Tipo de Trabajo"]}}]},
        "Tipo de Proyecto": {"rich_text": [{"text": {"content": labels_map["Tipo de Proyecto"]}}]},
        "Due Date": {"date": {"start": issue.get("dueDate")}} if issue.get("dueDate") else None,
        "Owner": {"rich_text": [{"text": {"content": issue.get("assignee", {}).get("name", "")}}]},
        "Descripción": {"rich_text": [{"text": {"content": issue.get("description") or ""}}]},
    }

    # Remove None values to avoid errors
    properties = {k: v for k, v in properties.items() if v is not None}

    payload = {"parent": {"database_id": DATABASE_ID}, "properties": properties}

    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers_notion,
        json=payload
    )

    print("Notion status:", response.status_code)
    if response.status_code != 200:
        print(response.text)
