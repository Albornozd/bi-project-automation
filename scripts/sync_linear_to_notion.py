import os
import requests
import json

# --------------------------
# Configuración
# --------------------------
LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
LINEAR_GRAPHQL_URL = "https://api.linear.app/graphql"
NOTION_URL = "https://api.notion.com/v1"

HEADERS_LINEAR = {
    "Authorization": f"Bearer {LINEAR_API_KEY}",
    "Content-Type": "application/json"
}

HEADERS_NOTION = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# --------------------------
# Mapping Linear → Notion
# --------------------------
LABEL_MAPPING = {
    "Departamento": {
        "Digital":"Departamento","BI":"Departamento","RRHH":"Departamento","IT":"Departamento",
        "Finanzas":"Departamento","Administración":"Departamento","Logística":"Departamento",
        "Producto":"Departamento","Retail":"Departamento","Marketing":"Departamento",
        "Postventa":"Departamento","Gemología":"Departamento","Relojería":"Departamento",
        "Diseño":"Departamento","Proyecto FABRIC":"Departamento","Producción (Fabricación)":"Departamento"
    },
    "Sociedad": {
        "Aristocrazy":"Sociedad","Suarez":"Sociedad","Grupo":"Sociedad"
    },
    "Esfuerzo Estimado": {
        "XL":"Esfuerzo","L":"Esfuerzo","M":"Esfuerzo","S":"Esfuerzo"
    },
    "Impacto en Negocio": {
        "Alto":"Impacto","Medio":"Impacto","Bajo":"Impacto"
    },
    "Prioridad": {
        "Alta":"Prioridad","Media":"Prioridad","Baja":"Prioridad"
    },
    "Tipo Proyecto": {
        "Dashboard":"Tipo Proyecto","Data model":"Tipo Proyecto","Data Pipeline":"Tipo Proyecto","Analysis":"Tipo Proyecto"
    },
    "Tipo Trabajo": {
        "Funcionalidad (Feature)":"Tipo Trabajo","Mejora (Improvement)":"Tipo Trabajo","Cambio (Change)":"Tipo Trabajo"
    }
}

# --------------------------
# Fetch issues de Linear
# --------------------------
def fetch_linear_issues():
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
          team { name }
          project { name }
          labels { nodes { name } }
        }
      }
    }
    """
    resp = requests.post(LINEAR_GRAPHQL_URL, headers=HEADERS_LINEAR, json={"query": query})
    data = resp.json()
    return data["data"]["issues"]["nodes"]

# --------------------------
# Find page en Notion
# --------------------------
def find_page(linear_id):
    url = f"{NOTION_URL}/databases/{DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": "Linear ID",
            "rich_text": {
                "equals": linear_id
            }
        }
    }

    res = requests.post(url, headers=HEADERS_NOTION, json=payload)
    
    try:
        data = res.json()
    except Exception as e:
        print("Error parsing Notion response:", e)
        print("Response content:", res.text)
        return None

    if "results" not in data:
        print("Notion query failed. Full response:", data)
        return None

    results = data["results"]
    return results[0]["id"] if results else None

# --------------------------
# Transform labels a Notion
# --------------------------
def map_labels(labels):
    mapped = {}
    for label in labels:
        name = label["name"]
        for group, mapping in LABEL_MAPPING.items():
            if name in mapping:
                mapped[mapping[name]] = name
    return mapped

# --------------------------
# Crear o actualizar página
# --------------------------
def upsert_notion(issue):
    linear_id = issue["id"]
    page_id = find_page(linear_id)
    
    # Mapping de campos
    labels_mapped = map_labels(issue.get("labels", {}).get("nodes", []))

    props = {
        "Nombre": {"title":[{"text":{"content":issue.get("title","")}}]},
        "Descripcion": {"rich_text":[{"text":{"content":issue.get("description","")}}]},
        "Estado": {"status":{"name":issue.get("state", {}).get("name","")}},
        "Owner": {"rich_text":[{"text":{"content":issue.get("assignee", {}).get("name","")}}]},
        "Due Date": {"date":{"start":issue.get("dueDate")}},
        "Team": {"rich_text":[{"text":{"content":issue.get("team", {}).get("name","")}}]},
        "Proyecto": {"rich_text":[{"text":{"content":issue.get("project", {}).get("name","")}}]},
    }

    # Agregar labels mapeados
    for k,v in labels_mapped.items():
        props[k] = {"select":{"name":v}}

    if page_id:
        url = f"{NOTION_URL}/pages/{page_id}"
        res = requests.patch(url, headers=HEADERS_NOTION, json={"properties": props})
    else:
        url = f"{NOTION_URL}/pages"
        body = {
            "parent": {"database_id": DATABASE_ID},
            "properties": props
        }
        res = requests.post(url, headers=HEADERS_NOTION, json=body)

    if res.status_code not in [200, 201]:
        print("Notion status:", res.status_code)
        print(res.text)
    else:
        print(f"Notion page synced for Linear ID {linear_id}")

# --------------------------
# Main
# --------------------------
def main():
    issues = fetch_linear_issues()
    print(f"Issues fetched: {len(issues)}")
    for issue in issues:
        upsert_notion(issue)

if __name__ == "__main__":
    main()
