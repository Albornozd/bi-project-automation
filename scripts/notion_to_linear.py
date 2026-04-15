import os
import requests

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_ID = os.getenv("REQUESTS_BI")
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")

LINEAR_URL = "https://api.linear.app/graphql"
NOTION_QUERY_URL = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
NOTION_PAGE_URL = "https://api.notion.com/v1/pages"

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
# LINEAR HELPERS (IDs dinámicos)
# =========================

def linear_query(query, variables=None):
    res = requests.post(
        LINEAR_URL,
        headers=LINEAR_HEADERS,
        json={"query": query, "variables": variables or {}}
    )
    res.raise_for_status()
    data = res.json()

    if "errors" in data:
        raise Exception(data["errors"])

    return data["data"]


def get_team_id_by_name(name):
    q = """
    query {
      teams {
        nodes { id name }
      }
    }
    """
    data = linear_query(q)
    for t in data["teams"]["nodes"]:
        if t["name"] == name:
            return t["id"]
    raise Exception(f"Team not found: {name}")


def get_project_id_by_name(name):
    q = """
    query {
      projects {
        nodes { id name }
      }
    }
    """
    data = linear_query(q)
    for p in data["projects"]["nodes"]:
        if p["name"] == name:
            return p["id"]
    raise Exception(f"Project not found: {name}")


def get_label_ids():
    q = """
    query {
      issueLabels {
        nodes { id name }
      }
    }
    """
    data = linear_query(q)
    return {l["name"]: l["id"] for l in data["issueLabels"]["nodes"]}


# =========================
# NOTION HELPERS
# =========================

def get_text(prop):
    try:
        return prop["rich_text"][0]["text"]["content"]
    except:
        return ""

def get_title(prop):
    try:
        return prop["title"][0]["text"]["content"]
    except:
        return ""

def get_select(prop):
    try:
        return prop["select"]["name"]
    except:
        return None


def get_checkbox(task, name):
    return task["properties"].get(name, {}).get("checkbox", False)


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

    res = requests.post(NOTION_QUERY_URL, headers=NOTION_HEADERS, json=payload)
    res.raise_for_status()
    return res.json()["results"]


# =========================
# CREATE LINEAR ISSUE
# =========================

def create_issue(task, team_id, project_id, label_map):

    props = task["properties"]

    title = get_text(props.get("Título"))
    description = get_text(props.get("Notas de Implementación"))

    labels = []

    # mapping Notion → Linear labels
    for field in ["Departamento", "Sociedad", "Prioridad", "Impacto Negocio", "Esfuerzo Estimado"]:
        val = get_select(props.get(field))
        if val and val in label_map:
            labels.append(label_map[val])

    mutation = """
    mutation IssueCreate($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        issue { id identifier }
      }
    }
    """

    variables = {
        "input": {
            "title": title,
            "description": description,
            "teamId": team_id,
            "projectId": project_id,
            "labelIds": labels
        }
    }

    res = requests.post(
        LINEAR_URL,
        headers=LINEAR_HEADERS,
        json={"query": mutation, "variables": variables}
    )

    data = res.json()

    if "errors" in data:
        print("❌ Linear error:", data["errors"])
        return None

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

    url = f"{NOTION_PAGE_URL}/{page_id}"

    res = requests.patch(url, headers=NOTION_HEADERS, json=payload)

    if res.status_code != 200:
        print("❌ Notion update error:", res.text)


# =========================
# MAIN
# =========================

def main():

    print("🔄 Sync Notion → Linear iniciado")

    team_id = get_team_id_by_name("JoyeriaSuarez")
    project_id = get_project_id_by_name("BI Requests - Grupo Suarez")
    label_map = get_label_ids()

    tasks = get_tasks()

    print(f"📥 Tasks found: {len(tasks)}")

    for task in tasks:

        if get_checkbox(task, "Issue Creado"):
            continue

        issue = create_issue(task, team_id, project_id, label_map)

        if issue:
            print("✅ Created:", issue["identifier"])
            update_notion(task["id"], issue["id"])
        else:
            print("⏭️ Skipped")

    print("✅ Sync completed")


if __name__ == "__main__":
    main()
