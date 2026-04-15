import os
import requests

# ==============================
# ENV VARIABLES
# ==============================
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_ID = os.getenv("REQUESTS_BI")  # 👈 AJUSTADO
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")

LINEAR_TEAM_ID = os.getenv("LINEAR_TEAM_ID")
LINEAR_PROJECT_ID = os.getenv("LINEAR_PROJECT_ID")

# ==============================
# URLS
# ==============================
NOTION_QUERY_URL = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
NOTION_PAGE_URL = "https://api.notion.com/v1/pages"
LINEAR_URL = "https://api.linear.app/graphql"

# ==============================
# HEADERS
# ==============================
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

LINEAR_HEADERS = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json"
}

# ==============================
# HELPERS
# ==============================
def get_title(prop):
    try:
        return prop["title"][0]["text"]["content"]
    except:
        return ""

def get_text(prop):
    try:
        return prop["rich_text"][0]["text"]["content"]
    except:
        return ""

def get_select(prop):
    try:
        return prop["select"]["name"]
    except:
        return None

# ==============================
# GET TASKS FROM NOTION
# ==============================
def get_tasks_to_plan():

    payload = {
        "filter": {
            "and": [
                {"property": "Planificar", "checkbox": {"equals": True}},
                {"property": "Issue Creado", "checkbox": {"equals": False}}
            ]
        }
    }

    response = requests.post(NOTION_QUERY_URL, headers=NOTION_HEADERS, json=payload)
    response.raise_for_status()

    return response.json().get("results", [])

# ==============================
# CREATE ISSUE IN LINEAR
# ==============================
def create_linear_issue(task):

    props = task["properties"]

    title = get_title(props["Título"])
    description = get_text(props["Notas de Implementación"])

    labels = []
    for field in [
        "Departamento",
        "Sociedad",
        "Prioridad",
        "Impacto Negocio",
        "Esfuerzo Estimado"
    ]:
        val = get_select(props.get(field))
        if val:
            labels.append(val)

    query = """
    mutation ($title: String!, $description: String, $teamId: String!, $projectId: String, $labels: [String!]) {
      issueCreate(input: {
        title: $title,
        description: $description,
        teamId: $teamId,
        projectId: $projectId,
        labelNames: $labels
      }) {
        issue {
          id
          identifier
        }
      }
    }
    """

    variables = {
        "title": title,
        "description": description,
        "teamId": LINEAR_TEAM_ID,
        "projectId": LINEAR_PROJECT_ID,
        "labels": labels
    }

    response = requests.post(
        LINEAR_URL,
        headers=LINEAR_HEADERS,
        json={"query": query, "variables": variables}
    )

    response.raise_for_status()

    return response.json()["data"]["issueCreate"]["issue"]

# ==============================
# UPDATE NOTION AFTER CREATION
# ==============================
def update_notion_page(page_id, linear_id):

    payload = {
        "properties": {
            "Planificar": {"checkbox": False},
            "Issue Creado": {"checkbox": True},
            "Linear ID": {
                "rich_text": [{"text": {"content": linear_id}}]
            }
        }
    }

    url = f"{NOTION_PAGE_URL}/{page_id}"

    response = requests.patch(url, headers=NOTION_HEADERS, json=payload)
    response.raise_for_status()

# ==============================
# MAIN
# ==============================
def main():

    tasks = get_tasks_to_plan()

    print(f"Tareas encontradas para planificar: {len(tasks)}")

    for task in tasks:

        page_id = task["id"]
        props = task["properties"]

        existing_linear_id = get_text(props.get("Linear ID", {}))

        # 🚫 Evitar duplicados
        if existing_linear_id:
            print("Ya existe en Linear → skip")
            continue

        issue = create_linear_issue(task)

        print(f"Issue creado: {issue['identifier']}")

        update_notion_page(page_id, issue["id"])


if __name__ == "__main__":
    main()
