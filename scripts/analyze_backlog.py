import json

with open("data/linear_issues.json") as f:
    data = json.load(f)

issues = data["data"]["issues"]["nodes"]

print(f"Total issues: {len(issues)}")

summary = {}

for issue in issues:
    state = issue["state"]["name"]

    if state not in summary:
        summary[state] = 0

    summary[state] += 1

print("Resumen por estado:")

for state, count in summary.items():
    print(f"{state}: {count}")
