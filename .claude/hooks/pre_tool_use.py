#!/usr/bin/env python3
import json, sys
data = json.load(sys.stdin)
tool = data.get("tool_name", "")
tool_input = data.get("tool_input", {})
blocked = False
reason = ""
if tool == "Bash":
    cmd = tool_input.get("command", "")
    if "rm -rf" in cmd and "/landos/" not in cmd:
        blocked = True
        reason = f"rm -rf outside landos/ blocked: {cmd[:100]}"
if tool in ("Read", "Write", "Edit"):
    path = str(tool_input.get("file_path", ""))
    if ".env" in path or "private_key" in path.lower():
        blocked = True
        reason = f"Sensitive file blocked: {path}"
if blocked:
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)
print(json.dumps({"decision": "allow"}))
