import os
import json
from openai import OpenAI, OpenAIError

INPUT_FILE = os.getenv("INPUT_FILE", "data/linear_issues.json")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "reports/backlog_report.md")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# Cargar issues de Linear
try:
    with open(INPUT_FILE, encoding="utf-8") as f:
        issues = json.load(f)
except FileNotFoundError:
    issues = []
    print(f"Archivo {INPUT_FILE} no encontrado. Generando reporte vacío.")

# Preparar contenido del reporte
report_lines = ["# Backlog / BI Report\n"]
report_lines.append("Nota: OpenAI falló, reporte estándar.\n")

# Agregar detalle de cada issue
for i in issues:
    assignee = i.get("assignee")
    assignee_name = assignee.get("name") if isinstance(assignee, dict) else assignee or "Sin asignar"
    
    team = i.get("team")
    team_name = team.get("name") if isinstance(team, dict) else team or "Sin Team"
    
    project = i.get("project")
    project_name = project.get("name") if isinstance(project, dict) else project or "Sin Project"
    
    state = i.get("state")
    state_name = state.get("name") if isinstance(state, dict) else state or "Sin Estado"
    
    due_date = i.get("due_date", "Sin Due Date")
    
    labels = i.get("labels", [])
    labels_str = ", ".join(labels)
    
    report_lines.append(
        f"- [{team_name}/{project_name}] {i.get('title', 'Sin título')} | "
        f"Asignado a: {assignee_name} | Estado: {state_name} | Due Date: {due_date} | Labels: {labels_str}\n"
    )

report_text = "".join(report_lines)

# Intentar generar resumen con OpenAI
if OPENAI_KEY:
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente que resume issues de BI."},
                {"role": "user", "content": report_text}
            ],
            temperature=0.5
        )
        report_text = response.choices[0].message.content
    except OpenAIError as e:
        print(f"OpenAI falló: {e}. Se mantendrá reporte estándar.")

# Guardar reporte
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(report_text)
