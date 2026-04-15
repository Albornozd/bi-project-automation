import os
import requests

# =========================
# ENV
# =========================
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_ID = os.getenv("REQUESTS_BI")
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")

TEAM_NAME = "JoyeriaSuarez"
PROJECT_NAME = "BI Requests - Grupo Suarez"

# =========================
# URLS
# =========================
NOTION_QUERY_URL = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
NOTION_PAGE_URL = "https://api.notion.com/v1/pages"
LINEAR_URL = "https://api.linear.app/graphql"

# =========================
# HEADERS
# =========================
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

LINEAR_HEADERS = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json"
}

# =========================
# LINEAR HELPERS
# =========================
def graphql(query, variables=None):
    response = requests.post(
        LINEAR_URL,
        headers=LINEAR_HEADERS,
        json={"query": query, "variables": variables or {}}
    )
    response.raise_for_status()
    data = response.json()

    if "errors" in data:
        raise Exception(data["errors"])

    return data["data"]


def get_team_id():
    query = """
    {
      teams {
        nodes {
          id
          name
        }
      }
    }
    """
    data = graphql(query)
    for t in data["teams"]["nodes"]:
        if t["name"] == TEAM_NAME:
            return t["id"]
    raise Exception("Team not found")


def get_project_id():
    query = """
    {
      projects {
        nodes {
          id
          name
        }
      }
    }
    """
    data = graphql(query)
    for p in data["projects"]["nodes"]:
        if p["name"] == PROJECT_NAME:
            return p["id"]
    raise Exception("Project not found")


# =========================
# NOTION HELPERS
# =========================
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


# =========================
# NOTION QUERY
# =========================
def get_tasks():
    payload = {
        "filter": {
            "property": "Planificar",
            "checkbox": {"equals": True}
        }
    }

    r = requests.post(NOTION_QUERY_URL, headers=NOTION_HEADERS, json=payload)
    r.raise_for_status()
    return r.json()["results"]


# =========================
# CREATE LINEAR ISSUE
# =========================
def create_issue(task, team_id, project_id):

    props = task["properties"]

    title = get_title(props["Título"])
    description = get_text(props["Notas de Implementación"])

    labels = []
    label_fields = [
        "Departamento",
        "Sociedad",
        "Prioridad",
        "Impacto Negocio",
        "Esfuerzo Estimado"
    ]

    for f in label_fields:
        val = get_select(props.get(f, {}))
        if val:
            labels.append(val)

    mutation = """
    mutation IssueCreate($input: IssueCreateInput!) {
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
            "teamId": team_id,
            "projectId": project_id,
            "labelNames": labels
        }
    }

    r = requests.post(
        LINEAR_URL,
        headers=LINEAR_HEADERS,
        json={"query": mutation, "variables": variables}
    )

    data = r.json()

    if "errors" in data:
        raise Exception(data["errors"])

    return data["data"]["issueCreate"]["issue"]


# =========================
# UPDATE NOTION
# =========================
def update_notion(page_id, issue_id):

    payload = {
        "properties": {
            "Planificar": {"checkbox": False},
            "Issue Creado": {"checkbox": True},
            "Linear ID": {
                "rich_text": [{"text": {"content": issue_id}}]
            }
        }
    }

    r = requests.patch(f"{NOTION_PAGE_URL}/{page_id}",
                       headers=NOTION_HEADERS,
                       json=payload)

    r.raise_for_status()


# =========================
# MAIN
# =========================
def main():

    print("🔄 Sync Notion → Linear iniciado")

    team_id = get_team_id()
    project_id = get_project_id()

    tasks = get_tasks()

    print(f"📥 Tasks found: {len(tasks)}")

    created = 0
    skipped = 0

    for task in tasks:

        props = task["properties"]

        if get_checkbox(props.get("Issue Creado", {})):
            skipped += 1
            continue

        try:
            issue = create_issue(task, team_id, project_id)
            update_notion(task["id"], issue["id"])
            created += 1
            print(f"✅ Created: {issue['identifier']}")

        except Exception as e:
            print(f"❌ Error en task {task['id']}: {e}")

    print("================================")
    print(f"✅ Created: {created}")
    print(f"⏭️ Skipped: {skipped}")
    print("================================")


if __name__ == "__main__":
    main()
