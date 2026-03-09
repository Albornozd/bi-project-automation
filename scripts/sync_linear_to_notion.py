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

# Diccionario para mapear labels de Linear a campos de Notion
LABEL_MAPPING = {
    # Sociedad
    "Aristocrazy": ("Sociedad", "Aristocrazy"),
    "Suarez": ("Sociedad", "Suarez"),
    "Grupo": ("Sociedad", "Grupo"),
    # Esfuerzo Estimado
    "XL": ("Esfuerzo", "XL"),
    "L": ("Esfuerzo", "L"),
    "M": ("Esfuerzo", "M"),
    "S": ("Esfuerzo", "S"),
    # Impacto en Negocio
    "Alto": ("Impacto", "Alto"),
    "Medio": ("Impacto", "Medio"),
    "Bajo": ("Impacto", "Bajo"),
    # Prioridad
    "Alta": ("Prioridad", "Alta"),
    "Media": ("Prioridad", "Media"),
    "Baja": ("Prioridad", "Baja"),
    # Tipo Proyecto
    "Dashboard": ("Tipo de Proyecto", "Dashboard"),
    "Data model": ("Tipo de Proyecto", "Data model"),
    "Data Pipeline": ("Tipo de Proyecto", "Data Pipeline"),
    "Analysis": ("Tipo de Proyecto", "Analysis"),
    # Tipo Trabajo
    "Funcionalidad (Feature)": ("Tipo de Trabajo", "Funcionalidad (Feature)"),
    "Mejora (Improvement)": ("Tipo de Trabajo", "Mejora (Improvement)"),
    "Cambio (Change)": ("Tipo de Trabajo", "Cambio (Change)")
}

def validate_env():
    required = {
        "LINEAR_API_KEY": LINEAR_API_KEY,
        "NOTION_API_KEY": NOTION_API_KEY,
        "BI_INITIATIVES_DB": NOTION_DATABASE_ID
    }
    for key, value in required.items():
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
          dueDate
          assignee { name }
          labels(first: 10) { nodes { name } }
        }
      }
    }
    """
    response = requests.post(LINEAR_URL, headers=LINEAR_HEADERS, json={"query": query})
    response.raise_for_status()
    data = response.json()
    return data["data"]["issues"]["nodes"]

def map_labels(labels):
    mapped = {
        "Sociedad": [],
        "Prioridad": [],
        "Impacto": [],
        "Esfuerzo": [],
        "Tipo de Trabajo": [],
        "Tipo de Proyecto": []
    }
    for label_node in labels:
        name = label_node.get("name")
        if name in LABEL_MAPPING:
            field, value = LABEL_MAPPING[name]
            mapped[field].append(value)
    return mapped

def create_notion_page(issue):
    title = issue.get("title", "Sin título")
    estado = issue.get("state", {}).get("name", "Backlog")
    team = issue.get("team", {}).get("name", "General")
    proyecto = issue.get("project", {}).get("name", "General")
    descripcion = issue.get("description", "")
    owner = issue.get("assignee", {}).get("name", "")
    due_date = issue.get("dueDate", None)

    labels = issue.get("labels", {}).get("nodes", [])
    mapped_labels = map_labels(labels)

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Nombre": {
                "title": [{"text": {"content": title}}]
            },
            "Estado": {"status": {"name": estado}},
            "Proyecto": {"select": {"name": proyecto}},
            "Team": {"select": {"name": team}},
            "Departamento": {"multi_select": [{"name": "BI"}]},
            "Descripcion": {"rich_text": [{"text": {"content": descripcion}}]},
            "Owner": {"rich_text": [{"text": {"content": owner}}]},
        }
    }

    # Añadir Due Date si existe
    if due_date:
        payload["properties"]["Due Date"] = {"date": {"start": due_date}}

    # Añadir labels mapeados
    for field, values in mapped_labels.items():
        if values:
            payload["properties"][field] = {"multi_select": [{"name": v} for v in values]}

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
