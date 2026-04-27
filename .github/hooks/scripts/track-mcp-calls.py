#!/usr/bin/env python3
# ruff: noqa: T201,D,PLR2004,N802,N815,ANN,RUF,S603
# Hook: track-mcp-calls.py
# Events: SessionStart, PreToolUse, PostToolUse
# Purpose: MCP call deduplication tracker.
#
# Warns (permissionDecision: "ask") when the same tool is called 3+ times in the
# current session with an equivalent query fingerprint.
#
# Tracked tool families:
#   - fetch_webpage               → fingerprint: sorted normalized URL paths
#   - mcp_github_search_*         → fingerprint: query.lower().strip()
#   - mcp_ai-agent-guid_agent-memory → fingerprint: command + sorted(tags)
#   - mcp_ai-agent-guid_*         → fingerprint: first 80 chars of task/description
#
# State file: .github/hooks/scripts/.mcp_session_state.json (in-repo, gitignored)
# State is scoped to the most-recent session entry. SessionStart appends a new entry.
# Max 50 sessions are retained to prevent unbounded growth.

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import NoReturn
from urllib.parse import urlparse

STATE_FILE = Path(__file__).parent / ".mcp_session_state.json"
MAX_SESSIONS = 50
# Warn starting from the Nth identical call (count already recorded >= threshold)
DEDUP_THRESHOLD = 2

# Tools whose calls are individually fingerprinted and tracked
_TRACKED_EXACT = frozenset(
    {
        "fetch_webpage",
        "mcp_github_search_code",
        "mcp_github_search_repositories",
        "mcp_github_search_issues",
        "mcp_ai-agent-guid_agent-memory",
    }
)
_TRACKED_PREFIX = "mcp_ai-agent-guid_"


# ---------------------------------------------------------------------------
# State file helpers
# ---------------------------------------------------------------------------


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"sessions": []}


def _save_state(state: dict) -> None:
    state["sessions"] = state["sessions"][-MAX_SESSIONS:]
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


def _sha16(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _current_session(state: dict) -> dict | None:
    sessions = state.get("sessions")
    return sessions[-1] if sessions else None


# ---------------------------------------------------------------------------
# Fingerprint computation
# ---------------------------------------------------------------------------


def _fingerprint(tool_name: str, tool_input: dict) -> tuple[str, str]:
    """Return (sha16_fingerprint, human-readable args_summary)."""
    if tool_name == "fetch_webpage":
        urls: list[str] = tool_input.get("urls") or []
        normalized = sorted(urlparse(u).netloc + urlparse(u).path for u in urls)
        key = "|".join(normalized)
        shown = urls[:2]
        summary = ", ".join(shown) + ("…" if len(urls) > 2 else "")
        return _sha16(key), summary

    if tool_name in {
        "mcp_github_search_code",
        "mcp_github_search_repositories",
        "mcp_github_search_issues",
    }:
        query = (tool_input.get("query") or "").lower().strip()
        return _sha16(query), f'query="{query[:80]}"'

    if tool_name == "mcp_ai-agent-guid_agent-memory":
        command = tool_input.get("command") or ""
        tags = sorted(tool_input.get("tags") or [])
        key = command + "|" + "|".join(tags)
        return _sha16(key), f"command={command} tags={tags}"

    if tool_name.startswith(_TRACKED_PREFIX):
        task = (tool_input.get("task") or tool_input.get("description") or "")[:80]
        return _sha16(task.lower()), f'task="{task}"'

    # Generic fallback (should not be reached for tracked tools)
    raw = json.dumps(tool_input, sort_keys=True)
    return _sha16(raw), raw[:80]


def _is_tracked(tool_name: str) -> bool:
    return tool_name in _TRACKED_EXACT or tool_name.startswith(_TRACKED_PREFIX)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _continue() -> NoReturn:
    print(json.dumps({"continue": True}))
    sys.exit(0)


def _ask(tool_name: str, count: int, args_summary: str, last_ts: str) -> NoReturn:
    reason = (
        f"Tool '{tool_name}' has already been called {count} time(s) this session "
        f"with an equivalent query fingerprint.\n"
        f"Prior args: {args_summary}\n"
        f"Last called: {last_ts}\n\n"
        f"Before proceeding, consider:\n"
        f"  • mcp_ai-agent-guid_agent-memory (command=find) — check cached results\n"
        f"  • Are you re-asking a question you already have the answer to?\n"
        f"  • If context7 docs were already fetched, reuse from the context window.\n"
        f"Proceed only if this is genuinely a new query variant."
    )
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------


def handle_session_start(state: dict) -> None:
    state["sessions"].append(
        {
            "session_id": str(time.time()),
            "started_at": _now_iso(),
            "calls": [],
        }
    )
    _save_state(state)
    _continue()


def handle_post_tool_use(state: dict, tool_name: str, tool_input: dict) -> None:
    if not _is_tracked(tool_name):
        _continue()

    fp, summary = _fingerprint(tool_name, tool_input)
    session = _current_session(state)
    if session is None:
        _continue()

    calls: list[dict] = session.setdefault("calls", [])
    for call in calls:
        if call["tool"] == tool_name and call["fingerprint"] == fp:
            call["count"] += 1
            call["timestamp"] = _now_iso()
            break
    else:
        calls.append(
            {
                "tool": tool_name,
                "fingerprint": fp,
                "args_summary": summary,
                "timestamp": _now_iso(),
                "count": 1,
            }
        )

    _save_state(state)
    _continue()


def handle_pre_tool_use(state: dict, tool_name: str, tool_input: dict) -> None:
    if not _is_tracked(tool_name):
        _continue()

    fp, _ = _fingerprint(tool_name, tool_input)
    session = _current_session(state)
    if session is None:
        _continue()

    for call in session.get("calls", []):
        if call["tool"] == tool_name and call["fingerprint"] == fp:
            if call["count"] >= DEDUP_THRESHOLD:
                _ask(
                    tool_name=tool_name,
                    count=call["count"],
                    args_summary=call["args_summary"],
                    last_ts=call["timestamp"],
                )
            break

    _continue()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        _continue()

    event: str = data.get("hookEventName", "")
    state = _load_state()

    if event == "SessionStart":
        handle_session_start(state)
    elif event == "PostToolUse":
        handle_post_tool_use(
            state,
            tool_name=data.get("tool_name", ""),
            tool_input=data.get("tool_input") or {},
        )
    elif event == "PreToolUse":
        handle_pre_tool_use(
            state,
            tool_name=data.get("tool_name", ""),
            tool_input=data.get("tool_input") or {},
        )
    else:
        _continue()


if __name__ == "__main__":
    main()
