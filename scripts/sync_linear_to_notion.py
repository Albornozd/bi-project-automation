import os
import requests

LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("BI_INITIATIVES_DB")

LINEAR_URL = "https://api.linear.app/graphql"
NOTION_URL = "https://api.notion.com/v1/pages"
NOTION_QUERY_URL = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"

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


def find_notion_page_by_linear_id(linear_id):

    payload = {
        "filter": {
            "property": "Linear ID",
            "rich_text": {
                "equals": linear_id
            }
        }
    }

    response = requests.post(NOTION_QUERY_URL, headers=NOTION_HEADERS, json=payload)
    response.raise_for_status()

    results = response.json().get("results")

    if results:
        return results[0]["id"]

    return None


def build_payload(issue):

    linear_id = issue["id"]
    title = issue.get("title") or "Sin título"
    estado = issue.get("state", {}).get("name") or "Backlog"
    team = issue.get("team", {}).get("name") or "General"
    proyecto = issue.get("project", {}).get("name") or "General"
    owner = issue.get("assignee", {}).get("name") if issue.get("assignee") else ""
    due_date = issue.get("dueDate") or None
    descripcion = issue.get("description") or ""
    labels = issue.get("labels", {}).get("nodes", [])

    properties = {
        "Nombre": {"title": [{"text": {"content": title}}]},
        "Descripcion": {"rich_text": [{"text": {"content": descripcion}}]},
        "Owner": {"rich_text": [{"text": {"content": owner}}]},
        "Estado": {"status": {"name": estado}},
        "Proyecto": {"select": {"name": proyecto or "None"}},
        "Team": {"select": {"name": team or "None"}},
        "Departamento": {"multi_select": [{"name": "BI"}]},
        "Linear ID": {"rich_text": [{"text": {"content": linear_id}}]},
        "Sociedad": {"select": {"name": map_label_to_field(labels, "Sociedad")}},
        "Prioridad": {"select": {"name": map_label_to_field(labels, "Prioridad")}},
        "Impacto": {"select": {"name": map_label_to_field(labels, "Impacto")}},
        "Esfuerzo": {"select": {"name": map_label_to_field(labels, "Esfuerzo")}},
        "Tipo de Trabajo": {"select": {"name": map_label_to_field(labels, "Tipo de Trabajo")}},
        "Tipo de Proyecto": {"select": {"name": map_label_to_field(labels, "Tipo de Proyecto")}}
    }

    if due_date:
        properties["Due Date"] = {"date": {"start": due_date}}

    return {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties
    }


def create_notion_page(payload, title):

    response = requests.post(NOTION_URL, headers=NOTION_HEADERS, json=payload)

    if response.status_code != 200:
        print("Error creando tarea en Notion:")
        print(response.text)
    else:
        print(f"Tarea creada en Notion: {title}")


def update_notion_page(page_id, payload, title):

    url = f"https://api.notion.com/v1/pages/{page_id}"

    response = requests.patch(
        url,
        headers=NOTION_HEADERS,
        json={"properties": payload["properties"]}
    )

    if response.status_code != 200:
        print("Error actualizando tarea en Notion:")
        print(response.text)
    else:
        print(f"Tarea actualizada en Notion: {title}")


def sync_issue(issue):

    linear_id = issue["id"]
    title = issue.get("title")

    page_id = find_notion_page_by_linear_id(linear_id)

    payload = build_payload(issue)

    if page_id:
        update_notion_page(page_id, payload, title)
    else:
        create_notion_page(payload, title)


def main():

    validate_env()

    issues = get_linear_issues()

    print(f"Issues encontrados en Linear: {len(issues)}")

    for issue in issues:
        sync_issue(issue)


if __name__ == "__main__":
    main()
