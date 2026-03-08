import requests
import os
import json

token = os.environ.get("LINEAR_API_KEY")

headers = {
    "Authorization": token,
    "Content-Type": "application/json"
}

query = """
{
  issues(first: 50) {
    nodes {
      id
      title
      description
      priority
      state {
        name
      }
      assignee {
        name
      }
      createdAt
    }
  }
}
"""

response = requests.post(
    "https://api.linear.app/graphql",
    json={"query": query},
    headers=headers
)

data = response.json()

with open("data/linear_issues.json", "w") as f:
    json.dump(data, f, indent=2)

print("Issues guardados en data/linear_issues.json")
