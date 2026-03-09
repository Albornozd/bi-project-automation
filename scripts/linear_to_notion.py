import os
import requests

# Variables de entorno
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_ID = os.getenv("BI_INITIATIVES_DB")

# Headers Linear
linear_headers = {
    "Authorization": f"Bearer {LINEAR_API_KEY}",
    "Content-Type": "application/json"
}

# Headers Notion
notion_headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# Diccionarios para mapear labels
departamento = ["Administración","BI","IT","Finanzas","Logística","RRHH","Producto","Digital","Retail","Marketing","Postventa","Gemología","Diseño","Producción (Fabricación)","Proyecto FABRIC"]
sociedad = ["Aristocrazy","Suarez","Grupo"]
esfuerzo = ["XL","L","M","S"]
impacto = ["Alto","Medio","Bajo"]
prioridad = ["Alta","Media","Baja"]
tipo_proyecto = ["Analysis","Dashboard","Data Model","Data Pipeline","Machine Learning"]
tipo_trabajo = ["Análisis (Analysis)","Cambio (Change)","Funcionalidad (Feature)","Mejora (Improvement)"]

def get_linear_issues():
    url = "https://api.linear.app/graphql"
    query = """
    query {
      issues {
        nodes {
          id
          title
          description
          state {
            name
          }
          assignee {
            name
          }
          dueDate
          labels {
            nodes {
              name
            }
          }
          project {
            name
          }
          team {
            name
          }
        }
      }
    }
    """
    response = requests.post(url, json={"query": query}, headers=linear_headers)
    response.raise_for_status()
    data = response.json()
    return data["data"]["issues"]["nodes"]

def classify_labels(labels):
    groups = {
        "Departamento": None,
        "Sociedad": None,
        "Esfuerzo": None,
        "Impacto": None,
        "Prioridad": None,
        "Tipo Proyecto": None,
        "Tipo Trabajo": None
    }
    for label in labels:
        name = label["name"]
        if name in departamento:
            groups["Departamento"] = name
        elif name in sociedad:
            groups["Sociedad"] = name
        elif name in esfuerzo:
            groups["Esfuerzo"] = name
        elif name in impacto:
            groups["Impacto"] = name
        elif name in prioridad:
            groups["Prioridad"] = name
        elif name in tipo_proyecto:
            groups["Tipo Proyecto"] = name
        elif name in tipo_trabajo:
            groups["Tipo Trabajo"] = name
    return groups

def create_notion_page(issue):
    labels = classify_labels(issue.get("labels", {}).get("nodes", []))
    properties = {
        "Title": {
            "title": [{"text": {"content": issue.get("title") or ""}}]
        },
        "Description": {
            "rich_text": [{"text": {"content": issue.get("description") or ""}}]
        },
        "Estado": {"select": {"name": issue.get("state", {}).get("name") or "Unknown"}},
        "Responsable": {"rich_text": [{"text": {"content": issue.get("assignee", {}).get("name") or ""}}]},
        "Due Date": {"date": {"start": issue.get("dueDate")}},
        "Proyecto": {"rich_text": [{"text": {"content": issue.get("project", {}).get("name") or ""}}]},
        "Team": {"rich_text": [{"text": {"content": issue.get("team", {}).get("name") or ""}}]},
        "Departamento": {"select": {"name": labels["Departamento"]}} if labels["Departamento"] else {},
        "Sociedad": {"select": {"name": labels["Sociedad"]}} if labels["Sociedad"] else {},
        "Esfuerzo": {"select": {"name": labels["Esfuerzo"]}} if labels["Esfuerzo"] else {},
        "Impacto": {"select": {"name": labels["Impacto"]}} if labels["Impacto"] else {},
        "Prioridad": {"select": {"name": labels["Prioridad"]}} if labels["Prioridad"] else {},
        "Tipo Proyecto": {"select": {"name": labels["Tipo Proyecto"]}} if labels["Tipo Proyecto"] else {},
        "Tipo Trabajo": {"select": {"name": labels["Tipo Trabajo"]}} if labels["Tipo Trabajo"] else {},
    }
    # Limpiar propiedades vacías
    properties = {k:v for k,v in properties.items() if v}

    payload = {"parent": {"database_id": NOTION_DB_ID}, "properties": properties}
    response = requests.post("https://api.notion.com/v1/pages", headers=notion_headers, json=payload)
    response.raise_for_status()
    print(f"Página creada en Notion: {issue.get('title')}")

def main():
    issues = get_linear_issues()
    for issue in issues:
        create_notion_page(issue)

if __name__ == "__main__":
    main()
