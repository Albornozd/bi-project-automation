import requests
import os
import json

API_KEY = os.getenv("LINEAR_API_KEY")

query = """
{
  issues(first: 100) {
    nodes {
      id
      title
      description
      dueDate
      state { name }
      team { name }
      project { name }
      labels { nodes { name } }
    }
  }
}
"""

response = requests.post(
    "https://api.linear.app/graphql",
    headers={"Authorization": API_KEY},
    json={"query": query}
)

data = response.json()

issues = []

for issue in data["data"]["issues"]["nodes"]:

    issues.append({
        "id": issue["id"],
        "title": issue["title"],
        "description": issue["description"],
        "status": issue["state"]["name"],
        "team": issue["team"]["name"] if issue["team"] else None,
        "project": issue["project"]["name"] if issue["project"] else None,
        "dueDate": issue["dueDate"],
        "labels": [l["name"] for l in issue["labels"]["nodes"]]
    })

os.makedirs("data", exist_ok=True)

with open("data/linear_issues.json", "w") as f:
    json.dump({"issues": issues}, f)

print("Linear issues fetched")
