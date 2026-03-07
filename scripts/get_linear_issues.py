import requests
import os
import json

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]

url = "https://api.linear.app/graphql"

query = """
{
  issues(first: 100) {
    nodes {
      id
      title
      description
      priority
      dueDate
      state {
        name
      }
      assignee {
        name
      }
      labels {
        name
      }
    }
  }
}
"""

headers = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json"
}

response = requests.post(url, json={"query": query}, headers=headers)
data = response.json()

# Guardar archivo local para que otros scripts lo consuman
with open("data/linear_issues.json","w") as f:
    json.dump(data,f,indent=2)

print("✅ Issues descargados de Linear")
