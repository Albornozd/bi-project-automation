import os
import requests

LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")  # Debe ser un UUID válido

if not DATABASE_ID:
    raise ValueError("NOTION_DATABASE_ID no está definido. Revisa tus secrets.")

HEADERS_LINEAR = {"Authorization": f"Bearer {LINEAR_API_KEY}", "Content-Type": "application/json"}
HEADERS_NOTION = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# Fetch issues Linear
def fetch_linear_issues():
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
          team { name }
          project { name }
          labels { nodes { name } }
        }
      }
    }
    """
    resp = requests.post("https://api.linear.app/graphql", headers=HEADERS_LINEAR, json={"query": query})
    resp.raise_for_status()
    return resp.json()["data"]["issues"]["nodes"]

# Find Notion page by Linear ID
def find_page(linear_id):
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": "Linear ID",
            "rich_text": {"equals": linear_id}
        }
    }
    res = requests.post(url, headers=HEADERS_NOTION, json=payload)
    data = res.json()
    if "results" not in data:
        print("Notion query failed. Response:", data)
        return None
    return data["results"][0]["id"] if data["results"] else None

# Map labels Linear -> Notion
def map_labels(labels):
    mapped = {}
    # Aquí va tu mapping existente (Departamento, Sociedad, Esfuerzo, etc.)
    return mapped

# Crear o actualizar página
def upsert_notion(issue):
    linear_id = issue["id"]
    page_id = find_page(linear_id)
    
    props = {
        "Nombre": {"title": [{"text": {"content": issue.get("title","")}}]},
        "Descripcion": {"rich_text": [{"text": {"content": issue.get("description","")}}]},
        "Estado": {"status": {"name": issue.get("state", {}).get("name","")}},
        "Owner": {"rich_text": [{"text": {"content": issue.get("assignee", {}).get("name","") if issue.get("assignee") else ""}}]},
        "Due Date": {"date": {"start": issue.get("dueDate")}},
        "Team": {"rich_text": [{"text": {"content": issue.get("team", {}).get("name","")}}]},
        "Proyecto": {"rich_text": [{"text": {"content": issue.get("project", {}).get("name","")}}]},
        "Linear ID": {"rich_text": [{"text": {"content": linear_id}}]}
    }

    if page_id:
        url = f"https://api.notion.com/v1/pages/{page_id}"
        res = requests.patch(url, headers=HEADERS_NOTION, json={"properties": props})
    else:
        url = "https://api.notion.com/v1/pages"
        body = {"parent": {"database_id": DATABASE_ID}, "properties": props}
        res = requests.post(url, headers=HEADERS_NOTION, json=body)

    if res.status_code not in [200, 201]:
        print("Error Notion:", res.status_code, res.text)
    else:
        print(f"Page synced for Linear ID {linear_id}")

def main():
    issues = fetch_linear_issues()
    print(f"Issues fetched: {len(issues)}")
    for issue in issues:
        upsert_notion(issue)

if __name__ == "__main__":
    main()
