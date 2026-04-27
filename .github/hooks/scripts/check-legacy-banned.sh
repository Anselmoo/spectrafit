#!/usr/bin/env bash
# Hook: check-legacy-banned.sh
# Event: PreToolUse
# Purpose: Block re-introduction of v1 legacy patterns that are being purged in v2.
#
# Hard-banned (deny):
#   - New args_out["key"] dict-access patterns
#   - global_: int parameter (replace with FittingMode StrEnum)
#   - New from_legacy_dict() call sites (bridge only; no new usage)
#
# Soft-warned (ask):
#   - normalize_unified_config_input() — migration adapter, no new call sites
#   - SolverModels(...) direct instantiation — use LmfitSolverRuntime instead
#   - ParameterBuilder direct instantiation in new code
#   - New print() statements in spectrafit/ (use logger or Rich console)

set -euo pipefail

INPUT="$(cat)"
TOOL_NAME="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || true)"

case "$TOOL_NAME" in
  create_file|replace_string_in_file|multi_replace_string_in_file) ;;
  *) echo '{"continue": true}'; exit 0 ;;
esac

FILE_PATH="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('filePath', d.get('tool_input',{}).get('path','')))" 2>/dev/null || true)"
CONTENT="$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); inp=d.get('tool_input',{}); print(inp.get('content', inp.get('newString', '')))" 2>/dev/null || true)"

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

HARD_VIOLATIONS=()
SOFT_VIOLATIONS=()

# Hard-banned: dict-access on args_out
if echo "$CONTENT" | grep -qE 'args_out\[["'"'"']'; then
  HARD_VIOLATIONS+=("args_out[\"key\"] dict access — use FitResult typed properties instead")
fi

# Hard-banned: global_: int pattern
if echo "$CONTENT" | grep -qE 'global_\s*:\s*int\b'; then
  HARD_VIOLATIONS+=("global_: int — replace with FittingMode StrEnum from spectrafit.models.fitting_context")
fi

# Hard-banned: new from_legacy_dict usage (only allowed in bridge/compat files)
if echo "$CONTENT" | grep -qE '\.from_legacy_dict\(' ; then
  case "$FILE_PATH" in
    */report/_compat.py|*/models/results/fit_result.py|*/jupyter/solver.py) ;;
    *) HARD_VIOLATIONS+=("from_legacy_dict() outside of bridge files — construct typed models directly via model_validate()") ;;
  esac
fi

# Soft-warned: legacy adapter
if echo "$CONTENT" | grep -qE 'normalize_unified_config_input\('; then
  SOFT_VIOLATIONS+=("normalize_unified_config_input() — migration adapter; no new call sites; use UnifiedFittingConfig.model_validate() instead")
fi

# Soft-warned: SolverModels direct instantiation
if echo "$CONTENT" | grep -qE 'SolverModels\('; then
  case "$FILE_PATH" in
    */models/solver.py) ;;
    *) SOFT_VIOLATIONS+=("SolverModels(...) — legacy shim; use LmfitSolverRuntime directly for new code") ;;
  esac
fi

# Soft-warned: new print() in spectrafit/ source
if echo "$CONTENT" | grep -qE '^\s*print\(' && [[ "$FILE_PATH" == */spectrafit/*.py ]]; then
  case "$FILE_PATH" in
    */tests/*|*/test_*) ;;
    *) SOFT_VIOLATIONS+=("print() in source — use Rich console or Python logger; bare print() is banned in spectrafit/") ;;
  esac
fi

if [ ${#HARD_VIOLATIONS[@]} -eq 0 ] && [ ${#SOFT_VIOLATIONS[@]} -eq 0 ]; then
  echo '{"continue": true}'
  exit 0
fi

if [ ${#HARD_VIOLATIONS[@]} -gt 0 ]; then
  HARD_REASONS=$(printf " • %s\n" "${HARD_VIOLATIONS[@]}")
  SOFT_REASONS=$(printf " • %s\n" "${SOFT_VIOLATIONS[@]}")
  python3 -c "
import json, sys
hard = sys.argv[1]
soft = sys.argv[2]
file = sys.argv[3]
msg = f'HARD-BANNED legacy patterns in {file}:\n{hard}'
if soft.strip():
    msg += f'\n\nAdditional warnings:\n{soft}'
msg += '\n\nThese patterns are being removed in v2. Do not re-introduce them.'
output = {
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': msg
    }
}
print(json.dumps(output))
" "$HARD_REASONS" "$SOFT_REASONS" "$FILE_PATH"
else
  SOFT_REASONS=$(printf " • %s\n" "${SOFT_VIOLATIONS[@]}")
  python3 -c "
import json, sys
soft = sys.argv[1]
file = sys.argv[2]
output = {
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'ask',
        'permissionDecisionReason': f'Legacy pattern warnings in {file}:\n{soft}\n\nConfirm this is intentional and explain why the v2 alternative cannot be used here.'
    }
}
print(json.dumps(output))
" "$SOFT_REASONS" "$FILE_PATH"
fi
