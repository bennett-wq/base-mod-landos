#!/usr/bin/env python3
import json, sys, os
from datetime import datetime
data = json.load(sys.stdin)
log_path = os.path.expanduser("~/.claude/landos-subagent-log.txt")
with open(log_path, "a") as f:
    f.write(
        f"{datetime.utcnow().isoformat()} | "
        f"session={os.environ.get('CLAUDE_SESSION_ID','?')} | "
        f"last={data.get('last_assistant_message','')[:100]}\n"
    )
sys.exit(0)
