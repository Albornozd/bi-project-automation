import os
import requests

# ============================================================
# CONFIGURACIÓN
# ============================================================

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_ID = os.getenv("REQUESTS_BI")

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
LINEAR_TEAM_ID = os.getenv("LINEAR_TEAM_JOYERIASUAREZ")

LINEAR_URL = "https://api.linear.app/graphql"
NOTION_PAGE_URL = "https://api.notion.com/v1/pages"
NOTION_QUERY_URL = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"

LINEAR_WORKSPACE = "joyeriasuarez"

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

LINEAR_HEADERS = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json",
}


# ============================================================
# HELPERS NOTION
# ============================================================

def get_title(prop):
    """
    Lee TODO el contenido del campo title.
    """
    if not prop:
        return ""

    try:
        items = prop.get("title", [])
        return "".join(
            item.get("plain_text", "")
            or item.get("text", {}).get("content", "")
            for item in items
        ).strip()
    except Exception:
        return ""


def get_rich_text(prop):
    """
    Lee TODO el contenido de un rich_text.
    No se limita a rich_text[0].
    """
    if not prop:
        return ""

    try:
        items = prop.get("rich_text", [])

        parts = []

        for item in items:
            text = item.get("plain_text")

            if text is None:
                text = item.get("text", {}).get("content", "")

            if text:
                parts.append(text)

        return "".join(parts)

    except Exception:
        return ""


def get_select(prop):
    """
    Lee un campo select.
    """
    if not prop:
        return None

    try:
        return prop.get("select", {}).get("name")
    except Exception:
        return None


def get_text_or_select(prop):
    """
    Permite que Proyecto sea select o rich_text.
    """
    if not prop:
        return None

    value = get_select(prop)

    if value:
        return value.strip()

    value = get_rich_text(prop)

    if value:
        return value.strip()

    return None


# ============================================================
# VALIDACIÓN
# ============================================================

def validate_env():

    required = {
        "NOTION_API_KEY": NOTION_API_KEY,
        "REQUESTS_BI": NOTION_DB_ID,
        "LINEAR_API_KEY": LINEAR_API_KEY,
        "LINEAR_TEAM_JOYERIASUAREZ": LINEAR_TEAM_ID,
    }

    for key, value in required.items():

        if not value:
            raise Exception(f"❌ Missing environment variable: {key}")

    print("✅ Variables de entorno OK")


# ============================================================
# LINEAR - LABELS
# ============================================================

def get_linear_labels():

    query = """
    {
      issueLabels(first: 250) {
        nodes {
          id
          name
        }
      }
    }
    """

    response = requests.post(
        LINEAR_URL,
        headers=LINEAR_HEADERS,
        json={"query": query},
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise Exception(
            f"❌ Error obteniendo labels de Linear: {data['errors']}"
        )

    labels = data["data"]["issueLabels"]["nodes"]

    return {
        label["name"].strip(): label["id"]
        for label in labels
    }


# ============================================================
# LINEAR - PROJECTS
# ============================================================

def get_linear_projects():

    query = """
    {
      projects(first: 250) {
        nodes {
          id
          name
        }
      }
    }
    """

    response = requests.post(
        LINEAR_URL,
        headers=LINEAR_HEADERS,
        json={"query": query},
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise Exception(
            f"❌ Error obteniendo proyectos de Linear: {data['errors']}"
        )

    projects = data["data"]["projects"]["nodes"]

    project_map = {}

    for project in projects:

        name = project.get("name", "").strip()

        if name:
            project_map[name.lower()] = {
                "id": project["id"],
                "name": name,
            }

    print(f"📁 Proyectos Linear encontrados: {len(project_map)}")

    return project_map


def find_linear_project(project_name, project_map):

    if not project_name:
        raise Exception(
            "❌ La propiedad 'Proyecto' está vacía en Notion."
        )

    normalized = project_name.strip().lower()

    project = project_map.get(normalized)

    if not project:

        available = sorted(
            project["name"]
            for project in project_map.values()
        )

        print("")
        print("❌ PROYECTO NO ENCONTRADO EN LINEAR")
        print(f"   Proyecto indicado en Notion: {project_name}")
        print("")
        print("📁 Proyectos disponibles en Linear:")

        for name in available:
            print(f"   - {name}")

        print("")

        raise Exception(
            f"El proyecto '{project_name}' no existe en Linear."
        )

    return project


# ============================================================
# NOTION - TASKS
# ============================================================

def get_tasks_to_plan():

    payload = {
        "filter": {
            "property": "Planificar",
            "checkbox": {
                "equals": True
            }
        }
    }

    response = requests.post(
        NOTION_QUERY_URL,
        headers=NOTION_HEADERS,
        json=payload,
        timeout=30,
    )

    if response.status_code != 200:

        print("❌ Error consultando Notion:")
        print(response.text)

        raise Exception("Error querying Notion")

    data = response.json()

    return data.get("results", [])


# ============================================================
# LINEAR - CREATE ISSUE
# ============================================================

def create_linear_issue(task, label_map, project_map):

    props = task["properties"]

    # --------------------------------------------------------
    # TÍTULO
    # --------------------------------------------------------

    title = get_title(
        props.get("Título")
    )

    if not title:

        print("⏭️ Skip: título vacío")

        return None

    # --------------------------------------------------------
    # DESCRIPCIÓN COMPLETA
    # --------------------------------------------------------

    description = get_rich_text(
        props.get("Notas de Implementación")
    )

    print(
        f"📝 Notas de Implementación: "
        f"{len(description)} caracteres"
    )

    # --------------------------------------------------------
    # PROYECTO
    # --------------------------------------------------------

    project_name = get_text_or_select(
        props.get("Proyecto")
    )

    print(
        f"📁 Proyecto indicado en Notion: "
        f"{project_name}"
    )

    project = find_linear_project(
        project_name,
        project_map
    )

    project_id = project["id"]

    print(
        f"📁 Proyecto Linear encontrado: "
        f"{project['name']}"
    )

    # --------------------------------------------------------
    # LABELS
    # --------------------------------------------------------

    label_fields = [
        "Departamento",
        "Sociedad",
        "Prioridad",
        "Impacto Negocio",
        "Esfuerzo Estimado",
    ]

    label_ids = []

    for field in label_fields:

        value = get_select(
            props.get(field)
        )

        if not value:
            continue

        value = value.strip()

        label_id = label_map.get(value)

        if label_id:

            label_ids.append(label_id)

            print(
                f"🏷️ {field}: {value}"
            )

        else:

            print(
                f"⚠️ Label no encontrado en Linear: "
                f"{value}"
            )

    # --------------------------------------------------------
    # MUTATION
    # --------------------------------------------------------

    query = """
    mutation ($input: IssueCreateInput!) {

      issueCreate(input: $input) {

        issue {
          id
          identifier
          title
          description
          project {
            id
            name
          }
        }

      }

    }
    """

    variables = {
        "input": {
            "title": title,
            "description": description,
            "teamId": LINEAR_TEAM_ID,
            "projectId": project_id,
            "labelIds": label_ids,
        }
    }

    response = requests.post(
        LINEAR_URL,
        headers=LINEAR_HEADERS,
        json={
            "query": query,
            "variables": variables,
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:

        print("❌ Linear error:")
        print(data["errors"])

        raise Exception(
            "Linear creation failed"
        )

    issue = data["data"]["issueCreate"]["issue"]

    print(
        f"✅ Issue creado en Linear: "
        f"{issue['identifier']}"
    )

    return issue


# ============================================================
# NOTION - UPDATE PAGE
# ============================================================

def update_notion_page(page_id, linear_issue):

    identifier = linear_issue["identifier"]

    linear_url = (
        f"https://linear.app/"
        f"{LINEAR_WORKSPACE}/issue/"
        f"{identifier}"
    )

    payload = {
        "properties": {

            "Issue Creado": {
                "checkbox": True
            },

            "Linear ID": {
                "rich_text": [
                    {
                        "text": {
                            "content": identifier
                        }
                    }
                ]
            },

            "Issue Linear": {
                "url": linear_url
            },
        }
    }

    url = f"{NOTION_PAGE_URL}/{page_id}"

    response = requests.patch(
        url,
        headers=NOTION_HEADERS,
        json=payload,
        timeout=30,
    )

    if response.status_code != 200:

        print("❌ Error actualizando Notion:")
        print(response.text)

        raise Exception(
            "Error updating Notion"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("")
    print("==============================================")
    print("🔄 NOTION → LINEAR")
    print("==============================================")

    validate_env()

    # --------------------------------------------------------
    # Cargar proyectos y labels una sola vez
    # --------------------------------------------------------

    project_map = get_linear_projects()

    label_map = get_linear_labels()

    # --------------------------------------------------------
    # Obtener tareas
    # --------------------------------------------------------

    tasks = get_tasks_to_plan()

    print(
        f"📥 Tasks found: {len(tasks)}"
    )

    created = 0
    skipped = 0
    errors = 0

    # --------------------------------------------------------
    # Procesar tareas
    # --------------------------------------------------------

    for task in tasks:

        try:

            props = task["properties"]

            # ------------------------------------------------
            # Evitar duplicados
            # ------------------------------------------------

            issue_created = (
                props
                .get("Issue Creado", {})
                .get("checkbox", False)
            )

            if issue_created:

                print(
                    "⏭️ Ya creado → skip"
                )

                skipped += 1

                continue

            existing_linear_id = get_rich_text(
                props.get("Linear ID", {})
            )

            if existing_linear_id:

                print(
                    "⏭️ Ya tiene Linear ID "
                    f"({existing_linear_id}) → skip"
                )

                skipped += 1

                continue

            # ------------------------------------------------
            # Crear
            # ------------------------------------------------

            page_id = task["id"]

            issue = create_linear_issue(
                task,
                label_map,
                project_map
            )

            if issue:

                update_notion_page(
                    page_id,
                    issue
                )

                print(
                    f"✅ Sincronizado: "
                    f"{issue['identifier']}"
                )

                created += 1

        except Exception as e:

            errors += 1

            print(
                f"❌ Error en task "
                f"{task.get('id')}: {e}"
            )

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    print("")
    print("==============================================")
    print("📊 RESULTADO")
    print("==============================================")
    print(f"Created: {created}")
    print(f"Skipped: {skipped}")
    print(f"Errors:  {errors}")
    print("==============================================")
    print("")


if __name__ == "__main__":
    main()
