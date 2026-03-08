import os
import requests
import json

LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")
OUTPUT_FILE = "data/linear_issues.json"

headers = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json"
}

query = """
{
  issues(first: 100) {
    nodes {
      id
      title
      state {
        name
      }
      dueDate
      assignee {
        name
      }
      project {
        name
        team {
          name
        }
      }
      labels {
        nodes {
          name
          description
        }
      }
    }
  }
}
"""

response = requests.post("https://api.linear.app/graphql", json={"query": query}, headers=headers)
data = response.json()

os.makedirs("data", exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Linear issues saved to {OUTPUT_FILE}")
