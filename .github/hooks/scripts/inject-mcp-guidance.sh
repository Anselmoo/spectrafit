#!/usr/bin/env bash
# Hook: inject-mcp-guidance.sh
# Event: SessionStart
# Purpose: Inject MCP tool efficiency rules so agents always use the right tool
#          for the right job without needing explicit instruction each session.

set -euo pipefail

python3 -c "
import json

SYSTEM_MESSAGE = '''
## MCP Tool Efficiency Contract (auto-injected)

### Tool selection hierarchy
1. **Read/explore** — use grep_search, file_search, read_file, semantic_search
   BEFORE running shell commands. Custom tools are faster and don't clutter context.
2. **Symbolic navigation** — use mcp_serena_find_symbol / mcp_serena_get_symbols_overview
   for targeted symbol reads instead of reading entire files.
3. **Library docs** — use mcp_context7_resolve-library-id + mcp_context7_query-docs
   for ANY library/framework question (Pydantic, lmfit, typer, pytest, etc.).
   Do not rely on training data for API specifics.
4. **Memory** — check mcp_ai-agent-guid_agent-memory (find/list) at session start
   for prior decisions and patterns before re-researching.
5. **GitHub** — use mcp_github_* tools for PR review comments, issue reads, and
   file contents from remote refs. Never guess GitHub URLs.
6. **Parallel reads** — batch independent file reads into one parallel tool call.
   Never call read_file sequentially when reads are independent.
7. **Edits** — use multi_replace_string_in_file for multiple independent changes
   to the same or different files. Never call replace_string_in_file sequentially.

### Context7 invocation pattern
- Step 1: mcp_context7_resolve-library-id — get the library ID
- Step 2: mcp_context7_query-docs — query with the specific question
- Use for: Pydantic v2, lmfit, typer, scipy, numpy, pandas, pytest, ruff, hatchling

### Serena invocation pattern
- Step 0: mcp_serena_activate_project() — ALWAYS first, before any other Serena call
- mcp_serena_get_symbols_overview — module-level overview before reading bodies
- mcp_serena_find_symbol — find a specific class/function (include_body=True when editing)
- mcp_serena_find_referencing_symbols — find all usages before renaming/deleting
- mcp_serena_replace_symbol_body — replace full symbol body (preferred over replace_string_in_file for full symbols)

### GitHub search pattern
- mcp_github_search_code — find patterns across repos (check upstream before re-implementing)
- mcp_github_search_issues — find bug reports and discussions
- mcp_github_search_repositories — discover related repos / vendors
- mcp_github_get_file_contents — read file at a remote ref/branch without cloning

### Zen-of-Languages pattern
- mcp_zen-of-langua_analyze_batch — batch scan a directory for idiomatic violations
- mcp_zen-of-langua_check_architectural_patterns — check pydantic_v2, no_dict_contracts, etc.
- mcp_zen-of-langua_analyze_repository — full repo health score (run before/after sprints)
- mcp_zen-of-langua_generate_agent_tasks — turn violations into actionable tasks
- mcp_zen-of-langua_generate_report — export findings as markdown

### fetch_webpage pattern
- Use for: PEP text, external changelogs, arxiv references, release pages
- Do NOT use for GitHub issues/code — use mcp_github_search_* instead

### Agent-memory invocation pattern
- mcp_ai-agent-guid_agent-memory command=find at start of any refactoring session
- mcp_ai-agent-guid_agent-memory command=write after discovering key decisions
- mcp_ai-agent-guid_agent-memory command=enrich to attach context7 library docs to an artifact
- Tags to use: pydantic, architecture, spectrafit, legacy, testing, mcp

### Anti-patterns (never do these)
- Skipping mcp_serena_activate_project before other Serena calls
- Running grep in terminal when grep_search is available
- Reading a full file when only one symbol body is needed
- Calling context7 with a vague query — be specific
- Making sequential read_file calls for independent files
- Skipping agent-memory lookup before starting investigation work
- Using fetch_webpage for GitHub issues (use mcp_github_search_issues instead)
- Writing new utility code without first checking mcp_github_search_code on upstream vendors

### MCP dedup tracker
Active this session: you will be prompted (ask) on the 3rd call with the same query fingerprint.
Use mcp_ai-agent-guid_agent-memory (command=find) before re-researching to avoid duplicate calls.
'''

print(json.dumps({'systemMessage': SYSTEM_MESSAGE.strip(), 'continue': True}))
"
