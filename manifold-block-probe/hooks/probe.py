#!/usr/bin/env python3
"""Blocking probe. Records the payload shape, then denies using one of two output
shapes depending on which marker matched, so a single session shows which one works.

  marker A -> {"decision": "block"}                  the shape the August POC used
  marker B -> hookSpecificOutput/permissionDecision  confirmed working for PreToolUse,
                                                     observed to be ignored on prompts

PreToolUse denies on either marker and is the control: it is already known to work.
"""
import json, os, sys, datetime

LOG = "/tmp/manifold-block-probe.log"
A = "MFDENY" + "-7Q2"      # split so this file never contains either marker whole
B = "MFDENY" + "-8R3"

event = sys.argv[1] if len(sys.argv) > 1 else "unknown"
raw = sys.stdin.read()
try:
    payload = json.loads(raw)
except Exception:
    payload = {}

if event == "UserPromptSubmit":
    field = "prompt" if "prompt" in payload else ("user_prompt" if "user_prompt" in payload else "MISSING")
    hay = str(payload.get(field, ""))
else:
    field = "tool_input"
    hay = json.dumps(payload.get("tool_input", ""))

which = "A" if A in hay else ("B" if B in hay else None)

def log(line):
    with open(LOG, "a") as fh:
        fh.write(line + "\n")

log("{} event={} remote={} keys={} field={} marker={} tool={}".format(
    datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    event,
    os.environ.get("CLAUDE_CODE_REMOTE", "false"),
    ",".join(sorted(payload.keys())) or "NONE",
    field, which or "none", payload.get("tool_name", "-")))

if which is None:
    sys.exit(0)

legacy = {"decision": "block", "reason": "manifold-block-probe: marker A in prompt"}
current = {"hookSpecificOutput": {
    "hookEventName": event,
    "permissionDecision": "deny",
    "permissionDecisionReason": "manifold-block-probe: marker {} in {}".format(which, field)}}

out = legacy if (event == "UserPromptSubmit" and which == "A") else current

log("   shape={} emitted={}".format("legacy" if out is legacy else "current", json.dumps(out)))
print(json.dumps(out))
sys.exit(0)
