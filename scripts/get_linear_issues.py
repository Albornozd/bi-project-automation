import os
import requests
import json

LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")

url = "https://api.linear.app/graphql"

query = """
{
  issues(first: 100) {
    nodes {
      id
      title
      description
      state {
        name
      }
      assignee {
        name
      }
      dueDate
      labels {
        nodes {
          name
          description
        }
      }
      createdAt
      updatedAt
    }
  }
}
"""

response = requests.post(
    url,
    headers={
        "Authorization": f"Bearer {LINEAR_API_KEY}",
        "Content-Type": "application/json"
    },
    json={"query": query}
)

data = response.json()

# Guardar JSON completo para análisis posterior
os.makedirs("data", exist_ok=True)
with open("data/linear_issues.json", "w") as f:
    json.dump(data, f, indent=2)

print("Linear issues obtenidos:", len(data.get("data", {}).get("issues", {}).get("nodes", [])))

print("Issues guardados en data/linear_issues.json")
