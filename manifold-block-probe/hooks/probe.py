#!/usr/bin/env python3
"""Blocking probe. Reads the hook payload on stdin, records its shape, and denies
only when the marker appears in the one field that event carries."""
import json, os, sys, datetime

LOG = "/tmp/manifold-block-probe.log"
MARKER = "MFDENY" + "-7Q2"          # split so this file never contains it whole

event = sys.argv[1] if len(sys.argv) > 1 else "unknown"
raw = sys.stdin.read()
try:
    payload = json.loads(raw)
except Exception:
    payload = {}

# Match the specific field only. Whole-payload matching broke co-work in the POC,
# because cwd and transcript_path travel in the same object.
if event == "UserPromptSubmit":
    field = "prompt" if "prompt" in payload else ("user_prompt" if "user_prompt" in payload else None)
    hay = str(payload.get(field, "")) if field else ""
else:
    field = "tool_input"
    hay = json.dumps(payload.get("tool_input", ""))

hit = MARKER in hay

with open(LOG, "a") as fh:
    fh.write("{} event={} remote={} keys={} field={} hit={} tool={}\n".format(
        datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        event,
        os.environ.get("CLAUDE_CODE_REMOTE", "false"),
        ",".join(sorted(payload.keys())) or "NONE",
        field, hit, payload.get("tool_name", "-")))

if not hit:
    sys.exit(0)

# v0.1.0 emitted {"decision": "block"} here, the shape the August POC used, and the
# session hung for minutes and could not be stopped. PreToolUse with hookSpecificOutput
# denied cleanly in the same run, so this now uses the same shape for both events.
out = {"hookSpecificOutput": {
    "hookEventName": event,
    "permissionDecision": "deny",
    "permissionDecisionReason": "manifold-block-probe: marker in {}".format(
        "prompt" if event == "UserPromptSubmit" else "tool_input")}}

with open(LOG, "a") as fh:
    fh.write("   emitted={}\n".format(json.dumps(out)))
print(json.dumps(out))
sys.exit(0)
