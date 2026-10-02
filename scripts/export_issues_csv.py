"""Converts SonarQube raw JSON issue export into structured CSV format."""

import json
import csv
import sys


def json_to_csv(json_path: str, csv_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    issues = data.get("issues", [])
    if not issues:
        print("No issues found in JSON file.")
        return

    headers = [
        "key",
        "rule",
        "severity",
        "component",
        "line",
        "message",
        "type",
        "effort",
        "debt",
        "status",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for issue in issues:
            row = {
                "key": issue.get("key", ""),
                "rule": issue.get("rule", ""),
                "severity": issue.get("severity", ""),
                "component": issue.get("component", ""),
                "line": issue.get("line", ""),
                "message": issue.get("message", ""),
                "type": issue.get("type", ""),
                "effort": issue.get("effort", ""),
                "debt": issue.get("debt", ""),
                "status": issue.get("status", ""),
            }
            writer.writerow(row)

    print(f"Exported {len(issues)} issues to {csv_path}")


if __name__ == "__main__":
    src = "reports/baseline_issues.json"
    dst = "reports/baseline_issues.csv"
    json_to_csv(src, dst)
