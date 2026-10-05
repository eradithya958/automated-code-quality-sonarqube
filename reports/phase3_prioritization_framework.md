# Phase 3: Risk-Weighted Static Analysis Prioritization Framework

**Project**: `network-telemetry-engine`  
**Purpose**: Algorithmic scoring and backlog prioritization of static analysis findings for automated CI/CD and release readiness governance.

---

## 1. Prioritization Scoring Methodology

Default SonarQube severity alone does not account for the architectural impact of an issue or how widely a defective module is consumed by the rest of the system. To address this, our framework computes a **Risk-Weighted Priority Score (RWPS)**:

$$\text{RWPS} = (W_{\text{sev}} \times M_{\text{type}}) \times F_{\text{blast}} \times F_{\text{effort}}$$

### 1.1 Mathematical Components & Parameter Weights

1. **Base Severity Weight ($W_{\text{sev}}$)**:
   - **BLOCKER**: `10.0`
   - **CRITICAL**: `8.0`
   - **MAJOR**: `5.0`
   - **MINOR**: `2.0`
   - **INFO**: `1.0`

2. **Issue Type Multiplier ($M_{\text{type}}$)**:
   - **VULNERABILITY**: `1.50`
   - **BUG**: `1.35`
   - **SECURITY HOTSPOT**: `1.20`
   - **CODE SMELL**: `1.00`

3. **Blast Radius Factor ($F_{\text{blast}}$)**:
   Calculated via Python Abstract Syntax Tree (AST) import graph analysis measuring how many downstream modules depend on the affected component ($D_{\text{in}}$):
   $$F_{\text{blast}} = 1.0 + (0.25 \times D_{\text{in}})$$

4. **Effort Scaling Factor ($F_{\text{effort}}$)**:
   Calibrates the fix urgency and complexity based on SonarQube SQALE debt-minutes ($T_{\text{debt}}$):
   $$F_{\text{effort}} = 1.0 + \frac{T_{\text{debt}}}{60.0}$$

---

## 2. AST Import Graph & Blast Radius Summary

- `auth/jwt_handler.py`: **3 dependents** (`api/routes_devices`, `api/routes_telemetry`, `api/routes_alerts`) → **HIGH BLAST RADIUS**
- `models/device.py`: **2 dependents** (`services/device_manager`, `api/routes_devices`) → **MEDIUM BLAST RADIUS**
- `auth/permissions.py`: **2 dependents** (`api/routes_devices`, `api/routes_alerts`) → **MEDIUM BLAST RADIUS**
- `services/aggregation_service.py`: **1 dependent** (`api/routes_telemetry`) → **LOW BLAST RADIUS**
- `utils/file_utils.py`: **1 dependent** (`services/ingestion_service`) → **LOW BLAST RADIUS**

---

## 3. Prioritized Remediation Backlog

1. **Rank #1** [`jwt_handler.py:138`](../src/telemetry_engine/auth/jwt_handler.py#L138): `python:S3516` (Score: 39.8, Blocker, 3 dependents)
2. **Rank #2** [`file_utils.py:17`](../src/telemetry_engine/utils/file_utils.py#L17): `python:S5445` (Score: 38.5, Critical Vulnerability, TOCTOU symlink)
3. **Rank #3** [`aggregation_service.py:103`](../src/telemetry_engine/services/aggregation_service.py#L103): `python:S3776` (Score: 35.6, Critical Smell, Cognitive Complexity 47 vs 15)
4. **Rank #4** [`device.py:51`](../src/telemetry_engine/models/device.py#L51): `python:S3516` (Score: 34.1, Blocker Smell, 2 dependents)
5. **Rank #5** [`jwt_handler.py:158`](../src/telemetry_engine/auth/jwt_handler.py#L158): `python:S1192` (Score: 33.9, Critical Smell, Duplicated literal)
6. **Rank #6** [`jwt_handler.py:145`](../src/telemetry_engine/auth/jwt_handler.py#L145): `python:S3923` (Score: 32.5, Major Bug)
7. **Rank #7-#10** [`permissions.py`](../src/telemetry_engine/auth/permissions.py): `python:S1192` (Scores: 30.8 - 29.0, Critical Smells, 4 string literals duplicated)
8. **Rank #11** [`aggregation_service.py:150`](../src/telemetry_engine/services/aggregation_service.py#L150): `python:S3516` (Score: 28.4, Blocker Smell, SLA compliance logic)
9. **Rank #12** [`device.py:55`](../src/telemetry_engine/models/device.py#L55): `python:S3923` (Score: 27.8, Major Bug)
10. **Rank #13** [`permissions.py:83`](../src/telemetry_engine/auth/permissions.py#L83): `python:S5797` (Score: 27.3, Critical Smell, Constant condition)
11. **Rank #14** [`routes_telemetry.py:27`](../src/telemetry_engine/api/routes_telemetry.py#L27): `python:S3516` (Score: 22.7, Blocker Smell)
12. **Rank #15** [`alert_evaluator.py:51`](../src/telemetry_engine/services/alert_evaluator.py#L51): `python:S1764` (Score: 19.2, Major Bug)
13. **Rank #16** [`file_utils.py:46`](../src/telemetry_engine/utils/file_utils.py#L46): `python:S4790` (Score: 19.2, Hotspot)
14. **Rank #17** [`routes_telemetry.py:32`](../src/telemetry_engine/api/routes_telemetry.py#L32): `python:S3923` (Score: 18.6, Major Bug)
15. **Rank #18** [`config.py:15`](../src/telemetry_engine/config.py#L15): `python:S5443` (Score: 15.4, Hotspot)
