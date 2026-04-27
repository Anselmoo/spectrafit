#!/usr/bin/env bash
# Hook: check-test-paired.sh
# Event: PreToolUse
# Purpose: Warn when editing a spectrafit/ source module without a paired test file.
#
# Policy:
#   - Any edit to spectrafit/**/*.py (except __init__.py, conftest.py, py.typed)
#     should have a corresponding tests/unit/test_*.py or tests/integration/test_*.py.
#   - If the paired test file does not exist, prompt the agent to create it.

set -euo pipefail

INPUT="$(cat)"
TOOL_NAME="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || true)"

case "$TOOL_NAME" in
  create_file|replace_string_in_file|multi_replace_string_in_file) ;;
  *) echo '{"continue": true}'; exit 0 ;;
esac

FILE_PATH="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('filePath', d.get('tool_input',{}).get('path','')))" 2>/dev/null || true)"

# Only watch spectrafit/ source files
case "$FILE_PATH" in
  */spectrafit/*.py|*/spectrafit/**/*.py) ;;
  *) echo '{"continue": true}'; exit 0 ;;
esac

# Skip infrastructure files
BASENAME="$(basename "$FILE_PATH")"
case "$BASENAME" in
  __init__.py|conftest.py|py.typed) echo '{"continue": true}'; exit 0 ;;
esac

# Skip test files themselves
case "$FILE_PATH" in
  */test_*.py|*/tests/*) echo '{"continue": true}'; exit 0 ;;
esac

# Derive expected test file name
MODULE_NAME="${BASENAME%.py}"
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
UNIT_TEST="$REPO_ROOT/tests/unit/test_${MODULE_NAME}.py"
INTEG_TEST="$REPO_ROOT/tests/integration/test_${MODULE_NAME}.py"

if [ -f "$UNIT_TEST" ] || [ -f "$INTEG_TEST" ]; then
  echo '{"continue": true}'
  exit 0
fi

python3 -c "
import json, sys
module = sys.argv[1]
unit_test = sys.argv[2]
output = {
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'ask',
        'permissionDecisionReason': (
            f'No paired test file found for {module}.\n'
            f'Expected: tests/unit/test_{module}.py\n\n'
            f'Test-driven policy: create or update the test file alongside this source change. '
            f'Proceed anyway only if this is a non-testable scaffold file.'
        )
    }
}
print(json.dumps(output))
" "$MODULE_NAME" "$UNIT_TEST"
