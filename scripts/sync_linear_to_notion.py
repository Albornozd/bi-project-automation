import os
from linear import LinearClient
from notion_client import Client

# --- Configuración ---
LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DB_ID = os.environ.get("BI_INITIATIVES_DB")

linear_client = LinearClient(api_key=LINEAR_API_KEY)
notion = Client(auth=NOTION_API_KEY)

# Diccionario para mapear labels de Linear a campos de Notion
LABEL_MAPPING = {
    "Sociedad": {
        "Aristocrazy": "Aristocrazy",
        "Suarez": "Suarez",
        "Grupo": "Grupo"
    },
    "Esfuerzo": {
        "XL": "XL",
        "L": "L",
        "M": "M",
        "S": "S"
    },
    "Impacto": {
        "Alto": "Alto",
        "Medio": "Medio",
        "Bajo": "Bajo"
    },
    "Prioridad": {
        "Alta": "Alta",
        "Media": "Media",
        "Baja": "Baja"
    },
    "Tipo de Proyecto": {
        "Dashboard": "Dashboard",
        "Data model": "Data model",
        "Data Pipeline": "Data Pipeline",
        "Analysis": "Analysis"
    },
    "Tipo de Trabajo": {
        "Funcionalidad (Feature)": "Funcionalidad (Feature)",
        "Mejora (Improvement)": "Mejora (Improvement)",
        "Cambio (Change)": "Cambio (Change)"
    }
}

# --- Función para extraer labels ---
def map_labels(issue_labels, field_name):
    mapped = []
    for label in issue_labels:
        name = label.get("name")
        if name in LABEL_MAPPING.get(field_name, {}):
            mapped.append(LABEL_MAPPING[field_name][name])
    return mapped if mapped else None

# --- Función principal ---
def sync_issues():
    issues = linear_client.issues()  # Ajusta el query si quieres filtrar por proyecto
    for issue in issues:
        try:
            issue_labels = issue.labels.nodes if hasattr(issue.labels, "nodes") else []

            # Mapeo de campos de texto o fecha
            properties = {
                "Nombre": {"title": [{"text": {"content": issue.title}}]},
                "Descripcion": {"rich_text": [{"text": {"content": issue.description or ""}}]},
                "Owner": {"people": [{"name": issue.assignee.name}]} if issue.assignee else None,
                "Due Date": {"date": {"start": issue.dueDate}} if issue.dueDate else None,
                "Estado": {"status": {"name": issue.state.name}}
            }

            # Mapeo de labels a campos Notion
            for field in ["Sociedad", "Esfuerzo", "Impacto", "Prioridad", "Tipo de Proyecto", "Tipo de Trabajo"]:
                mapped = map_labels(issue_labels, field)
                if mapped:
                    properties[field] = {"multi_select": [{"name": val} for val in mapped]}

            # Limpieza de None
            properties = {k: v for k, v in properties.items() if v is not None}

            # Crear o actualizar página en Notion
            notion.pages.create(
                parent={"database_id": NOTION_DB_ID},
                properties=properties
            )
            print(f"Issue sincronizado: {issue.title}")
        except Exception as e:
            print("Error creando tarea en Notion:", e)

if __name__ == "__main__":
    sync_issues()
