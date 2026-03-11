import requests
import os
import json

# Traemos el API Key de Linear desde el secret de GitHub
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
GRAPHQL_URL = "https://api.linear.app/graphql"

# Query GraphQL para obtener issues y labels
query = """
{
  issues(first: 50) {
    nodes {
      id
      title
      description
      createdAt
      state { name }
      assignee { name }
      dueDate
      labels { nodes { name } }
      team { name }
      project { name }
    }
  }
}
"""

headers = {
    "Authorization": f"Bearer {LINEAR_API_KEY}",
    "Content-Type": "application/json"
}

response = requests.post(GRAPHQL_URL, headers=headers, json={"query": query})

if response.status_code == 200:
    data = response.json()
    issues = data.get("data", {}).get("issues", {}).get("nodes", [])
    print(f"Issues fetched: {len(issues)}")
    
    # Guardar los issues en un archivo JSON para usarlo en push_to_notion.py
    with open("issues.json", "w", encoding="utf-8") as f:
        json.dump(issues, f, indent=2, ensure_ascii=False)
else:
    print("Error fetching Linear issues:", response.status_code, response.text)
