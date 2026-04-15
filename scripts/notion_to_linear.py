import os
import requests
from datetime import datetime

# ==============================
# ENV VARIABLES
# ==============================
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_ID = os.getenv("REQUESTS_BI", "").replace("-", "")
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
# HELPERS SAFE GETTERS
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

def get_date(prop):
    try:
        return prop["date"]["start"]
    except:
        return None

def get_people(prop):
    try:
        return prop["people"][0]["id"]
    except:
        return None

# ==============================
# NOTION QUERY
# ==============================
def get_tasks_to_plan():

    payload = {
        "filter": {
            "property": "Planificar",
            "checkbox": {"equals": True}
        }
    }

    res = requests.post(NOTION_QUERY_URL, headers=NOTION_HEADERS, json=payload)

    if res.status_code != 200:
        print("❌ Error Notion Query:", res.text)
        raise Exception("Notion query failed")

    return res.json().get("results", [])

# ==============================
# CREATE LINEAR ISSUE
# ==============================
def create_linear_issue(task):

    props = task["properties"]

    title = get_title(props.get("Título", {}))
    description = get_text(props.get("Notas de Implementación", {}))

    due_date = get_date(props.get("Due Date", {}))
    owner = get_people(props.get("Owner", {}))

    labels = []

    label_fields = [
        "Departamento",
        "Sociedad",
        "Prioridad",
        "Impacto Negocio",
        "Esfuerzo Estimado",
        "Tipo de Proyecto",
        "Tipo de Trabajo"
    ]

    for field in label_fields:
        val = get_select(props.get(field, {}))
        if val:
            labels.append(val)

    query = """
    mutation CreateIssue($input: IssueCreateInput!) {
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
            "description": description,
            "teamId": LINEAR_TEAM_ID,
            "projectId": LINEAR_PROJECT_ID,
            "labelNames": labels if labels else None,
            "dueDate": due_date,
            "assigneeId": owner
        }
    }

    res = requests.post(
        LINEAR_URL,
        headers=LINEAR_HEADERS,
        json={"query": query, "variables": variables}
    )

    if res.status_code != 200:
        print("❌ Linear error:", res.text)
        raise Exception("Linear creation failed")

    return res.json()["data"]["issueCreate"]["issue"]

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
                    {"text": {"content": linear_issue["id"]}}
                ]
            }
        }
    }

    res = requests.patch(
        f"{NOTION_PAGE_URL}/{page_id}",
        headers=NOTION_HEADERS,
        json=payload
    )

    if res.status_code != 200:
        print("❌ Notion update error:", res.text)
        raise Exception("Notion update failed")

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

        props = task["properties"]
        page_id = task["id"]

        already_created = get_checkbox(props.get("Issue Creado", {}))
        linear_id = get_text(props.get("Linear ID", {}))

        # 🔁 evitar duplicados
        if already_created or linear_id:
            skipped += 1
            continue

        try:
            issue = create_linear_issue(task)
            update_notion_page(page_id, issue)

            print(f"✅ Created: {issue['identifier']}")
            created += 1

        except Exception as e:
            print(f"❌ Error en task {page_id}: {str(e)}")

    print("================================")
    print(f"✅ Created: {created}")
    print(f"⏭️ Skipped: {skipped}")
    print("================================")


if __name__ == "__main__":
    main()

    print("✅ Sync completado")


if __name__ == "__main__":
    main()
