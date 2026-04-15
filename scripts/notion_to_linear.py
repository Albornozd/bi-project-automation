import os
import requests

# ==============================
# ENV VARIABLES
# ==============================
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_ID = os.getenv("REQUESTS_BI")
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
# HELPERS NOTION
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

def get_checkbox(prop):
    try:
        return prop["checkbox"]
    except:
        return False


# ==============================
# GET TASKS FROM NOTION
# ==============================
def get_tasks_to_plan():
    payload = {
        "filter": {
            "property": "Planificar",
            "checkbox": {
                "equals": True
            }
        }
    }

    response = requests.post(NOTION_QUERY_URL, headers=NOTION_HEADERS, json=payload)

    if response.status_code != 200:
        print("❌ ERROR NOTION QUERY")
        print(response.text)
        raise Exception("Error querying Notion")

    return response.json().get("results", [])


# ==============================
# LINEAR ISSUE CREATION
# ==============================
def create_linear_issue(task):

    props = task["properties"]

    # ==========================
    # TITLE + DESCRIPTION
    # ==========================
    title = get_title(props.get("Título", {}))
    description = get_text(props.get("Notas de Implementación", {}))

    # ==========================
    # LABEL MAPPING (NOTION → LINEAR)
    # ==========================
    label_fields = [
        "Departamento",
        "Sociedad",
        "Prioridad",
        "Impacto Negocio",
        "Esfuerzo Estimado"
    ]

    labels = []

    for field in label_fields:
        value = get_select(props.get(field, {}))
        if value:
            labels.append(value)

    # ==========================
    # TEAM / PROJECT VALIDATION
    # ==========================
    if not LINEAR_TEAM_ID or not LINEAR_PROJECT_ID:
        raise Exception("Missing LINEAR_TEAM_ID or LINEAR_PROJECT_ID")

    # ==========================
    # GRAPHQL MUTATION
    # ==========================
    mutation = """
    mutation ($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        issue {
          id
          identifier
        }
      }
    }
    """

    variables = {
        "input": {
            "title": title,
            "description": description if description else "",
            "teamId": LINEAR_TEAM_ID,
            "projectId": LINEAR_PROJECT_ID,
            "labelNames": labels  # ⚠️ SI TU WORKSPACE NO SOPORTA labelNames, CAMBIA A labelIds
        }
    }

    response = requests.post(
        LINEAR_URL,
        headers=LINEAR_HEADERS,
        json={"query": mutation, "variables": variables}
    )

    if response.status_code != 200:
        print("❌ ERROR LINEAR")
        print(response.text)
        return None

    data = response.json()

    if "errors" in data:
        print("❌ Linear error:", data["errors"])
        return None

    return data["data"]["issueCreate"]["issue"]


# ==============================
# UPDATE NOTION
# ==============================
def update_notion_page(page_id, linear_issue):

    payload = {
        "properties": {
            "Planificar": {"checkbox": False},
            "Issue Creado": {"checkbox": True},
            "Linear ID": {
                "rich_text": [
                    {"text": {"content": linear_issue["identifier"]}}
                ]
            }
        }
    }

    url = f"{NOTION_PAGE_URL}/{page_id}"

    response = requests.patch(url, headers=NOTION_HEADERS, json=payload)

    if response.status_code != 200:
        print("❌ ERROR ACTUALIZANDO NOTION")
        print(response.text)
        return False

    return True


# ==============================
# MAIN
# ==============================
def main():

    print("🔄 Sync Notion → Linear iniciado")

    tasks = get_tasks_to_plan()

    print(f"📥 Tasks found: {len(tasks)}")

    created = 0
    skipped = 0

    for task in tasks:

        page_id = task["id"]
        props = task["properties"]

        issue_creado = get_checkbox(props.get("Issue Creado", {}))
        linear_id = get_title(props.get("Linear ID", {}))

        # 🚫 Evitar duplicados
        if issue_creado or linear_id:
            skipped += 1
            continue

        issue = create_linear_issue(task)

        if not issue:
            continue

        updated = update_notion_page(page_id, issue)

        if updated:
            created += 1
            print(f"✅ Created: {issue['identifier']}")

    print("================================")
    print(f"✅ Created: {created}")
    print(f"⏭️ Skipped: {skipped}")
    print("================================")
    print("✅ Sync completado")


if __name__ == "__main__":
    main()
