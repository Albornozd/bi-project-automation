import os
import requests
import json

# Variables de entorno
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_ID = os.getenv("BI_INITIATIVES_DB")

if not LINEAR_API_KEY or not NOTION_API_KEY or not NOTION_DB_ID:
    raise ValueError("Asegúrate de definir LINEAR_API_KEY, NOTION_API_KEY y BI_INITIATIVES_DB en los secrets.")

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
          state { name }
          assignee { name }
          dueDate
          labels { nodes { name } }
          project { name }
          team { name }
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

def find_page(linear_id):
    """Busca si la issue ya existe en Notion usando Linear ID"""
    query_url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    filter_payload = {
        "filter": {
            "property": "Linear ID",
            "rich_text": {"equals": linear_id}
        }
    }
    response = requests.post(query_url, headers=notion_headers, json=filter_payload)
    if response.status_code != 200:
        print(f"Notion query failed. Full response: {response.json()}")
        return None
    results = response.json().get("results")
    if results:
        return results[0]["id"]
    return None

def upsert_notion(issue):
    linear_id = issue["id"]
    page_id = find_page(linear_id)
    labels = classify_labels(issue.get("labels", {}).get("nodes", []))

    properties = {
        "Linear ID": {"rich_text": [{"text": {"content": linear_id}}]},
        "Nombre": {"title": [{"text": {"content": issue.get("title","")}}]},
        "Descripcion": {"rich_text": [{"text": {"content": issue.get("description","")}}]},
        "Estado": {"select": {"name": issue.get("state", {}).get("name","Unknown")}},
        "Owner": {"rich_text": [{"text": {"content": (issue.get("assignee") or {}).get("name","")}}]},
        "Due Date": {"date": {"start": issue.get("dueDate")}},
        "Proyecto": {"rich_text": [{"text": {"content": (issue.get("project") or {}).get("name","")}}]},
        "Team": {"rich_text": [{"text": {"content": (issue.get("team") or {}).get("name","")}}]},
        "Departamento": {"select": {"name": labels["Departamento"]}} if labels["Departamento"] else {},
        "Sociedad": {"select": {"name": labels["Sociedad"]}} if labels["Sociedad"] else {},
        "Esfuerzo": {"select": {"name": labels["Esfuerzo"]}} if labels["Esfuerzo"] else {},
        "Impacto": {"select": {"name": labels["Impacto"]}} if labels["Impacto"] else {},
        "Prioridad": {"select": {"name": labels["Prioridad"]}} if labels["Prioridad"] else {},
        "Tipo Proyecto": {"select": {"name": labels["Tipo Proyecto"]}} if labels["Tipo Proyecto"] else {},
        "Tipo Trabajo": {"select": {"name": labels["Tipo Trabajo"]}} if labels["Tipo Trabajo"] else {},
    }
    properties = {k:v for k,v in properties.items() if v}  # eliminar vacíos

    payload = {"properties": properties}
    if page_id:
        # Actualizar página existente
        response = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=notion_headers, json=payload)
        action = "Actualizada"
    else:
        # Crear nueva página
        payload["parent"] = {"database_id": NOTION_DB_ID}
        response = requests.post("https://api.notion.com/v1/pages", headers=notion_headers, json=payload)
        action = "Creada"

    # 🔹 Imprimir payload para depuración
    print(f"\nPayload enviado a Notion ({action}):")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    try:
        response.raise_for_status()
        print(f"{action} página en Notion: {issue.get('title')}")
    except requests.exceptions.HTTPError:
        print(f"Error al procesar {issue.get('title')}: {response.status_code} {response.text}")

def main():
    issues = get_linear_issues()
    print(f"Issues fetched: {len(issues)}")
    for issue in issues:
        upsert_notion(issue)

if __name__ == "__main__":
    main()
