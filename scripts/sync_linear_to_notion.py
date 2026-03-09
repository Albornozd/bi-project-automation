import os
import requests
import json

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_ID = os.getenv("BI_INITIATIVES_DB")

if not LINEAR_API_KEY or not NOTION_API_KEY or not NOTION_DB_ID:
    raise ValueError("Debes definir LINEAR_API_KEY, NOTION_API_KEY y BI_INITIATIVES_DB")

linear_headers = {
    "Authorization": f"Bearer {LINEAR_API_KEY}",
    "Content-Type": "application/json"
}

notion_headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

departamento = ["Administración","BI","IT","Finanzas","Logística","RRHH","Producto","Digital","Retail","Marketing","Postventa","Gemología","Diseño","Producción (Fabricación)","Proyecto FABRIC"]
sociedad = ["Aristocrazy","Suarez","Grupo"]
esfuerzo = ["XL","L","M","S"]
impacto = ["Alto","Medio","Bajo"]
prioridad = ["Alta","Media","Baja"]
tipo_proyecto = ["Analysis","Dashboard","Data Model","Data Pipeline","Machine Learning"]
tipo_trabajo = ["Análisis (Analysis)","Cambio (Change)","Funcionalidad (Feature)","Mejora (Improvement)"]

def get_linear_issues():

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

    response = requests.post(
        "https://api.linear.app/graphql",
        headers=linear_headers,
        json={"query": query}
    )

    response.raise_for_status()

    data = response.json()

    issues = data["data"]["issues"]["nodes"]

    print(f"Issues fetched: {len(issues)}")

    return issues


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

    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"

    payload = {
        "filter": {
            "property": "Linear ID",
            "rich_text": {
                "equals": linear_id
            }
        }
    }

    response = requests.post(url, headers=notion_headers, json=payload)

    response.raise_for_status()

    results = response.json()["results"]

    if results:
        return results[0]["id"]

    return None


def upsert_notion(issue):

    linear_id = issue["id"]

    page_id = find_page(linear_id)

    labels = classify_labels(issue.get("labels", {}).get("nodes", []))

    properties = {

        "Linear ID": {"rich_text": [{"text": {"content": linear_id}}]},

        "Nombre": {"title": [{"text": {"content": issue.get("title") or ""}}]},

        "Descripcion": {"rich_text": [{"text": {"content": issue.get("description") or ""}}]},

        "Estado": {"select": {"name": issue.get("state", {}).get("name") or "Unknown"}},

        "Owner": {"rich_text": [{"text": {"content": (issue.get("assignee") or {}).get("name","")}}]},

        "Due Date": {"date": {"start": issue.get("dueDate")}} if issue.get("dueDate") else {},

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

    properties = {k:v for k,v in properties.items() if v}

    payload = {"properties": properties}

    if page_id:

        url = f"https://api.notion.com/v1/pages/{page_id}"

        response = requests.patch(url, headers=notion_headers, json=payload)

        action = "Updated"

    else:

        url = "https://api.notion.com/v1/pages"

        payload["parent"] = {"database_id": NOTION_DB_ID}

        response = requests.post(url, headers=notion_headers, json=payload)

        action = "Created"

    print("\nPayload sent to Notion:")

    print(json.dumps(payload, indent=2, ensure_ascii=False))

    try:

        response.raise_for_status()

        print(f"{action} page: {issue.get('title')}")

    except requests.exceptions.HTTPError:

        print(f"Error processing {issue.get('title')}:")

        print(response.text)


def main():

    issues = get_linear_issues()

    for issue in issues:

        upsert_notion(issue)


if __name__ == "__main__":

    main()
