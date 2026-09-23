import os
import requests
from datetime import datetime


# ============================================================
# CONFIGURACIÓN
# ============================================================

LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")

NOTION_DATABASE_ID = os.environ.get(
    "BI_INITIATIVES_DB"
)

LINEAR_URL = "https://api.linear.app/graphql"

NOTION_PAGE_URL = (
    "https://api.notion.com/v1/pages"
)

NOTION_QUERY_URL = (
    f"https://api.notion.com/v1/databases/"
    f"{NOTION_DATABASE_ID}/query"
)


LINEAR_HEADERS = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json",
}

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


# ============================================================
# NOTION TEXT LIMIT
# ============================================================

# Dejamos margen respecto al límite de 2.000.
NOTION_TEXT_CHUNK_SIZE = 1800


# ============================================================
# LABEL MAPPING
# ============================================================

LABEL_MAPPING = {

    "Departamento": [
        "BI",
        "IT",
        "Finanzas",
        "Administración",
        "Logística",
        "RRHH",
        "Producto",
        "Retail",
        "Digital",
        "Marketing",
        "Producción (Fabricación)",
        "Postventa",
        "Gemología",
        "Diseño",
    ],

    "Sociedad": [
        "Aristocrazy",
        "Suarez",
        "Grupo",
    ],

    "Esfuerzo": [
        "XL",
        "L",
        "M",
        "S",
    ],

    "Impacto": [
        "Alto",
        "Medio",
        "Bajo",
    ],

    "Prioridad": [
        "Alta",
        "Media",
        "Baja",
    ],

    "Modelo de Datos": [
        "None",
        "Modelo Produccion",
        "Modelo Contable - Suarez",
        "Modelo Contable - Aristocrazy",
        "Modelo Transaccional - Suarez",
        "Modelo Transaccional - Aristocrazy",
        "Modelo Ventas en Real Time",
        "Modelo CRM",
    ],

    "Tipo de Trabajo": [
        "Funcionalidad (Feature)",
        "Mejora (Improvement)",
        "Cambio (Change)",
    ],
}


# ============================================================
# HELPERS - TEXTOS LARGOS
# ============================================================

def chunk_text(text, size=NOTION_TEXT_CHUNK_SIZE):

    if not text:
        return []

    return [
        text[i:i + size]
        for i in range(
            0,
            len(text),
            size
        )
    ]


def build_rich_text(text):

    if text is None:
        text = ""

    chunks = chunk_text(text)

    return [
        {
            "type": "text",
            "text": {
                "content": chunk
            }
        }
        for chunk in chunks
    ]


# ============================================================
# VALIDACIÓN
# ============================================================

def validate_env():

    required = {

        "LINEAR_API_KEY":
            LINEAR_API_KEY,

        "NOTION_API_KEY":
            NOTION_API_KEY,

        "BI_INITIATIVES_DB":
            NOTION_DATABASE_ID,
    }

    for key, value in required.items():

        if not value:

            raise Exception(
                f"❌ Missing environment variable: {key}"
            )

    print(
        "✅ Environment variables validated"
    )


# ============================================================
# LINEAR - ISSUES
# ============================================================

def get_linear_issues():

    query = """
    {
      issues(first: 100) {
        nodes {

          id
          identifier
          title
          description

          createdAt
          completedAt
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

          assignee {
            name
          }

          labels(first: 100) {
            nodes {
              name
            }
          }
        }
      }
    }
    """

    response = requests.post(
        LINEAR_URL,
        headers=LINEAR_HEADERS,
        json={
            "query": query
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:

        raise Exception(
            f"❌ Linear GraphQL error: "
            f"{data['errors']}"
        )

    return (
        data["data"]
        ["issues"]
        ["nodes"]
    )


# ============================================================
# LABEL → NOTION
# ============================================================

def map_label_to_field(
    label_nodes,
    field_name
):

    allowed_values = (
        LABEL_MAPPING
        .get(field_name, [])
    )

    allowed_lower = {
        value.lower(): value
        for value in allowed_values
    }

    for label in label_nodes:

        name = (
            label.get("name")
            or ""
        ).strip()

        normalized = name.lower()

        if normalized in allowed_lower:

            return allowed_lower[
                normalized
            ]

    return None


# ============================================================
# DATE
# ============================================================

def format_date_safe(date_str):

    if not date_str:
        return None

    try:

        dt = datetime.fromisoformat(
            date_str.replace(
                "Z",
                "+00:00"
            )
        )

        return dt.strftime(
            "%Y-%m-%d"
        )

    except Exception:

        return None


# ============================================================
# NOTION - FIND PAGE
# ============================================================

def find_notion_page_by_linear_id(
    identifier,
    uuid
):

    # --------------------------------------------------------
    # Primero buscamos por identifier:
    # BI-123
    # --------------------------------------------------------

    if identifier:

        payload = {
            "filter": {
                "property": "Linear ID",
                "rich_text": {
                    "equals": identifier
                }
            }
        }

        response = requests.post(
            NOTION_QUERY_URL,
            headers=NOTION_HEADERS,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        results = (
            response
            .json()
            .get("results", [])
        )

        if results:

            return results[0]["id"]

    # --------------------------------------------------------
    # Compatibilidad con registros antiguos que guardaban UUID
    # --------------------------------------------------------

    if uuid:

        payload = {
            "filter": {
                "property": "Linear ID",
                "rich_text": {
                    "equals": uuid
                }
            }
        }

        response = requests.post(
            NOTION_QUERY_URL,
            headers=NOTION_HEADERS,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        results = (
            response
            .json()
            .get("results", [])
        )

        if results:

            return results[0]["id"]

    return None


# ============================================================
# BUILD NOTION PAYLOAD
# ============================================================

def build_payload(issue):

    linear_uuid = (
        issue.get("id")
        or ""
    )

    linear_identifier = (
        issue.get("identifier")
        or ""
    )

    title = (
        issue.get("title")
        or "Sin título"
    )

    estado = (
        issue.get("state", {})
        .get("name")
        or "Backlog"
    )

    team = (
        issue.get("team", {})
        .get("name")
        or "General"
    )

    proyecto = (
        issue.get("project", {})
        .get("name")
        or "General"
    )

    owner = ""

    if issue.get("assignee"):

        owner = (
            issue["assignee"]
            .get("name")
            or ""
        )

    due_date = (
        issue.get("dueDate")
        or None
    )

    descripcion = (
        issue.get("description")
        or ""
    )

    labels = (
        issue
        .get("labels", {})
        .get("nodes", [])
    )

    created_at = format_date_safe(
        issue.get("createdAt")
    )

    completed_at = format_date_safe(
        issue.get("completedAt")
    )

    # ========================================================
    # LABELS
    # ========================================================

    departamento = map_label_to_field(
        labels,
        "Departamento"
    )

    sociedad = map_label_to_field(
        labels,
        "Sociedad"
    )

    prioridad = map_label_to_field(
        labels,
        "Prioridad"
    )

    impacto = map_label_to_field(
        labels,
        "Impacto"
    )

    esfuerzo = map_label_to_field(
        labels,
        "Esfuerzo"
    )

    modelo_datos = map_label_to_field(
        labels,
        "Modelo de Datos"
    )

    tipo_trabajo = map_label_to_field(
        labels,
        "Tipo de Trabajo"
    )

    # ========================================================
    # PROPERTIES
    # ========================================================

    properties = {

        "Nombre": {
            "title": build_rich_text(title)
        },

        "Descripcion": {
            "rich_text": build_rich_text(
                descripcion
            )
        },

        "Owner": {
            "rich_text": build_rich_text(
                owner
            )
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

        "Linear ID": {
            "rich_text": build_rich_text(
                linear_identifier
            )
        },

        "Fecha de Creacion": (
            {
                "date": {
                    "start": created_at
                }
            }
            if created_at
            else
            {
                "date": None
            }
        ),

        "Fecha de Culminacion": (
            {
                "date": {
                    "start": completed_at
                }
            }
            if completed_at
            else
            {
                "date": None
            }
        ),
    }

    # ========================================================
    # LABELS - SOLO SI EXISTEN
    # ========================================================

    if departamento:

        properties["Departamento"] = {
            "multi_select": [
                {
                    "name": departamento
                }
            ]
        }

    if sociedad:

        properties["Sociedad"] = {
            "select": {
                "name": sociedad
            }
        }

    if prioridad:

        properties["Prioridad"] = {
            "select": {
                "name": prioridad
            }
        }

    if impacto:

        properties["Impacto"] = {
            "select": {
                "name": impacto
            }
        }

    if esfuerzo:

        properties["Esfuerzo"] = {
            "select": {
                "name": esfuerzo
            }
        }

    # ========================================================
    # MODELO DE DATOS
    # ========================================================

    if modelo_datos:

        print(
            f"🧩 Modelo de Datos: "
            f"{modelo_datos}"
        )

        properties["Modelo de Datos"] = {
            "select": {
                "name": modelo_datos
            }
        }

    else:

        print(
            "⚠️ El issue no tiene un label "
            "compatible con 'Modelo de Datos'"
        )

    # ========================================================
    # TIPO DE TRABAJO
    # ========================================================

    if tipo_trabajo:

        properties["Tipo de Proyecto"] = {
            "select": {
                "name": tipo_trabajo
            }
        }

    # ========================================================
    # DUE DATE
    # ========================================================

    if due_date:

        properties["Due Date"] = {
            "date": {
                "start": due_date
            }
        }

    return {
        "parent": {
            "database_id":
                NOTION_DATABASE_ID
        },

        "properties": properties
    }


# ============================================================
# CREATE NOTION PAGE
# ============================================================

def create_notion_page(
    payload,
    title
):

    response = requests.post(
        NOTION_URL,
        headers=NOTION_HEADERS,
        json=payload,
        timeout=30,
    )

    if response.status_code != 200:

        print(
            "❌ Error creando tarea "
            "en Notion:"
        )

        print(
            response.text
        )

        raise Exception(
            "Error creando página en Notion"
        )

    print(
        f"✅ Tarea creada en Notion: "
        f"{title}"
    )


# ============================================================
# UPDATE NOTION PAGE
# ============================================================

def update_notion_page(
    page_id,
    payload,
    title
):

    url = (
        f"https://api.notion.com/v1/pages/"
        f"{page_id}"
    )

    response = requests.patch(
        url,
        headers=NOTION_HEADERS,
        json={
            "properties":
                payload["properties"]
        },
        timeout=30,
    )

    if response.status_code != 200:

        print(
            "❌ Error actualizando "
            "tarea en Notion:"
        )

        print(
            response.text
        )

        raise Exception(
            "Error actualizando página "
            "en Notion"
        )

    print(
        f"✅ Tarea actualizada en Notion: "
        f"{title}"
    )


# ============================================================
# SYNC
# ============================================================

def sync_issue(issue):

    linear_uuid = (
        issue.get("id")
    )

    linear_identifier = (
        issue.get("identifier")
    )

    title = (
        issue.get("title")
        or "Sin título"
    )

    descripcion = (
        issue.get("description")
        or ""
    )

    print("")
    print(
        "----------------------------------------------"
    )

    print(
        f"🔄 {linear_identifier} - {title}"
    )

    print(
        f"📝 Descripción: "
        f"{len(descripcion)} caracteres"
    )

    # --------------------------------------------------------
    # Buscar por identifier o UUID
    # --------------------------------------------------------

    page_id = find_notion_page_by_linear_id(
        linear_identifier,
        linear_uuid
    )

    payload = build_payload(
        issue
    )

    if page_id:

        update_notion_page(
            page_id,
            payload,
            title
        )

    else:

        create_notion_page(
            payload,
            title
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("")
    print("==============================================")
    print("🔄 LINEAR → NOTION")
    print("==============================================")

    validate_env()

    issues = get_linear_issues()

    print(
        f"📥 Issues encontrados en Linear: "
        f"{len(issues)}"
    )

    errors = 0

    for issue in issues:

        try:

            sync_issue(
                issue
            )

        except Exception as e:

            errors += 1

            print(
                f"❌ Error procesando "
                f"{issue.get('identifier')}: "
                f"{e}"
            )

    print("")
    print("==============================================")
    print("📊 RESULTADO")
    print("==============================================")
    print(
        f"Issues procesados: {len(issues)}"
    )
    print(
        f"Errores: {errors}"
    )
    print("==============================================")


if __name__ == "__main__":
    main()
