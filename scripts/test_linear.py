import requests
import os

token = os.environ.get("LINEAR_API_KEY")

headers = {
    "Authorization": token,
    "Content-Type": "application/json"
}

query = """
{
  viewer {
    id
    name
  }
}
"""

response = requests.post(
    "https://api.linear.app/graphql",
    json={"query": query},
    headers=headers
)

print(response.text)
