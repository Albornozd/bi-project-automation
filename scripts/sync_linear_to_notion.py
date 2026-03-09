import os
import requests

LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("BI_INITIATIVES_DB")

LINEAR_URL = "https://api.linear.app/graphql"
NOTION_URL = "https://api.notion.com/v1/pages"

LINEAR_HEADERS = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json"
}

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

LABEL_MAPPING = {
    "Sociedad": ["Aristocrazy", "Suarez", "Grupo"],
    "Esfuerzo": ["XL", "L", "M", "S"],
    "Impacto": ["Alto", "Medio", "Bajo"],
    "Prioridad": ["Alta", "Media", "Baja"],
    "Tipo de Proyecto": ["Dashboard", "Data model", "Data Pipeline", "Analysis"],
    "Tipo de Trabajo": ["Funcionalidad (Feature)", "Mejora (Improvement)", "Cambio (Change)"]
}


def validate_env():
    for key, value in {
        "LINEAR_API_KEY": LINEAR_API_KEY,
        "NOTION_API_KEY": NOTION_API_KEY,
        "BI_INITIATIVES_DB": NOTION_DATABASE_ID
    }.items():
        if not value:
            raise Exception(f"Missing environment variable: {key}")
    print("Environment variables validated")


def get_linear_issues():
    query = """
    {
      issues(first: 50) {
        nodes {
          id
          title
          description
          state { name }
          team { name }
          project { name }
          assignee { name }
          dueDate
          labels(first:10) { nodes { name } }
        }
      }
    }
    """
    resp = requests.post(LINEAR_URL, headers=LINEAR_HEADERS, json={"query": query})
    resp.raise_for_status()
    return resp.json()["data"]["issues"]["nodes"]


def map_label_to_field(label_nodes, field_name):
    for label in label_nodes:
        name = label.get("name")
        if name in LABEL_MAPPING.get(field_name, []):
            return name
    return "None"


def create_notion_page(issue):
    title = issue.get("title") or "Sin título"
    estado = issue.get("state", {}).get("name") or "Backlog"
    team = issue.get("team", {}).get("name") or "General"
    proyecto = issue.get("project", {}).get("name") or "General"
    owner = issue.get("assignee", {}).get("name") if issue.get("assignee") else ""
    due_date = issue.get("dueDate") or None
    descripcion = issue.get("description") or ""
    labels = issue.get("labels", {}).get("nodes", [])

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Nombre": {"title": [{"text": {"content": title}}]},
            "Descripcion": {"rich_text": [{"text": {"content": descripcion}}]},
            "Owner": {"rich_text": [{"text": {"content": owner}}]},
            "Estado": {"status": {"name": estado}},
            "Proyecto": {"select": {"name": proyecto or "None"}},
            "Team": {"select": {"name": team or "None"}},
            "Departamento": {"multi_select": [{"name": "BI"}]},
            "Sociedad": {"select": {"name": map_label_to_field(labels, "Sociedad")}},
            "Prioridad": {"select": {"name": map_label_to_field(labels, "Prioridad")}},
            "Impacto": {"select": {"name": map_label_to_field(labels, "Impacto")}},
            "Esfuerzo": {"select": {"name": map_label_to_field(labels, "Esfuerzo")}},
            "Tipo de Trabajo": {"select": {"name": map_label_to_field(labels, "Tipo de Trabajo")}},
            "Tipo de Proyecto": {"select": {"name": map_label_to_field(labels, "Tipo de Proyecto")}}
        }
    }

    # Solo agregamos Due Date si existe
    if due_date:
        payload["properties"]["Due Date"] = {"date": {"start": due_date}}

    response = requests.post(NOTION_URL, headers=NOTION_HEADERS, json=payload)
    if response.status_code != 200:
        print("Error creando tarea en Notion:")
        print(response.text)
    else:
        print(f"Tarea creada en Notion: {title}")


def main():
    validate_env()
    issues = get_linear_issues()
    print(f"Issues encontrados en Linear: {len(issues)}")
    for issue in issues:
        create_notion_page(issue)


if __name__ == "__main__":
    main()
