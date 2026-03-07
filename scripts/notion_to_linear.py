import requests
import os

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]

NOTION_DATABASE_ID = "TU_DATABASE_ID"  # Reemplaza con tu database ID

# Leer Notion BI Requests
headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
response = requests.post(url, headers=headers)
data = response.json()

# Crear Issues en Linear
for page in data["results"]:
    title_prop = page["properties"]["Titulo"]["title"]
    title = title_prop[0]["plain_text"] if title_prop else "Sin título"

    mutation = """
    mutation ($title: String!) {
      issueCreate(input:{title:$title}) {
        success
        issue {
          id
          title
        }
      }
    }
    """

    linear_headers = {
        "Authorization": LINEAR_API_KEY,
        "Content-Type": "application/json"
    }

    r = requests.post(
        "https://api.linear.app/graphql",
        json={"query": mutation, "variables":{"title": title}},
        headers=linear_headers
    )

    print(f"✅ Issue creado en Linear: {title}")
