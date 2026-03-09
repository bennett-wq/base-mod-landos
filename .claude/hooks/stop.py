#!/usr/bin/env python3
import json, sys, subprocess
from pathlib import Path

data = json.load(sys.stdin)
last_message = data.get("last_assistant_message", "")

if "LANDOS_STEP_COMPLETE" in last_message:
    repo = (Path(__file__).resolve().parents[2] / "landos")
    result = subprocess.run(
        ["python3", "-m", "pytest", "tests/", "-v", "--tb=no", "-q"],
        cwd=str(repo), capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        print(
            f"LANDOS_STEP_COMPLETE claimed but tests failed:\n{result.stdout[-2000:]}",
            file=sys.stderr
        )
        sys.exit(2)
sys.exit(0)
