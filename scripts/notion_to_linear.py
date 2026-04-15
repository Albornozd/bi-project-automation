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
# HELPERS
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

# =========================
# LINEAR: GET LABELS
# =========================
def get_linear_labels():
    query = """
    {
      issueLabels {
        nodes {
          id
          name
        }
      }
    }
    """

    res = requests.post(
        LINEAR_URL,
        headers=LINEAR_HEADERS,
        json={"query": query}
    )

    res.raise_for_status()

    labels = res.json()["data"]["issueLabels"]["nodes"]

    return {l["name"]: l["id"] for l in labels}

# =========================
# NOTION QUERY
# =========================
def get_tasks_to_plan():

    payload = {
        "filter": {
            "property": "Planificar",
            "checkbox": {"equals": True}
        }
    }

    res = requests.post(
        NOTION_QUERY_URL,
        headers=NOTION_HEADERS,
        json=payload
    )

    if res.status_code != 200:
        print("❌ ERROR NOTION")
        print(res.text)
        raise Exception("Notion query failed")

    return res.json().get("results", [])

# =========================
# CREATE LINEAR ISSUE
# =========================
def create_linear_issue(task, label_map):

    props = task["properties"]

    title = get_title(props.get("Título"))
    description = get_text(props.get("Notas de Implementación"))

    label_fields = [
        "Departamento",
        "Sociedad",
        "Prioridad",
        "Impacto Negocio",
        "Esfuerzo Estimado"
    ]

    label_ids = []

    for field in label_fields:
        val = get_select(props.get(field))
        if val and val in label_map:
            label_ids.append(label_map[val])

    query = """
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
            "description": description,
            "teamId": LINEAR_TEAM_ID,
            "projectId": LINEAR_PROJECT_ID,
            "labelIds": label_ids
        }
    }

    res = requests.post(
        LINEAR_URL,
        headers=LINEAR_HEADERS,
        json={"query": query, "variables": variables}
    )

    data = res.json()

    if res.status_code != 200 or "errors" in data:
        print("❌ Linear error:", data.get("errors", data))
        return None

    return data["data"]["issueCreate"]["issue"]

# =========================
# UPDATE NOTION
# =========================
def update_notion(task_id, page_id, linear_id):

    url = f"https://api.notion.com/v1/pages/{page_id}"

    payload = {
        "properties": {
            "Planificar": {"checkbox": False},
            "Issue Creado": {"checkbox": True},
            "Linear ID": {
                "rich_text": [{"text": {"content": linear_id}}]
            }
        }
    }

    requests.patch(url, headers=NOTION_HEADERS, json=payload)

# =========================
# MAIN
# =========================
def main():

    print("🔄 Sync Notion → Linear iniciado")

    label_map = get_linear_labels()

    tasks = get_tasks_to_plan()

    print(f"📥 Tasks found: {len(tasks)}")

    created = 0
    skipped = 0

    for task in tasks:

        page_id = task["id"]
        props = task["properties"]

        # evitar duplicados
        if props.get("Issue Creado", {}).get("checkbox"):
            skipped += 1
            continue

        issue = create_linear_issue(task, label_map)

        if issue:
            update_notion(page_id, page_id, issue["id"])
            print(f"✅ Created: {issue['identifier']}")
            created += 1
        else:
            skipped += 1

    print("================================")
    print(f"Created: {created}")
    print(f"Skipped: {skipped}")
    print("================================")

if __name__ == "__main__":
    main()
