import os
import json
from pathlib import Path
import openai

INPUT_FILE = os.getenv("INPUT_FILE", "data/linear_issues.json")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "reports/roadmap.md")

Path("reports").mkdir(parents=True, exist_ok=True)

# Leer issues de Linear
try:
    with open(INPUT_FILE, encoding="utf-8") as f:
        issues = json.load(f)
except FileNotFoundError:
    print(f"Error: no se encontró {INPUT_FILE}")
    issues = []

# Función para generar reporte estándar
def generar_reporte_estandar(issues):
    report = "# Roadmap BI - Reporte Estándar\n\n"
    for i in issues:
        report += f"- **[{i.get('team', 'Sin Team')}/{i.get('project', 'Sin Project')}] {i.get('name', 'Sin nombre')}**\n"
        report += f"  - Estado: {i.get('status', 'Sin estado')}\n"
        report += f"  - Due Date: {i.get('due_date', 'No asignado')}\n"
        report += f"  - Asignado a: {i.get('assignee', 'Sin asignar')}\n"
        labels = i.get("labels", {})
        for label_group in ["Departamento", "Impacto en Negocio", "Esfuerzo Estimado", "Prioridad", "Sociedad", "Tipo de Proyecto", "Tipo de Trabajo"]:
            value = labels.get(label_group, "No definido")
            report += f"  - {label_group}: {value}\n"
        report += "\n"
    return report

# Intentar generar con OpenAI
report_text = ""
try:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = (
        "Genera un roadmap BI en formato Markdown basado en los siguientes issues:\n\n"
        f"{json.dumps(issues, indent=2)}\n\n"
        "Incluye: nombre, estado, due date, assignee, proyecto, team, y labels. "
        "Si algún campo no existe, indícalo como 'No definido'."
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    report_text = response.choices[0].message.content
except openai.OpenAIError as e:
    print(f"OpenAI falló, generando reporte estándar. Error: {e}")
    report_text = generar_reporte_estandar(issues)
except Exception as e:
    print(f"Ocurrió un error inesperado con OpenAI: {e}")
    report_text = generar_reporte_estandar(issues)

# Guardar reporte
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(report_text)

print(f"Reporte generado en {OUTPUT_FILE}")
