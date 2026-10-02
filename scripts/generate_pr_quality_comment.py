"""Generates a GitHub PR Comment summarizing SonarQube Quality Gate results and static analysis deltas."""

import os
import json
import urllib.request
import base64


def generate_pr_comment():
    sonar_host = os.getenv("SONAR_HOST_URL", "http://localhost:9000").rstrip("/")
    sonar_token = os.getenv("SONAR_TOKEN", "admin:admin")
    project_key = "network-telemetry-engine"

    # Prepare Basic Auth header
    if ":" in sonar_token:
        auth_str = base64.b64encode(sonar_token.encode("utf-8")).decode("utf-8")
    else:
        auth_str = base64.b64encode(f"{sonar_token}:".encode("utf-8")).decode("utf-8")

    headers = {"Authorization": f"Basic {auth_str}"}

    # Fetch Quality Gate Status
    qg_url = f"{sonar_host}/api/qualitygates/project_status?projectKey={project_key}"
    measures_url = f"{sonar_host}/api/measures/component?component={project_key}&metricKeys=bugs,vulnerabilities,code_smells,security_hotspots,coverage,duplicated_lines_density,sqale_index"

    qg_status = "UNKNOWN"
    qg_conditions = []
    measures = {}

    try:
        req = urllib.request.Request(qg_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            qg_data = json.loads(resp.read().decode("utf-8"))
            qg_status = qg_data.get("projectStatus", {}).get("status", "UNKNOWN")
            qg_conditions = qg_data.get("projectStatus", {}).get("conditions", [])
    except Exception as e:
        print(f"Warning: Could not fetch Quality Gate status from {qg_url}: {e}")

    try:
        req = urllib.request.Request(measures_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            m_data = json.loads(resp.read().decode("utf-8"))
            for m in m_data.get("component", {}).get("measures", []):
                measures[m["metric"]] = m.get("value", "0")
    except Exception as e:
        print(f"Warning: Could not fetch component measures: {e}")

    # Build Markdown Summary
    status_badge = "🟢 **PASSED**" if qg_status == "OK" else "🔴 **FAILED**"

    md = []
    md.append("<!-- sonarqube-quality-gate-comment -->")
    md.append(f"## 🛡️ SonarQube Automated Quality Gate: {status_badge}\n")
    md.append(f"**Project**: `{project_key}` | **Status**: `{qg_status}`\n")
    md.append("### 📊 Key Quality Metrics\n")
    md.append("| Metric | Value | Target Threshold | Status |")
    md.append("| :--- | :---: | :---: | :---: |")
    md.append(f"| **Bugs** | `{measures.get('bugs', '0')}` | `0` | {'✅' if measures.get('bugs') == '0' else '❌'} |")
    md.append(f"| **Vulnerabilities** | `{measures.get('vulnerabilities', '0')}` | `0` | {'✅' if measures.get('vulnerabilities') == '0' else '❌'} |")
    md.append(f"| **Code Smells** | `{measures.get('code_smells', '0')}` | `0` | {'✅' if measures.get('code_smells') == '0' else '❌'} |")
    md.append(f"| **Security Hotspots** | `{measures.get('security_hotspots', '0')}` | `0` | {'✅' if measures.get('security_hotspots') == '0' else '❌'} |")
    md.append(f"| **Test Coverage** | `{measures.get('coverage', '0')}%` | `≥ 80.0%` | {'✅' if float(measures.get('coverage', 0)) >= 80.0 else '⚠️'} |")
    md.append(f"| **Duplications** | `{measures.get('duplicated_lines_density', '0')}%` | `< 3.0%` | {'✅' if float(measures.get('duplicated_lines_density', 0)) < 3.0 else '❌'} |")
    md.append(f"| **Technical Debt** | `{measures.get('sqale_index', '0')} min` | `0 min` | {'✅' if measures.get('sqale_index') == '0' else '⚠️'} |\n")

    if qg_conditions:
        md.append("### 🔍 Quality Gate Condition Details\n")
        md.append("| Condition Metric | Operator | Actual Value | Error Threshold | Status |")
        md.append("| :--- | :---: | :---: | :---: | :---: |")
        for cond in qg_conditions:
            c_status = "✅ PASS" if cond.get("status") == "OK" else "❌ FAIL"
            md.append(f"| `{cond.get('metricKey')}` | `{cond.get('comparator')}` | `{cond.get('actualValue', 'N/A')}` | `{cond.get('errorThreshold', 'N/A')}` | {c_status} |")
        md.append("")

    md.append("> *Automated Quality Check enforced by CI Pipeline before code review.*")

    os.makedirs("reports", exist_ok=True)
    with open("reports/pr_comment_summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print("Generated reports/pr_comment_summary.md successfully.")


if __name__ == "__main__":
    generate_pr_comment()
