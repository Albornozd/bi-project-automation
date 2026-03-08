import os
import json
import requests

OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "data/linear_issues.json")
API_KEY = os.environ.get("LINEAR_API_KEY")

# GraphQL query para obtener todos los issues con campos importantes
query = """
{
  issues {
    nodes {
      id
      title
      description
      state {
        name
      }
      labels {
        nodes {
          name
        }
      }
      dueDate
      assignee {
        name
      }
      project {
        name
      }
      team {
        name
      }
    }
  }
}
"""

headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}

response = requests.post("https://api.linear.app/graphql", json={"query": query}, headers=headers)
data = response.json()

# Guardar los issues en JSON
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"Linear issues saved in {OUTPUT_FILE}")
