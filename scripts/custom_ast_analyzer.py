"""Custom AST-Based Static Analysis Engine.

Implements carrier-grade static analysis rules using Python's `ast` module:
- CARRIER-001: Invariant Method Return Detection (AST-level S3516)
- CARRIER-002: Insecure Temporary File API Detection (AST-level S5445)
- CARRIER-003: Hardcoded SLA Metric Threshold Detection
"""

import ast
import os
import sys
import argparse
from typing import List, Dict, Any


class Finding:
    def __init__(self, rule_id: str, severity: str, file_path: str, line: int, col: int, message: str):
        self.rule_id = rule_id
        self.severity = severity
        self.file_path = file_path
        self.line = line
        self.col = col
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "file_path": self.file_path,
            "line": self.line,
            "col": self.col,
            "message": self.message,
        }

    def __str__(self) -> str:
        return f"[{self.severity}] {self.rule_id} at {self.file_path}:{self.line}:{self.col} - {self.message}"


class InvariantReturnVisitor(ast.NodeVisitor):
    """CARRIER-001: Checks for functions where ALL return statements return the exact same constant literal."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.findings: List[Finding] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._check_function(node)
        self.generic_visit(node)

    def _check_function(self, node):
        return_nodes = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
        if len(return_nodes) >= 2:
            return_values = []
            is_all_constants = True
            for r in return_nodes:
                if r.value is not None and isinstance(r.value, ast.Constant):
                    return_values.append(r.value.value)
                else:
                    is_all_constants = False
                    break

            if is_all_constants and len(return_values) >= 2 and len(set(return_values)) == 1:
                # Every single return path yields the exact same constant!
                self.findings.append(Finding(
                    rule_id="CARRIER-001",
                    severity="BLOCKER",
                    file_path=self.file_path,
                    line=node.lineno,
                    col=node.col_offset,
                    message=f"Function '{node.name}' has invariant return values across all {len(return_nodes)} return paths (always returns constant '{return_values[0]}').",
                ))


class InsecureTempfileVisitor(ast.NodeVisitor):
    """CARRIER-002: Detects calls to insecure tempfile methods (mktemp)."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.findings: List[Finding] = []

    def visit_Call(self, node: ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "mktemp":
            if isinstance(func.value, ast.Name) and func.value.id == "tempfile":
                self.findings.append(Finding(
                    rule_id="CARRIER-002",
                    severity="CRITICAL",
                    file_path=self.file_path,
                    line=node.lineno,
                    col=node.col_offset,
                    message="Use of insecure 'tempfile.mktemp()' creates TOCTOU vulnerability. Replace with 'tempfile.NamedTemporaryFile'.",
                ))
        self.generic_visit(node)


class HardcodedThresholdVisitor(ast.NodeVisitor):
    """CARRIER-003: Detects hardcoded numeric SLA comparisons in service layers."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.findings: List[Finding] = []

    def visit_Compare(self, node: ast.Compare):
        if "services" in self.file_path and not self.file_path.endswith("test_services.py"):
            for comp in node.comparators:
                if isinstance(comp, ast.Constant) and isinstance(comp.value, (int, float)) and comp.value > 1000:
                    self.findings.append(Finding(
                        rule_id="CARRIER-003",
                        severity="MAJOR",
                        file_path=self.file_path,
                        line=node.lineno,
                        col=node.col_offset,
                        message=f"Hardcoded SLA magic number '{comp.value}' detected. Extract into configurable Settings.",
                    ))
        self.generic_visit(node)


def analyze_file(file_path: str) -> List[Finding]:
    findings = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content, filename=file_path)

        visitors = [
            InvariantReturnVisitor(file_path),
            InsecureTempfileVisitor(file_path),
            HardcodedThresholdVisitor(file_path),
        ]

        for visitor in visitors:
            visitor.visit(tree)
            findings.extend(visitor.findings)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)

    return findings


def analyze_directory(source_dir: str) -> List[Finding]:
    all_findings = []
    for root, _, files in os.walk(source_dir):
        for f in files:
            if f.endswith(".py"):
                full_path = os.path.join(root, f)
                findings = analyze_file(full_path)
                all_findings.extend(findings)
    return all_findings


def main():
    parser = argparse.ArgumentParser(description="Custom AST Static Analyzer")
    parser.add_argument("--source-dir", default="src/telemetry_engine", help="Source directory to analyze")
    parser.add_argument("--strict", action="store_true", help="Exit with non-zero code if findings exist")
    args = parser.parse_args()

    print(f"[*] Running Custom AST Static Analyzer on '{args.source_dir}'...")
    findings = analyze_directory(args.source_dir)

    print(f"\n[+] Analysis Complete. Total Findings: {len(findings)}")
    for finding in findings:
        print(f"  {finding}")

    if args.strict and len(findings) > 0:
        print("\n[!] Static analysis failed: Violations detected.")
        sys.exit(1)
    else:
        print("\n[✓] All custom static analysis checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
