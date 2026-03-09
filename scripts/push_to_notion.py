import os
import json
import requests

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("BI_INITIATIVES_DB")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

with open("data/linear_issues.json") as f:
    data = json.load(f)

def extract_label(labels, keyword):

    for label in labels:
        if keyword.lower() in label.lower():
            return label

    return None


for issue in data["issues"]:

    labels = issue["labels"]

    departamento = extract_label(labels, "Departamento")
    sociedad = extract_label(labels, "Sociedad")
    esfuerzo = extract_label(labels, "Esfuerzo")
    impacto = extract_label(labels, "Impacto")
    prioridad = extract_label(labels, "Prioridad")
    tipo_proyecto = extract_label(labels, "Tipo de Proyecto")
    tipo_trabajo = extract_label(labels, "Tipo de Trabajo")

    payload = {
        "parent": {"database_id": DATABASE_ID},

        "properties": {

            "Nombre": {
                "title": [{
                    "text": {
                        "content": issue["title"]
                    }
                }]
            },

            "Team": {
                "select": {"name": issue["team"]} if issue["team"] else None
            },

            "Proyecto": {
                "select": {"name": issue["project"]} if issue["project"] else None
            },

            "Estado": {
                "status": {"name": issue["status"]}
            },

            "Due Date": {
                "date": {"start": issue["dueDate"]}
            } if issue["dueDate"] else None,

            "Descripcion": {
                "rich_text": [{
                    "text": {
                        "content": issue["description"] or ""
                    }
                }]
            },

            "Departamento": {
                "select": {"name": departamento}
            } if departamento else None,

            "Sociedad": {
                "select": {"name": sociedad}
            } if sociedad else None,

            "Esfuerzo": {
                "select": {"name": esfuerzo}
            } if esfuerzo else None,

            "Impacto": {
                "select": {"name": impacto}
            } if impacto else None,

            "Prioridad": {
                "select": {"name": prioridad}
            } if prioridad else None,

            "Tipo de Proyecto": {
                "select": {"name": tipo_proyecto}
            } if tipo_proyecto else None,

            "Tipo de Trabajo": {
                "select": {"name": tipo_trabajo}
            } if tipo_trabajo else None

        }
    }

    payload["properties"] = {
        k: v for k, v in payload["properties"].items() if v is not None
    }

    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json=payload
    )

    print(response.status_code)
    print(response.text)

print("Issues pushed to Notion")
