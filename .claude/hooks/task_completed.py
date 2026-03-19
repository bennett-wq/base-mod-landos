#!/usr/bin/env python3
import json, sys, subprocess
from pathlib import Path

repo = (Path(__file__).resolve().parents[2] / "landos")
result = subprocess.run(
    ["python3", "-m", "pytest", "tests/", "--tb=no", "-q"],
    cwd=str(repo), capture_output=True, text=True, timeout=120
)
if result.returncode != 0:
    print(f"Task blocked — tests failing:\n{result.stdout[-1000:]}", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
