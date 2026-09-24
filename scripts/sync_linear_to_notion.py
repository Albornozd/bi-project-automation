```python
import os
import requests
from datetime import datetime
import unicodedata


# ============================================================
# CONFIGURACIÓN
# ============================================================

LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("BI_INITIATIVES_DB")

LINEAR_URL = "https://api.linear.app/graphql"

NOTION_PAGE_URL = "https://api.notion.com/v1/pages"

NOTION_DATABASE_URL = (
    f"https://api.notion.com/v1/databases/"
    f"{NOTION_DATABASE_ID}"
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
# CONFIGURACIÓN DE PROPIEDADES NOTION
# ============================================================

NOTION_LINEAR_ID_PROPERTY = "Linear ID"

NOTION_TITLE_PROPERTY = "Nombre"

NOTION_DESCRIPTION_PROPERTY = "Descripcion"

NOTION_MODEL_DATA_PROPERTY = "Modelo de Datos"

NOTION_OWNER_PROPERTY = "Owner"

NOTION_STATE_PROPERTY = "Estado"

NOTION_PROJECT_PROPERTY = "Proyecto"

NOTION_TEAM_PROPERTY = "Team"

NOTION_DEPARTMENT_PROPERTY = "Departamento"

NOTION_COMPANY_PROPERTY = "Sociedad"

NOTION_PRIORITY_PROPERTY = "Prioridad"

NOTION_IMPACT_PROPERTY = "Impacto"

NOTION_EFFORT_PROPERTY = "Esfuerzo"

NOTION_CREATED_DATE_PROPERTY = "Fecha de Creacion"

NOTION_COMPLETED_DATE_PROPERTY = "Fecha de Culminacion"

NOTION_DUE_DATE_PROPERTY = "Due Date"

NOTION_WORK_TYPE_PROPERTY = "Tipo de Proyecto"


# ============================================================
# TEXTOS LARGOS
# ============================================================

# Notion permite hasta 2.000 caracteres por objeto de texto.
# Utilizamos 1.800 para dejar margen.
NOTION_TEXT_CHUNK_SIZE = 1800


def chunk_text(text, size=NOTION_TEXT_CHUNK_SIZE):

    if not text:
        return []

    return [
        text[i:i + size]
        for i in range(0, len(text), size)
    ]


def build_rich_text(text):

    if text is None:
        text = ""

    if text == "":
        return []

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
# NORMALIZACIÓN DE TEXTO
# ============================================================

def normalize_text(value):

    if value is None:
        return ""

    value = str(value).strip().lower()

    value = unicodedata.normalize(
        "NFKD",
        value
    )

    value = "".join(
        c
        for c in value
        if not unicodedata.combining(c)
    )

    return value


# ============================================================
# VALIDACIÓN
# ============================================================

def validate_env():

    required = {
        "LINEAR_API_KEY": LINEAR_API_KEY,
        "NOTION_API_KEY": NOTION_API_KEY,
        "BI_INITIATIVES_DB": NOTION_DATABASE_ID,
    }

    for key, value in required.items():

        if not value:

            raise Exception(
                f"❌ Falta la variable de entorno: {key}"
            )

    print("✅ Variables de entorno OK")


# ============================================================
# NOTION - ESQUEMA DE LA BASE DE DATOS
# ============================================================

def get_notion_database_schema():

    print("")
    print("🔎 Consultando esquema de BI_INITIATIVES...")

    response = requests.get(
        NOTION_DATABASE_URL,
        headers=NOTION_HEADERS,
        timeout=30,
    )

    if response.status_code != 200:

        print("❌ Error obteniendo esquema de Notion:")
        print(response.text)

        raise Exception(
            "No se pudo obtener el esquema de BI_INITIATIVES"
        )

    data = response.json()

    properties = data.get("properties", {})

    print("")
    print("📋 PROPIEDADES DETECTADAS EN BI_INITIATIVES")
    print("------------------------------------------------")

    for name, definition in properties.items():

        prop_type = definition.get("type")

        print(
            f"   {name}  -->  {prop_type}"
        )

    print("------------------------------------------------")
    print("")

    return properties


def get_actual_property_name(
    schema,
    expected_name
):

    # Primero coincidencia exacta
    if expected_name in schema:
        return expected_name

    expected_normalized = normalize_text(
        expected_name
    )

    # Después coincidencia ignorando:
    # - mayúsculas
    # - minúsculas
    # - acentos
    for name in schema.keys():

        if normalize_text(name) == expected_normalized:

            print(
                f"ℹ️ Propiedad '{expected_name}' "
                f"encontrada como '{name}'"
            )

            return name

    return None


# ============================================================
# LINEAR - OBTENER ISSUES
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
              id
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
            f"❌ Error GraphQL de Linear: "
            f"{data['errors']}"
        )

    issues = (
        data
        .get("data", {})
        .get("issues", {})
        .get("nodes", [])
    )

    print(
        f"📥 Issues obtenidos de Linear: "
        f"{len(issues)}"
    )

    return issues


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


def map_label_to_field(
    label_nodes,
    field_name
):

    allowed_values = LABEL_MAPPING.get(
        field_name,
        []
    )

    allowed = {
        normalize_text(value): value
        for value in allowed_values
    }

    for label in label_nodes:

        name = (
            label.get("name")
            or ""
        ).strip()

        normalized = normalize_text(name)

        if normalized in allowed:

            return allowed[normalized]

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
# NOTION - BUSCAR POR LINEAR ID
# ============================================================

def query_notion_by_linear_id(value):

    if not value:
        return None

    payload = {
        "filter": {
            "property": NOTION_LINEAR_ID_PROPERTY,
            "rich_text": {
                "equals": value
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

        print(
            "❌ Error buscando Linear ID "
            f"{value} en Notion:"
        )

        print(response.text)

        raise Exception(
            "Error consultando BI_INITIATIVES"
        )

    results = (
        response
        .json()
        .get("results", [])
    )

    if results:

        return results[0]["id"]

    return None


def find_notion_page_by_linear_id(
    identifier,
    uuid
):

    # --------------------------------------------------------
    # 1. Buscar por identifier
    # Ejemplo: BI-123
    # --------------------------------------------------------

    if identifier:

        page_id = query_notion_by_linear_id(
            identifier
        )

        if page_id:

            print(
                f"🔎 Encontrado por Linear ID: "
                f"{identifier}"
            )

            return page_id

    # --------------------------------------------------------
    # 2. Compatibilidad con registros antiguos
    # donde se guardó el UUID
    # --------------------------------------------------------

    if uuid:

        page_id = query_notion_by_linear_id(
            uuid
        )

        if page_id:

            print(
                f"🔎 Encontrado por UUID antiguo: "
                f"{uuid}"
            )

            return page_id

    return None


# ============================================================
# BUILD PAYLOAD
# ============================================================

def build_payload(
    issue,
    notion_schema
):

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

    description = (
        issue.get("description")
        or ""
    )

    state = (
        issue.get("state", {})
        .get("name")
        or "Backlog"
    )

    team = (
        issue.get("team", {})
        .get("name")
        or ""
    )

    project = (
        issue.get("project", {})
        .get("name")
        or ""
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

    created_at = format_date_safe(
        issue.get("createdAt")
    )

    completed_at = format_date_safe(
        issue.get("completedAt")
    )

    labels = (
        issue
        .get("labels", {})
        .get("nodes", [])
    )

    # --------------------------------------------------------
    # DEBUG: mostrar labels
    # --------------------------------------------------------

    print("")
    print("🏷️ LABELS DE LINEAR:")

    for label in labels:

        print(
            f"   - {label.get('name')}"
        )

    # --------------------------------------------------------
    # MAPEAR LABELS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Mostrar Modelo de Datos
    # --------------------------------------------------------

    if modelo_datos:

        print(
            f"🧩 Modelo de Datos detectado: "
            f"{modelo_datos}"
        )

    else:

        print(
            "⚠️ No se encontró un label compatible "
            "con Modelo de Datos"
        )

    # --------------------------------------------------------
    # PROPERTIES
    # --------------------------------------------------------

    properties = {}

    # ========================================================
    # NOMBRE
    # ========================================================

    prop_name = get_actual_property_name(
        notion_schema,
        NOTION_TITLE_PROPERTY
    )

    if prop_name:

        properties[prop_name] = {
            "title": build_rich_text(title)
        }

    # ========================================================
    # DESCRIPCIÓN
    # ========================================================

    prop_description = get_actual_property_name(
        notion_schema,
        NOTION_DESCRIPTION_PROPERTY
    )

    if prop_description:

        prop_type = notion_schema[
            prop_description
        ].get("type")

        print(
            f"📝 Descripcion encontrada: "
            f"'{prop_description}' "
            f"(tipo={prop_type})"
        )

        if prop_type == "rich_text":

            properties[prop_description] = {
                "rich_text": build_rich_text(
                    description
                )
            }

            print(
                f"📝 Descripcion enviada: "
                f"{len(description)} caracteres"
            )

        else:

            print(
                "❌ La propiedad Descripcion "
                f"no es rich_text. Es: {prop_type}"
            )

    else:

        print(
            "❌ NO EXISTE la propiedad "
            "'Descripcion' en BI_INITIATIVES"
        )

    # ========================================================
    # OWNER
    # ========================================================

    prop_owner = get_actual_property_name(
        notion_schema,
        NOTION_OWNER_PROPERTY
    )

    if prop_owner:

        properties[prop_owner] = {
            "rich_text": build_rich_text(
                owner
            )
        }

    # ========================================================
    # ESTADO
    # ========================================================

    prop_state = get_actual_property_name(
        notion_schema,
        NOTION_STATE_PROPERTY
    )

    if prop_state:

        prop_type = notion_schema[
            prop_state
        ].get("type")

        if prop_type == "status":

            properties[prop_state] = {
                "status": {
                    "name": state
                }
            }

    # ========================================================
    # PROYECTO
    # ========================================================

    prop_project = get_actual_property_name(
        notion_schema,
        NOTION_PROJECT_PROPERTY
    )

    if prop_project and project:

        if notion_schema[
            prop_project
        ].get("type") == "select":

            properties[prop_project] = {
                "select": {
                    "name": project
                }
            }

    # ========================================================
    # TEAM
    # ========================================================

    prop_team = get_actual_property_name(
        notion_schema,
        NOTION_TEAM_PROPERTY
    )

    if prop_team and team:

        if notion_schema[
            prop_team
        ].get("type") == "select":

            properties[prop_team] = {
                "select": {
                    "name": team
                }
            }

    # ========================================================
    # LINEAR ID
    # ========================================================

    prop_linear_id = get_actual_property_name(
        notion_schema,
        NOTION_LINEAR_ID_PROPERTY
    )

    if prop_linear_id:

        properties[prop_linear_id] = {
            "rich_text": build_rich_text(
                linear_identifier
            )
        }

    # ========================================================
    # DEPARTAMENTO
    # ========================================================

    prop_department = get_actual_property_name(
        notion_schema,
        NOTION_DEPARTMENT_PROPERTY
    )

    if prop_department and departamento:

        if notion_schema[
            prop_department
        ].get("type") == "multi_select":

            properties[prop_department] = {
                "multi_select": [
                    {
                        "name": departamento
                    }
                ]
            }

    # ========================================================
    # SOCIEDAD
    # ========================================================

    prop_company = get_actual_property_name(
        notion_schema,
        NOTION_COMPANY_PROPERTY
    )

    if prop_company and sociedad:

        if notion_schema[
            prop_company
        ].get("type") == "select":

            properties[prop_company] = {
                "select": {
                    "name": sociedad
                }
            }

    # ========================================================
    # PRIORIDAD
    # ========================================================

    prop_priority = get_actual_property_name(
        notion_schema,
        NOTION_PRIORITY_PROPERTY
    )

    if prop_priority and prioridad:

        if notion_schema[
            prop_priority
        ].get("type") == "select":

            properties[prop_priority] = {
                "select": {
                    "name": prioridad
                }
            }

    # ========================================================
    # IMPACTO
    # ========================================================

    prop_impact = get_actual_property_name(
        notion_schema,
        NOTION_IMPACT_PROPERTY
    )

    if prop_impact and impacto:

        if notion_schema[
            prop_impact
        ].get("type") == "select":

            properties[prop_impact] = {
                "select": {
                    "name": impacto
                }
            }

    # ========================================================
    # ESFUERZO
    # ========================================================

    prop_effort = get_actual_property_name(
        notion_schema,
        NOTION_EFFORT_PROPERTY
    )

    if prop_effort and esfuerzo:

        if notion_schema[
            prop_effort
        ].get("type") == "select":

            properties[prop_effort] = {
                "select": {
                    "name": esfuerzo
                }
            }

    # ========================================================
    # MODELO DE DATOS
    # ========================================================

    prop_model = get_actual_property_name(
        notion_schema,
        NOTION_MODEL_DATA_PROPERTY
    )

    if prop_model:

        prop_type = notion_schema[
            prop_model
        ].get("type")

        print(
            f"🧩 Propiedad Modelo de Datos: "
            f"'{prop_model}' "
            f"(tipo={prop_type})"
        )

        if modelo_datos:

            if prop_type == "select":

                properties[prop_model] = {
                    "select": {
                        "name": modelo_datos
                    }
                }

                print(
                    f"✅ Modelo de Datos enviado: "
                    f"{modelo_datos}"
                )

            elif prop_type == "multi_select":

                properties[prop_model] = {
                    "multi_select": [
                        {
                            "name": modelo_datos
                        }
                    ]
                }

                print(
                    f"✅ Modelo de Datos enviado "
                    f"como multi_select: "
                    f"{modelo_datos}"
                )

            else:

                print(
                    "❌ Modelo de Datos tiene "
                    f"tipo no soportado: "
                    f"{prop_type}"
                )

    else:

        print(
            "❌ NO EXISTE la propiedad "
            "'Modelo de Datos' en Notion"
        )

    # ========================================================
    # FECHA CREACIÓN
    # ========================================================

    prop_created = get_actual_property_name(
        notion_schema,
        NOTION_CREATED_DATE_PROPERTY
    )

    if prop_created:

        if created_at:

            if notion_schema[
                prop_created
            ].get("type") == "date":

                properties[prop_created] = {
                    "date": {
                        "start": created_at
                    }
                }

    # ========================================================
    # FECHA CULMINACIÓN
    # ========================================================

    prop_completed = get_actual_property_name(
        notion_schema,
        NOTION_COMPLETED_DATE_PROPERTY
    )

    if prop_completed:

        if notion_schema[
            prop_completed
        ].get("type") == "date":

            properties[prop_completed] = {
                "date": (
                    {
                        "start": completed_at
                    }
                    if completed_at
                    else None
                )
            }

    # ========================================================
    # DUE DATE
    # ========================================================

    prop_due = get_actual_property_name(
        notion_schema,
        NOTION_DUE_DATE_PROPERTY
    )

    if prop_due and due_date:

        if notion_schema[
            prop_due
        ].get("type") == "date":

            properties[prop_due] = {
                "date": {
                    "start": due_date
                }
            }

    # ========================================================
    # TIPO DE TRABAJO
    # ========================================================

    prop_work_type = get_actual_property_name(
        notion_schema,
        NOTION_WORK_TYPE_PROPERTY
    )

    if prop_work_type and tipo_trabajo:

        if notion_schema[
            prop_work_type
        ].get("type") == "select":

            properties[prop_work_type] = {
                "select": {
                    "name": tipo_trabajo
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
# NOTION - CREATE
# ============================================================

def create_notion_page(
    payload,
    identifier,
    title
):

    print(
        f"🆕 CREANDO nuevo registro "
        f"para {identifier}"
    )

    response = requests.post(
        NOTION_PAGE_URL,
        headers=NOTION_HEADERS,
        json=payload,
        timeout=30,
    )

    if response.status_code != 200:

        print(
            "❌ Error creando página:"
        )

        print(response.text)

        raise Exception(
            "Error creando página en Notion"
        )

    print(
        f"✅ Registro creado: "
        f"{identifier} - {title}"
    )


# ============================================================
# NOTION - UPDATE
# ============================================================

def update_notion_page(
    page_id,
    payload,
    identifier,
    title
):

    url = (
        f"{NOTION_PAGE_URL}/"
        f"{page_id}"
    )

    print(
        f"🔄 ACTUALIZANDO registro existente: "
        f"{identifier}"
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
            "❌ Error actualizando página:"
        )

        print(response.text)

        raise Exception(
            "Error actualizando página "
            "en Notion"
        )

    print(
        f"✅ Registro actualizado: "
        f"{identifier} - {title}"
    )


# ============================================================
# SYNC INDIVIDUAL
# ============================================================

def sync_issue(
    issue,
    notion_schema
):

    identifier = (
        issue.get("identifier")
        or ""
    )

    uuid = (
        issue.get("id")
        or ""
    )

    title = (
        issue.get("title")
        or "Sin título"
    )

    description = (
        issue.get("description")
        or ""
    )

    print("")
    print(
        "================================================"
    )

    print(
        f"🔄 Procesando {identifier}"
    )

    print(
        f"   Título: {title}"
    )

    print(
        f"   Descripción: "
        f"{len(description)} caracteres"
    )

    print(
        f"   UUID: {uuid}"
    )

    print(
        "================================================"
    )

    # --------------------------------------------------------
    # BUSCAR REGISTRO EXISTENTE
    # --------------------------------------------------------

    page_id = find_notion_page_by_linear_id(
        identifier,
        uuid
    )

    # --------------------------------------------------------
    # CONSTRUIR PAYLOAD
    # --------------------------------------------------------

    payload = build_payload(
        issue,
        notion_schema
    )

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    if page_id:

        update_notion_page(
            page_id,
            payload,
            identifier,
            title
        )

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    else:

        create_notion_page(
            payload,
            identifier,
            title
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("")
    print("================================================")
    print("🔄 LINEAR → NOTION")
    print("================================================")

    validate_env()

    # --------------------------------------------------------
    # 1. Obtener esquema real de Notion
    # --------------------------------------------------------

    notion_schema = (
        get_notion_database_schema()
    )

    # --------------------------------------------------------
    # 2. Obtener issues de Linear
    # --------------------------------------------------------

    issues = get_linear_issues()

    errors = 0
    updated = 0
    created = 0

    # --------------------------------------------------------
    # 3. Procesar issues
    # --------------------------------------------------------

    for issue in issues:

        try:

            identifier = (
                issue.get("identifier")
                or ""
            )

            uuid = (
                issue.get("id")
                or ""
            )

            existing_page = (
                find_notion_page_by_linear_id(
                    identifier,
                    uuid
                )
            )

            sync_issue(
                issue,
                notion_schema
            )

            if existing_page:
                updated += 1
            else:
                created += 1

        except Exception as e:

            errors += 1

            print("")
            print(
                f"❌ ERROR procesando "
                f"{issue.get('identifier')}:"
            )

            print(str(e))

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    print("")
    print("================================================")
    print("📊 RESULTADO FINAL")
    print("================================================")

    print(
        f"📥 Issues Linear: {len(issues)}"
    )

    print(
        f"🔄 Registros actualizados: {updated}"
    )

    print(
        f"🆕 Registros nuevos: {created}"
    )

    print(
        f"❌ Errores: {errors}"
    )

    print("================================================")


if __name__ == "__main__":
    main()
```

### Qué ganamos con este script

Hay una diferencia importante respecto al anterior.

Ahora el log del workflow te dirá algo como:

```text
📋 PROPIEDADES DETECTADAS EN BI_INITIATIVES
------------------------------------------------
Nombre              --> title
Descripcion         --> rich_text
Owner               --> rich_text
Estado              --> status
Proyecto            --> select
Team                --> select
Departamento        --> multi_select
Linear ID           --> rich_text
Sociedad            --> select
Prioridad           --> select
Impacto             --> select
Esfuerzo            --> select
Modelo de Datos     --> select
Fecha de Creacion   --> date
Fecha de Culminacion --> date
------------------------------------------------
```

Y después:

```text
🔄 Procesando BI-123
   Título: Nuevo modelo de ventas
   Descripción: 8472 caracteres
   UUID: xxxxxxxx-xxxx...

🏷️ LABELS DE LINEAR:
   - BI
   - Suarez
   - Alta
   - Alto
   - L
   - Modelo CRM

🧩 Modelo de Datos detectado: Modelo CRM

📝 Descripcion encontrada: 'Descripcion' (tipo=rich_text)
📝 Descripcion enviada: 8472 caracteres

🧩 Propiedad Modelo de Datos: 'Modelo de Datos' (tipo=select)
✅ Modelo de Datos enviado: Modelo CRM

🔎 Encontrado por Linear ID: BI-123
🔄 ACTUALIZANDO registro existente: BI-123
✅ Registro actualizado: BI-123 - Nuevo modelo de ventas
```

Eso nos permite saber exactamente dónde está fallando si todavía hubiera algún problema.

---

# 2. Hay una mejora importante respecto al workflow actual

Tu `fetch_linear_issues.py` actualmente no participa en la sincronización.

Tienes:

```text
fetch_linear_issues.py
```

que genera:

```text
issues.json
```

pero después tienes:

```text
sync_linear_to_notion.py
```

que vuelve a consultar directamente Linear.

Por tanto:

```text
fetch_linear_issues.py
        ↓
    issues.json
        ↓
       ❌
   no se utiliza
```

Mientras que realmente tienes:

```text
sync_linear_to_notion.py
        ↓
     Linear API
        ↓
      Notion
```

Yo eliminaría esa duplicidad y dejaría un único script encargado de sincronizar.

Si quieres conservar `fetch_linear_issues.py` para debugging, podemos mantenerlo, pero **no es necesario para el workflow**.

---

# 3. Workflow actualizado

Tu workflow puede quedarse bastante sencillo.

```yaml
name: Linear → Notion Sync

on:

  workflow_dispatch:

  schedule:
    - cron: "0 0,12 * * *"

env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true

jobs:

  sync:

    runs-on: ubuntu-latest

    steps:

      # ======================================================
      # CHECKOUT
      # ======================================================

      - name: Checkout repo
        uses: actions/checkout@v4


      # ======================================================
      # PYTHON
      # ======================================================

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"


      # ======================================================
      # DEPENDENCIES
      # ======================================================

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests


      # ======================================================
      # LINEAR → NOTION
      # ======================================================

      - name: Run Linear → Notion sync
        env:

          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}

          NOTION_API_KEY: ${{ secrets.NOTION_API_KEY }}

          BI_INITIATIVES_DB: ${{ secrets.BI_INITIATIVES_DB }}

        run: |
          python scripts/sync_linear_to_notion.py
```

---

# 4. Una cosa especialmente importante: `Modelo de Datos`

Aquí quiero que hagamos una distinción.

En Linear no existe realmente un campo tipo:

```text
Modelo de Datos
   ├── Modelo CRM
   ├── Modelo Produccion
   ├── Modelo Contable - Suarez
   └── ...
```

como un `select` de Notion.

Lo que normalmente tienes en Linear es un **grupo de labels**, y cada issue puede tener alguno de esos labels.

Por ejemplo:

```text
Issue BI-123

Labels:
    BI
    Suarez
    Alta
    Alto
    L
    Modelo CRM
```

El script tiene que detectar:

```text
Modelo CRM
```

entre todos los labels y convertirlo en:

```text
BI_INITIATIVES
Modelo de Datos = Modelo CRM
```

La nueva versión imprime explícitamente:

```text
🏷️ LABELS DE LINEAR:
   - BI
   - Suarez
   - Alta
   - Alto
   - L
   - Modelo CRM

🧩 Modelo de Datos detectado: Modelo CRM
```

Si en el log aparece:

```text
🏷️ LABELS DE LINEAR:
   - BI
   - Suarez
   - Alta
   - Alto
   - L
```

pero **no aparece `Modelo CRM`**, entonces el problema no está en Notion: el issue de Linear no tiene ese label asociado o el nombre real del label es diferente.

---

# 5. Por qué la descripción puede estar fallando

También tenemos que diferenciar dos cosas.

### Linear → Python

El GraphQL:

```graphql
description
```

devuelve la descripción completa del issue.

Por eso ahora imprimimos:

```text
📝 Descripción: 8472 caracteres
```

Si Linear tiene 8.472 caracteres y aparece:

```text
📝 Descripcion enviada: 8472 caracteres
```

sabemos que Python está recibiendo todo.

### Python → Notion

Aquí dividimos:

```text
8472 caracteres
```

en:

```text
1800
1800
1800
1800
1272
```

y enviamos todos esos elementos dentro de `rich_text`.

Así no dependemos de un único fragmento.

---

# 6. El punto más importante: actualizar, no crear

La lógica ahora es explícitamente:

```text
Linear
BI-123
  │
  ▼
Buscar en BI_INITIATIVES
"Linear ID" = "BI-123"
  │
  ├── encontrado
  │      │
  │      ▼
  │   PATCH /v1/pages/{page_id}
  │      │
  │      ▼
  │   ACTUALIZAR
  │
  └── no encontrado
         │
         ▼
      POST /v1/pages
         │
         ▼
       CREAR
```

Por lo tanto, si tienes:

```text
BI-123
```

en Notion y en Linear modificas:

```text
Descripción
Modelo de Datos
Prioridad
Owner
Estado
Proyecto
```

el siguiente workflow debería encontrar:

```text
Linear ID = BI-123
```

y hacer:

```text
PATCH
```

sobre **la misma página de Notion**.

No debería crear otra.

---

# 7. Una mejora que te recomiendo hacer después

Hay una limitación todavía en el script: `issues(first: 100)` significa que si algún día tienes más de 100 issues, los restantes no se sincronizarán.

Para una automatización estable, el siguiente paso sería implementar **paginación con `pageInfo` + `endCursor`** y, todavía mejor, utilizar `updatedAt` de Linear para sincronizar únicamente los issues que hayan cambiado desde la última ejecución.

Eso nos permitiría pasar de:

```text
Cada 12 horas
   ↓
Traer 100 issues
   ↓
Comparar todos
```

a:

```text
Cada 10/15 minutos
       ↓
¿qué cambió en Linear?
       ↓
solo esos issues
       ↓
actualizar sus registros en Notion
```

Eso sería bastante más eficiente y encaja mejor con lo que estás buscando: **Linear como origen de cambios y BI_INITIATIVES como reflejo actualizado del issue, sin duplicados.**
