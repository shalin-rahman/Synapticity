"""
Import smoke test — verifies all refactored modules load without errors.
Run: python scratch/smoke_test.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

results = []

def check(label, fn):
    try:
        fn()
        results.append(("OK", label))
    except Exception as e:
        results.append(("FAIL", f"{label} -> {e}"))

# --- CLI package ---
check("synaptic.cli",                    lambda: __import__("synaptic.cli"))
check("synaptic.cli.utils",              lambda: __import__("synaptic.cli.utils"))
check("synaptic.cli.ui",                 lambda: __import__("synaptic.cli.ui"))
check("synaptic.cli.registry",           lambda: __import__("synaptic.cli.registry"))
check("synaptic.cli.handlers.mission",   lambda: __import__("synaptic.cli.handlers.mission"))
check("synaptic.cli.handlers.observe",   lambda: __import__("synaptic.cli.handlers.observe"))
check("synaptic.cli.handlers.integration", lambda: __import__("synaptic.cli.handlers.integration"))
check("synaptic.cli.handlers.review",    lambda: __import__("synaptic.cli.handlers.review"))

# --- Core mission sub-systems ---
check("synaptic.core.mission_state",     lambda: __import__("synaptic.core.mission_state"))
check("synaptic.core.mission_logger",    lambda: __import__("synaptic.core.mission_logger"))
check("synaptic.core.mission_workspace", lambda: __import__("synaptic.core.mission_workspace"))
check("synaptic.core.mission_gate",      lambda: __import__("synaptic.core.mission_gate"))
check("synaptic.core.mission_phases",    lambda: __import__("synaptic.core.mission_phases"))
check("synaptic.core.agent_dispatcher",  lambda: __import__("synaptic.core.agent_dispatcher"))
check("synaptic.core.mission_engine",    lambda: __import__("synaptic.core.mission_engine"))
check("synaptic.core.project_review_engine", lambda: __import__("synaptic.core.project_review_engine"))

# --- Utilities ---
check("synaptic.utils.project_indexer",  lambda: __import__("synaptic.utils.project_indexer"))
check("synaptic.utils.git_deployer",     lambda: __import__("synaptic.utils.git_deployer"))
check("synaptic.utils.resource_fetcher", lambda: __import__("synaptic.utils.resource_fetcher"))
check("synaptic.utils.memory_logger",    lambda: __import__("synaptic.utils.memory_logger"))

# --- Report ---
print("\n[SMOKE TEST] Import Validation Results")
print("-" * 50)
passed = failed = 0
for status, label in results:
    tag = "[OK]  " if status == "OK" else "[FAIL]"
    print(f"  {tag} {label}")
    if status == "OK": passed += 1
    else:              failed += 1

print("-" * 50)
print(f"  Passed: {passed} | Failed: {failed} | Total: {len(results)}")
sys.exit(1 if failed else 0)
