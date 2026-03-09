import os
import requests

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]
NOTION_API_KEY = os.environ["NOTION_API_KEY"]
NOTION_DATABASE_ID = os.environ["BI_INITIATIVES_DB"]

LINEAR_URL = "https://api.linear.app/graphql"
NOTION_URL = "https://api.notion.com/v1/pages"

LINEAR_HEADERS = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json"
}

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}


def get_linear_issues():

    query = """
    {
      issues(first: 50) {
        nodes {
          id
          title
          state { name }
          team { name }
          project { name }
        }
      }
    }
    """

    response = requests.post(
        LINEAR_URL,
        headers=LINEAR_HEADERS,
        json={"query": query}
    )

    response.raise_for_status()

    data = response.json()

    return data["data"]["issues"]["nodes"]


def create_notion_page(issue):

    title = issue["title"]
    estado = issue["state"]["name"] if issue["state"] else "Backlog"
    team = issue["team"]["name"] if issue["team"] else "General"
    proyecto = issue["project"]["name"] if issue["project"] else "General"

    payload = {

        "parent": {
            "database_id": NOTION_DATABASE_ID
        },

        "properties": {

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
            },

            "Proyecto": {
                "select": {
                    "name": proyecto
                }
            },

            "Team": {
                "select": {
                    "name": team
                }
            },

            "Departamento": {
                "multi_select": [
                    {"name": "BI"}
                ]
            }

        }
    }

    response = requests.post(
        NOTION_URL,
        headers=NOTION_HEADERS,
        json=payload
    )

    if response.status_code != 200:
        print("Error creando tarea en Notion:")
        print(response.text)


def main():

    issues = get_linear_issues()

    print(f"Issues encontrados: {len(issues)}")

    for issue in issues:
        create_notion_page(issue)


if __name__ == "__main__":
    main()
