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
# Map labels to Notion select fields
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
        if name == "Departamento":
            mapping["Departamento"] = name
        elif name == "Sociedad":
            mapping["Sociedad"] = name
        elif name == "Esfuerzo Estimado":
            mapping["Esfuerzo"] = name
        elif name == "Impacto en Negocio":
            mapping["Impacto"] = name
        elif name == "Prioridad":
            mapping["Prioridad"] = name
        elif name == "Tipo de Proyecto":
            mapping["Tipo de Proyecto"] = name
        elif name == "Tipo de Trabajo":
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
    assignee_name = issue.get("assignee")["name"] if issue.get("assignee") else ""

    properties = {
        "Nombre": {"title": [{"text": {"content": issue["title"]}}]},
        "Team": {"rich_text": [{"text": {"content": issue.get("team", {}).get("name", "")}}]},
        "Proyecto": {"rich_text": [{"text": {"content": issue.get("project", {}).get("name", "")}}]},
        "Estado": {"status": {"name": issue.get("state", {}).get("name", "Backlog")}},
        "Departamento": {"select": {"name": labels_map["Departamento"] or "No asignado"}},
        "Sociedad": {"select": {"name": labels_map["Sociedad"] or "No asignado"}},
        "Prioridad": {"select": {"name": labels_map["Prioridad"] or "Normal"}},
        "Impacto": {"select": {"name": labels_map["Impacto"] or "Medio"}},
        "Esfuerzo": {"select": {"name": labels_map["Esfuerzo"] or "Medio"}},
        "Tipo de Trabajo": {"select": {"name": labels_map["Tipo de Trabajo"] or "Tarea"}},
        "Tipo de Proyecto": {"select": {"name": labels_map["Tipo de Proyecto"] or "Proyecto"}},
        "Due Date": {"date": {"start": issue.get("dueDate")}} if issue.get("dueDate") else None,
        "Owner": {"rich_text": [{"text": {"content": assignee_name}}]},
        "Resumen Ejecutivo": {"rich_text": [{"text": {"content": issue.get("description") or ""}}]},
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
