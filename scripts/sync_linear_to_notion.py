import os
import requests

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("BI_INITIATIVES_DB")

LINEAR_URL = "https://api.linear.app/graphql"
NOTION_URL = "https://api.notion.com/v1"

# -------------------------
# Label mapping
# -------------------------

label_mapping = {

"Digital": ("Departamento","Digital"),
"BI": ("Departamento","BI"),
"RRHH": ("Departamento","RRHH"),
"IT": ("Departamento","IT"),
"Finanzas": ("Departamento","Finanzas"),
"Administración": ("Departamento","Administración"),
"Logística": ("Departamento","Logística"),
"Producto": ("Departamento","Producto"),
"Retail": ("Departamento","Retail"),
"Marketing": ("Departamento","Marketing"),
"Postventa": ("Departamento","Postventa"),
"Gemología": ("Departamento","Gemología"),
"Relojería": ("Departamento","Relojería"),
"Diseño": ("Departamento","Diseño"),
"Proyecto FABRIC": ("Departamento","Proyecto FABRIC"),
"Producción (Fabricación)": ("Departamento","Producción (Fabricación)"),

"Aristocrazy": ("Sociedad","Aristocrazy"),
"Suarez": ("Sociedad","Suarez"),
"Grupo": ("Sociedad","Grupo"),

"XL": ("Esfuerzo","XL"),
"L": ("Esfuerzo","L"),
"M": ("Esfuerzo","M"),
"S": ("Esfuerzo","S"),

"Alto": ("Impacto","Alto"),
"Medio": ("Impacto","Medio"),
"Bajo": ("Impacto","Bajo"),

"Alta": ("Prioridad","Alta"),
"Media": ("Prioridad","Media"),
"Baja": ("Prioridad","Baja"),

"Dashboard": ("Tipo Proyecto","Dashboard"),
"Data model": ("Tipo Proyecto","Data model"),
"Data Pipeline": ("Tipo Proyecto","Data Pipeline"),
"Analysis": ("Tipo Proyecto","Analysis"),

"Funcionalidad (Feature)": ("Tipo Trabajo","Funcionalidad (Feature)"),
"Mejora (Improvement)": ("Tipo Trabajo","Mejora (Improvement)"),
"Cambio (Change)": ("Tipo Trabajo","Cambio (Change)")
}

# -------------------------
# Linear query
# -------------------------

query = """
{
  issues(first:50){
    nodes{
      id
      title
      description
      dueDate
      state{ name }
      team{ name }
      project{ name }
      assignee{ name }
      labels{ nodes{ name } }
    }
  }
}
"""

headers_linear = {
"Authorization": LINEAR_API_KEY,
"Content-Type":"application/json"
}

response = requests.post(
LINEAR_URL,
headers=headers_linear,
json={"query":query}
)

issues = response.json()["data"]["issues"]["nodes"]

print("Issues fetched:",len(issues))

# -------------------------
# Notion headers
# -------------------------

headers_notion = {
"Authorization":f"Bearer {NOTION_API_KEY}",
"Content-Type":"application/json",
"Notion-Version":"2022-06-28"
}

# -------------------------
# Search issue in Notion
# -------------------------

def find_page(linear_id):

    url=f"{NOTION_URL}/databases/{DATABASE_ID}/query"

    payload={
        "filter":{
            "property":"Linear ID",
            "rich_text":{
                "equals":linear_id
            }
        }
    }

    res=requests.post(url,headers=headers_notion,json=payload)

    results=res.json()["results"]

    return results[0]["id"] if results else None

# -------------------------
# Build properties
# -------------------------

def build_properties(issue):

    labels = issue.get("labels",{}).get("nodes",[])

    mapped = {}

    for label in labels:

        name = label["name"]

        if name in label_mapping:

            field,value = label_mapping[name]

            mapped[field] = value

    assignee = issue.get("assignee")

    properties={

        "Nombre":{
            "title":[{"text":{"content":issue["title"]}}]
        },

        "Descripcion":{
            "rich_text":[{"text":{"content":issue.get("description") or ""}}]
        },

        "Estado":{
            "status":{"name":issue["state"]["name"]}
        },

        "Owner":{
            "rich_text":[{"text":{"content":assignee["name"] if assignee else ""}}]
        },

        "Due Date":{
            "date":{"start":issue["dueDate"]}
        } if issue.get("dueDate") else None,

        "Team":{
            "rich_text":[{"text":{"content":issue.get("team",{}).get("name","")}}]
        },

        "Proyecto":{
            "rich_text":[{"text":{"content":issue.get("project",{}).get("name","")}}]
        },

        "Linear ID":{
            "rich_text":[{"text":{"content":issue["id"]}}]
        }

    }

    for field,value in mapped.items():

        properties[field]={"select":{"name":value}}

    return {k:v for k,v in properties.items() if v}

# -------------------------
# Sync loop
# -------------------------

for issue in issues:

    linear_id = issue["id"]

    page_id = find_page(linear_id)

    properties = build_properties(issue)

    if page_id:

        print("Updating:",issue["title"])

        requests.patch(
            f"{NOTION_URL}/pages/{page_id}",
            headers=headers_notion,
            json={"properties":properties}
        )

    else:

        print("Creating:",issue["title"])

        requests.post(
            f"{NOTION_URL}/pages",
            headers=headers_notion,
            json={
                "parent":{"database_id":DATABASE_ID},
                "properties":properties
            }
        )
