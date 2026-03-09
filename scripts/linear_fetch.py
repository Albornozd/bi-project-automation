import requests
import json
import os

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")

query = """
{
  issues(first: 100) {
    nodes {
      id
      title
      description
      dueDate
      state {
        name
      }
      team {
        name
      }
      project {
        name
      }
      labels {
        nodes {
          name
        }
      }
    }
  }
}
"""

headers = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json"
}

response = requests.post(
    "https://api.linear.app/graphql",
    json={"query": query},
    headers=headers
)

data = response.json()

issues = data["data"]["issues"]["nodes"]

with open("linear_issues.json", "w") as f:
    json.dump(issues, f, indent=2)

print(f"Issues fetched: {len(issues)}")
