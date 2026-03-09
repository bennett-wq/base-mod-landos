#!/usr/bin/env python3
import json, sys, urllib.request, os
from datetime import datetime
data = json.load(sys.stdin)
event = {
    "hook": "PostToolUse",
    "session_id": os.environ.get("CLAUDE_SESSION_ID", "unknown"),
    "tool_name": data.get("tool_name"),
    "timestamp": datetime.utcnow().isoformat()
}
try:
    req = urllib.request.Request(
        "http://localhost:4000/hook",
        data=json.dumps(event).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=1)
except Exception:
    pass
sys.exit(0)
