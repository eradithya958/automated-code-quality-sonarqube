"""Automated Prioritization Engine and Import Graph Analyzer for Static Analysis Findings.

Computes Blast Radius via AST import analysis and scores issues using a
Risk-Weighted Prioritization Framework tailored for carrier-grade CI environments.
"""

import ast
import os
import json
import csv
from typing import Dict, Set, List, Any


def build_import_graph(src_dir: str) -> Dict[str, Set[str]]:
    """Analyzes AST imports across all Python files to determine module dependencies.
    Returns a mapping of {module_path: set_of_dependents} (Blast Radius).
    """
    file_modules = {}
    for root, _, files in os.walk(src_dir):
        for f in files:
            if f.endswith(".py"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, ".")
                # e.g., src.telemetry_engine.models.device
                mod_name = rel_path.replace("/", ".").replace(".py", "")
                if mod_name.endswith(".__init__"):
                    mod_name = mod_name[:-9]
                file_modules[rel_path] = mod_name

    # Inverted graph: target_file -> set of files importing it
    dependents_graph = {rel_path: set() for rel_path in file_modules}

    for rel_path, mod_name in file_modules.items():
        try:
            with open(rel_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=rel_path)

            for node in ast.walk(tree):
                imported_module = None
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_module = alias.name
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        if node.level > 0:
                            # Relative import
                            pkg_parts = mod_name.split(".")[:-node.level]
                            imported_module = ".".join(pkg_parts + [node.module])
                        else:
                            imported_module = node.module

                if imported_module:
                    for target_file, target_mod in file_modules.items():
                        if target_file != rel_path:
                            if imported_module == target_mod or imported_module.startswith(target_mod + "."):
                                dependents_graph[target_file].add(rel_path)
        except Exception as e:
            print(f"Error parsing AST for {rel_path}: {e}")

    return dependents_graph


def calculate_priority_score(
    severity: str,
    issue_type: str,
    debt_minutes: int,
    blast_radius: int,
) -> float:
    """Calculates composite Priority Score (0 - 100 scale).

    Formula Components:
    1. Severity Weight (W_sev): Blocker=10, Critical=8, Major=5, Minor=2, Info=1
    2. Type Multiplier (M_type): Vulnerability=1.5, Bug=1.35, Hotspot=1.2, Code Smell=1.0
    3. Blast Radius Factor (F_blast): 1.0 + (0.25 * blast_radius)
    4. Effort Factor (F_effort): 1.0 + min(debt_minutes / 30.0, 1.5)
    """
    sev_weights = {
        "BLOCKER": 10.0,
        "CRITICAL": 8.0,
        "MAJOR": 5.0,
        "MINOR": 2.0,
        "INFO": 1.0,
    }
    type_multipliers = {
        "VULNERABILITY": 1.50,
        "BUG": 1.35,
        "SECURITY_HOTSPOT": 1.20,
        "CODE_SMELL": 1.00,
    }

    w_sev = sev_weights.get(severity.upper(), 3.0)
    m_type = type_multipliers.get(issue_type.upper(), 1.0)
    f_blast = 1.0 + (0.25 * blast_radius)
    f_effort = 1.0 + min(debt_minutes / 30.0, 1.5)

    raw_score = (w_sev * m_type) * f_blast * (1.0 + (debt_minutes / 60.0))
    # Normalize to 0-100 scale
    normalized_score = min(round(raw_score * 2.2, 1), 100.0)
    return normalized_score


def parse_debt_to_minutes(debt_str: str) -> int:
    """Parses debt string like '2min', '15min', '1h', '37min' to integer minutes."""
    if not debt_str:
        return 5
    debt_str = debt_str.strip().lower()
    total = 0
    if "h" in debt_str:
        parts = debt_str.split("h")
        total += int(parts[0]) * 60
        if "min" in parts[1]:
            total += int(parts[1].replace("min", ""))
    elif "min" in debt_str:
        total += int(debt_str.replace("min", ""))
    else:
        try:
            total = int(debt_str)
        except ValueError:
            total = 5
    return total


def run_prioritization():
    src_dir = "src"
    graph = build_import_graph(src_dir)
    print("Computed AST Blast Radius (incoming dependents count):")
    for file_path, dependents in sorted(graph.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  - {file_path}: {len(dependents)} dependents -> {list(dependents)}")

    with open("reports/baseline_issues.json", "r", encoding="utf-8") as f:
        issues_data = json.load(f)
    with open("reports/baseline_hotspots.json", "r", encoding="utf-8") as f:
        hotspots_data = json.load(f)

    prioritized_list = []

    # Process Standard Issues
    for issue in issues_data.get("issues", []):
        comp = issue.get("component", "").split(":")[-1]
        blast_radius = len(graph.get(comp, []))
        debt_min = parse_debt_to_minutes(issue.get("debt", "5min"))
        sev = issue.get("severity", "MAJOR")
        itype = issue.get("type", "CODE_SMELL")

        score = calculate_priority_score(sev, itype, debt_min, blast_radius)

        # Technical justification generator
        justification = (
            f"Severity={sev}, Type={itype}, Blast Radius={blast_radius} dependents. "
            f"Rule {issue.get('rule')} in core component {os.path.basename(comp)}."
        )

        prioritized_list.append({
            "key": issue.get("key"),
            "rule": issue.get("rule"),
            "severity": sev,
            "type": itype,
            "component": comp,
            "line": issue.get("line", 0),
            "message": issue.get("message"),
            "debt_minutes": debt_min,
            "blast_radius": blast_radius,
            "priority_score": score,
            "justification": justification,
        })

    # Process Security Hotspots
    for spot in hotspots_data.get("hotspots", []):
        comp = spot.get("component", "").split(":")[-1]
        blast_radius = len(graph.get(comp, []))
        debt_min = 10
        sev = "CRITICAL" if spot.get("vulnerabilityProbability") == "HIGH" else "MAJOR"
        itype = "SECURITY_HOTSPOT"
        score = calculate_priority_score(sev, itype, debt_min, blast_radius)

        prioritized_list.append({
            "key": spot.get("key"),
            "rule": spot.get("ruleKey"),
            "severity": sev,
            "type": itype,
            "component": comp,
            "line": spot.get("line", 0),
            "message": spot.get("message"),
            "debt_minutes": debt_min,
            "blast_radius": blast_radius,
            "priority_score": score,
            "justification": f"Security Hotspot ({spot.get('securityCategory')}) requiring audit on {os.path.basename(comp)}.",
        })

    # Sort descending by priority score
    prioritized_list.sort(key=lambda x: x["priority_score"], reverse=True)

    # Save to JSON and CSV
    with open("reports/prioritized_backlog.json", "w", encoding="utf-8") as f:
        json.dump(prioritized_list, f, indent=2)

    fieldnames = [
        "rank",
        "key",
        "rule",
        "severity",
        "type",
        "component",
        "line",
        "priority_score",
        "debt_minutes",
        "blast_radius",
        "message",
        "justification",
    ]

    with open("reports/prioritized_backlog.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, item in enumerate(prioritized_list, 1):
            row = dict(item)
            row["rank"] = idx
            writer.writerow(row)

    print(f"\nGenerated Prioritized Remediation Backlog with {len(prioritized_list)} items.")
    print("\nTop 5 Prioritized Items:")
    for idx, item in enumerate(prioritized_list[:5], 1):
        print(f"  #{idx} [Score {item['priority_score']}] {item['rule']} ({item['severity']} {item['type']}) in {item['component']}:{item['line']}")


if __name__ == "__main__":
    run_prioritization()
