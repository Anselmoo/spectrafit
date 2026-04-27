#!/usr/bin/env bash
# Hook: check-pydantic.sh
# Event: PreToolUse
# Purpose: Block banned patterns before any Python file is written or edited.
#
# Banned patterns (Pydantic enforcement):
#   - @dataclass without a pydantic migration comment
#   - ClassVar[float|int|str] used in place of Pydantic fields
#   - dict[str, Any] / dict[str, object] as function return types or model fields
#   - extra="allow" without the required migration comment
#   - from typing import Optional (use X | None syntax instead)

set -euo pipefail

INPUT="$(cat)"
TOOL_NAME="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || true)"

# Only scan file-writing tools
case "$TOOL_NAME" in
  create_file|replace_string_in_file|multi_replace_string_in_file) ;;
  *) echo '{"continue": true}'; exit 0 ;;
esac

# Extract file path and content
FILE_PATH="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('filePath', d.get('tool_input',{}).get('path','')))" 2>/dev/null || true)"
CONTENT="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); inp=d.get('tool_input',{}); print(inp.get('content', inp.get('newString', inp.get('replacements','[]'))))" 2>/dev/null || true)"

# Only check Python files
case "$FILE_PATH" in
  *.py) ;;
  *) echo '{"continue": true}'; exit 0 ;;
esac

# Exclude hook scripts, tooling, and .github/ (repo root is also named spectrafit)
case "$FILE_PATH" in
  */.github/*|*/scripts/*.py|*/prototype/*)
    echo '{"continue": true}'; exit 0 ;;
esac

# Only check spectrafit/ package sub-directories (not the repo root)
if ! echo "$FILE_PATH" | grep -qE '/spectrafit/(adapters|api|app|cli|core|generators|jupyter|models|notebook|plugins|report|reporting|utilities|workflow)/'; then
  echo '{"continue": true}'; exit 0
fi

VIOLATIONS=()

# Check for raw dataclass usage (without pydantic BaseModel as base)
if echo "$CONTENT" | grep -qE '@dataclass(\(frozen=True\))?' && ! echo "$CONTENT" | grep -q 'BaseModel'; then
  VIOLATIONS+=("@dataclass without BaseModel inheritance — use Pydantic BaseModel with ConfigDict(frozen=True) instead")
fi

# Check for ClassVar in non-protocol/typing contexts used as plain data
if echo "$CONTENT" | grep -qE 'ClassVar\[(float|int|str|bool|list|dict)\]'; then
  VIOLATIONS+=("ClassVar[<scalar>] detected — use plain Pydantic field with default= instead (ClassVar is ignored by Pydantic v2)")
fi

# Check for dict[str, Any] or dict[str, object] as a return type or model field
if echo "$CONTENT" | grep -qE '-> dict\[str, (Any|object)\]|: dict\[str, (Any|object)\]'; then
  VIOLATIONS+=("dict[str, Any/object] as contract type — define a Pydantic model with extra=\"forbid\" instead")
fi

# Check for new extra="allow" without migration comment
if echo "$CONTENT" | grep -qE 'extra\s*=\s*"allow"' && ! echo "$CONTENT" | grep -q 'migration target\|result container\|parse-time adapter'; then
  VIOLATIONS+=("extra=\"allow\" without migration comment — add: # intentional: <reason>, v2.x migration target")
fi

# Check for Optional import (forbidden in new code)
if echo "$CONTENT" | grep -qE 'from typing import.*Optional|Optional\['; then
  VIOLATIONS+=("Optional[T] detected — use T | None syntax (Python 3.12+)")
fi

# Check for TypeAlias (use PEP 695 type keyword instead)
if echo "$CONTENT" | grep -qE 'TypeAlias'; then
  VIOLATIONS+=("TypeAlias detected — use PEP 695 'type X = ...' keyword instead")
fi

if [ ${#VIOLATIONS[@]} -eq 0 ]; then
  echo '{"continue": true}'
  exit 0
fi

REASONS=$(printf " • %s\n" "${VIOLATIONS[@]}")
python3 -c "
import json, sys
reasons = sys.argv[1]
output = {
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'ask',
        'permissionDecisionReason': f'Pydantic enforcement violations detected in {sys.argv[2]}:\n{reasons}\n\nFix before proceeding or confirm this is an intentional exception.'
    }
}
print(json.dumps(output))
" "$REASONS" "$FILE_PATH"
