"""Unit tests for custom AST static analyzer engine."""

import ast
from scripts.custom_ast_analyzer import (
    InvariantReturnVisitor,
    InsecureTempfileVisitor,
    HardcodedThresholdVisitor,
    analyze_file,
)


def test_invariant_return_visitor():
    code = """
def bad_func(x):
    if x > 10:
        return True
    elif x == 5:
        return True
    else:
        return True
"""
    tree = ast.parse(code)
    visitor = InvariantReturnVisitor("test.py")
    visitor.visit(tree)
    assert len(visitor.findings) == 1
    assert visitor.findings[0].rule_id == "CARRIER-001"
    assert "invariant return" in visitor.findings[0].message


def test_insecure_tempfile_visitor():
    code = """
import tempfile
def make_temp():
    return tempfile.mktemp()
"""
    tree = ast.parse(code)
    visitor = InsecureTempfileVisitor("test.py")
    visitor.visit(tree)
    assert len(visitor.findings) == 1
    assert visitor.findings[0].rule_id == "CARRIER-002"


def test_analyzer_on_refactored_code():
    findings = analyze_file("src/telemetry_engine/auth/jwt_handler.py")
    assert len(findings) == 0
