import os
import json
import requests
from pathlib import Path

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
Path("data").mkdir(parents=True, exist_ok=True)

headers = {"Authorization": LINEAR_API_KEY, "Content-Type": "application/json"}
query = """
{
  issues(first: 100) {
    nodes {
      id
      name
      description
      status { name }
      dueDate
      assignee { name }
      project { name }
      team { name }
      labels { nodes { name } }
    }
  }
}
"""

response = requests.post("https://api.linear.app/graphql", headers=headers, json={"query": query})
data = response.json()

issues = []
for i in data.get("data", {}).get("issues", {}).get("nodes", []):
    labels_dict = {}
    for label in i.get("labels", {}).get("nodes", []):
        # Supón que tus labels están en formato "Grupo:Valor"
        if ":" in label["name"]:
            group, value = label["name"].split(":", 1)
            labels_dict[group.strip()] = value.strip()
    issues.append({
        "id": i.get("id"),
        "name": i.get("name"),
        "description": i.get("description"),
        "status": i.get("status", {}).get("name"),
        "due_date": i.get("dueDate"),
        "assignee": i.get("assignee", {}).get("name"),
        "project": i.get("project", {}).get("name"),
        "team": i.get("team", {}).get("name"),
        "labels": labels_dict
    })

with open("data/linear_issues.json", "w", encoding="utf-8") as f:
    json.dump(issues, f, indent=2, ensure_ascii=False)

print(f"{len(issues)} issues guardados en data/linear_issues.json")
