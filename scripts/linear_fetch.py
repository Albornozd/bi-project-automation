import requests
import os
import json

API_KEY = os.getenv("LINEAR_API_KEY")

query = """
{
  issues(first: 100) {
    nodes {
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

for i in data["data"]["issues"]["nodes"]:
    issues.append({
        "title": i["title"],
        "description": i["description"],
        "status": i["state"]["name"],
        "team": i["team"]["name"] if i["team"] else None,
        "project": i["project"]["name"] if i["project"] else None,
        "dueDate": i["dueDate"],
        "labels": [l["name"] for l in i["labels"]["nodes"]]
    })

os.makedirs("data", exist_ok=True)

with open("data/linear_issues.json", "w") as f:
    json.dump({"issues": issues}, f)

print("Linear issues fetched")
