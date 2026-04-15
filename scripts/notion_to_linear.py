import os
import requests

# ==============================
# ENV VARIABLES
# ==============================
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_ID = os.getenv("REQUESTS_BI")
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")

LINEAR_TEAM_ID = os.getenv("LINEAR_TEAM_JOYERIASUAREZ")
LINEAR_PROJECT_ID = os.getenv("LINEAR_BIREQUESTS_GRUPOSUAREZ")

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
        return prop["title"][0]["text"]["content"].strip()
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
# VALIDATE ENV
# ==============================
def validate_env():
    required = {
        "NOTION_API_KEY": NOTION_API_KEY,
        "REQUESTS_BI": NOTION_DB_ID,
        "LINEAR_API_KEY": LINEAR_API_KEY,
        "LINEAR_TEAM_ID": LINEAR_TEAM_ID,
        "LINEAR_PROJECT_ID": LINEAR_PROJECT_ID
    }

    for k, v in required.items():
        if not v:
            raise Exception(f"❌ Missing env var: {k}")

    print("✅ Variables de entorno OK")

# ==============================
# GET LABEL IDS
# ==============================
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

    res = requests.post(LINEAR_URL, headers=LINEAR_HEADERS, json={"query": query})

    data = res.json()["data"]["issueLabels"]["nodes"]

    return {l["name"]: l["id"] for l in data}

# ==============================
# GET TASKS FROM NOTION
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
        print(res.text)
        raise Exception("Error querying Notion")

    return res.json().get("results", [])

# ==============================
# CREATE ISSUE IN LINEAR
# ==============================
def create_linear_issue(task, label_map):

    props = task["properties"]

    title = get_title(props.get("Título"))
    description = get_text(props.get("Notas de Implementación"))

    if not title:
        print("⏭️ Skip: título vacío")
        return None

    label_fields = [
        "Departamento",
        "Sociedad",
        "Prioridad",
        "Impacto Negocio",
        "Esfuerzo Estimado"
    ]

    label_ids = []

    for f in label_fields:
        val = get_select(props.get(f))
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

    if "errors" in data:
        print("❌ Linear error:", data["errors"])
        raise Exception("Linear creation failed")

    return data["data"]["issueCreate"]["issue"]

# ==============================
# UPDATE NOTION
# ==============================
def update_notion_page(page_id, linear_issue):

    linear_id = linear_issue["id"]
    linear_identifier = linear_issue["identifier"]

    payload = {
        "properties": {
            "Planificar": {"checkbox": False},
            "Issue Creado": {"checkbox": True},
            "Linear ID": {
                "rich_text": [
                    {"text": {"content": linear_identifier}}
                ]
            }
        }
    }

    url = f"{NOTION_PAGE_URL}/{page_id}"

    res = requests.patch(url, headers=NOTION_HEADERS, json=payload)

    if res.status_code != 200:
        print("❌ Error actualizando Notion:")
        print(res.text)
        raise Exception("Error updating Notion")

# ==============================
# MAIN
# ==============================
def main():

    print("🔄 Sync Notion → Linear iniciado")

    validate_env()

    tasks = get_tasks_to_plan()
    print(f"📥 Tasks found: {len(tasks)}")

    label_map = get_linear_labels()

    created = 0
    skipped = 0

    for task in tasks:

        try:
            props = task["properties"]

            # 🚫 evitar duplicados
            if props.get("Issue Creado", {}).get("checkbox"):
                print("⏭️ Ya creado → skip")
                skipped += 1
                continue

            page_id = task["id"]

            issue = create_linear_issue(task, label_map)

            if issue:
                update_notion_page(page_id, issue)
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

    print("✅ Sync completado")


if __name__ == "__main__":
    main()
