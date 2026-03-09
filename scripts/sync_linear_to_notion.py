import requests
import os

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

LINEAR_URL = "https://api.linear.app/graphql"


def get_linear_issues():

    query = """
    {
      issues(first: 50) {
        nodes {
          id
          title
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
        LINEAR_URL,
        json={"query": query},
        headers=headers
    )

    return response.json()["data"]["issues"]["nodes"]


def create_notion_page(issue):

    title = issue["title"]

    estado = issue["state"]["name"] if issue["state"] else "Backlog"

    proyecto = None
    if issue.get("project"):
        proyecto = issue["project"]["name"]

    team = None
    if issue.get("team"):
        team = issue["team"]["name"]

    departamentos = []
    if issue.get("labels"):
        departamentos = [l["name"] for l in issue["labels"]["nodes"]]

    url = "https://api.notion.com/v1/pages"

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    properties = {

        "Name": {
            "title": [
                {
                    "text": {
                        "content": title
                    }
                }
            ]
        },

        "Estado": {
            "status": {
                "name": estado
            }
        }
    }

    if proyecto:
        properties["Proyecto"] = {
            "select": {
                "name": proyecto
            }
        }

    if team:
        properties["Team"] = {
            "select": {
                "name": team
            }
        }

    if departamentos:
        properties["Departamento"] = {
            "multi_select": [
                {"name": d} for d in departamentos
            ]
        }

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print("Error creando tarea en Notion:")
        print(response.text)


def main():

    issues = get_linear_issues()

    for issue in issues:
        create_notion_page(issue)


if __name__ == "__main__":
    main()
