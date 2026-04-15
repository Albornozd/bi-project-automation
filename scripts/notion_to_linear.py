import os
import requests

# =========================
# ENV
# =========================
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_ID = os.getenv("REQUESTS_BI")

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
LINEAR_TEAM_ID = os.getenv("LINEAR_TEAM_ID")
LINEAR_PROJECT_ID = os.getenv("LINEAR_PROJECT_ID")

# =========================
# URLS
# =========================
NOTION_QUERY_URL = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
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
# HELPERS SAFE
# =========================
def get_title(prop):
    try:
        return prop.get("title", [{}])[0].get("text", {}).get("content", "")
    except:
        return ""

def get_text(prop):
    try:
        return prop.get("rich_text", [{}])[0].get("text", {}).get("content", "")
    except:
        return ""

def get_select(prop):
    try:
        return prop.get("select", {}).get("name")
    except:
        return None


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

    if r.status_code != 200:
        print("❌ Notion error:", r.text)
        raise Exception("Notion query failed")

    return r.json().get("results", [])


# =========================
# MAP LABELS
# =========================
def build_labels(props):

    fields = [
        "Departamento",
        "Sociedad",
        "Prioridad",
        "Impacto Negocio",
        "Esfuerzo Estimado"
    ]

    labels = []

    for f in fields:
        val = get_select(props.get(f))
        if val:
            labels.append(val)

    return labels


# =========================
# CREATE LINEAR ISSUE
# =========================
def create_issue(task):

    props = task["properties"]

    title = get_title(props.get("Título"))
    description = get_text(props.get("Notas de Implementación"))

    if not title or title.strip() == "":
        print(f"⚠️ Skip (sin título) {task['id']}")
        return None

    if not LINEAR_TEAM_ID or not LINEAR_PROJECT_ID:
        raise Exception("Missing LINEAR_TEAM_ID or LINEAR_PROJECT_ID")

    labels = build_labels(props)

    query = """
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
            "teamId": LINEAR_TEAM_ID,
            "projectId": LINEAR_PROJECT_ID,
            "labelIds": labels
        }
    }

    r = requests.post(
        LINEAR_URL,
        headers=LINEAR_HEADERS,
        json={"query": query, "variables": variables}
    )

    data = r.json()

    if r.status_code != 200 or "errors" in data:
        print("❌ Linear error:", data)
        return None

    return data["data"]["issueCreate"]["issue"]


# =========================
# MAIN
# =========================
def main():

    print("🔄 Sync Notion → Linear iniciado")

    tasks = get_tasks()

    print(f"📥 Tasks found: {len(tasks)}")

    created = 0
    skipped = 0

    for task in tasks:

        try:
            issue = create_issue(task)

            if issue:
                print(f"✅ Created: {issue['identifier']}")
                created += 1
            else:
                skipped += 1

        except Exception as e:
            print(f"❌ Error en task {task['id']}: {e}")
            skipped += 1

    print("================================")
    print(f"Created: {created}")
    print(f"Skipped: {skipped}")
    print("================================")


if __name__ == "__main__":
    main()
