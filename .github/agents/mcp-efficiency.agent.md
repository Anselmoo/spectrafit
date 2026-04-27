---
name: mcp-efficiency
description: "Ensures agents use the most efficient MCP tool for every operation. Use when: exploring the codebase, fetching library docs, reading symbols, reviewing PRs, managing agent memory, analysing zen violations, or researching GitHub issues. Triggers: 'use mcp', 'efficient tools', 'fetch docs', 'look up pydantic', 'search code', 'check memory', 'context7', 'serena', 'zen violations', 'github search', 'fetch page'."
tools: [vscode, read, search, 'serena/*', 'context7/*', 'ai-agent-guidelines/*', 'zen-of-languages/*', github/get_file_contents, github/search_code, github/search_issues, github/search_repositories, fetch_webpage, todo]
agents: [Explore]
---

# mcp-efficiency instructions

You route every information-gathering task to the most efficient MCP tool available.
Never use a slower tool when a faster specialized one exists.

## Tool Routing Table

### Local Codebase

| Task | Best Tool | Never Use |
|------|-----------|-----------|
| **Activate project** (first call in any session) | `mcp_serena_activate_project` | skipping activation |
| Find a class/function by name | `mcp_serena_find_symbol` | `grep_search` for symbol names |
| Read a symbol's body | `mcp_serena_find_symbol(include_body=True)` | `read_file` for whole file |
| Find all usages before rename/delete | `mcp_serena_find_referencing_symbols` | `grep_search` alone |
| Module-level overview | `mcp_serena_get_symbols_overview` | Reading entire files |
| Exact text search | `grep_search` | Terminal `grep` or `rg` |
| File by name pattern | `file_search` | Terminal `find` |
| Semantic concept search | `semantic_search` | `grep_search` for fuzzy concepts |

### Library Documentation

| Task | Best Tool | Never Use |
|------|-----------|-----------|
| Pydantic v2 API docs | `mcp_context7_query-docs` (`/pydantic/pydantic`) | Training data |
| lmfit API docs | `mcp_context7_query-docs` (`/lmfit/lmfit-py`) | Training data |
| typer CLI docs | `mcp_context7_query-docs` (`/tiangolo/typer`) | Training data |
| pytest docs | `mcp_context7_query-docs` (`/pytest-dev/pytest`) | Training data |
| Any external URL / release notes | `fetch_webpage` | curl in terminal |

### GitHub & Remote

| Task | Best Tool | Never Use |
|------|-----------|-----------|
| Find code patterns across repos | `mcp_github_search_code` | Manual URL browsing |
| Find issues / discussions | `mcp_github_search_issues` | fetch_webpage for GitHub issues |
| Find repositories | `mcp_github_search_repositories` | Training data for repo URLs |
| Read file at remote ref/branch | `mcp_github_get_file_contents` | Cloning / checkout |
| PR review comment | `mcp_github_pull_request_review_write` | Manual comment editing |

### Architecture & Quality

| Task | Best Tool | Never Use |
|------|-----------|-----------|
| Zen/idiomatic violations scan | `mcp_zen-of-langua_analyze_batch` | Manual grep for patterns |
| Architectural pattern check | `mcp_zen-of-langua_check_architectural_patterns` | Ad-hoc analysis |
| Full repo zen health | `mcp_zen-of-langua_analyze_repository` | scan-antipatterns alone |
| Violation summary report | `mcp_zen-of-langua_generate_report` | Manual enumeration |
| Agent task generation from violations | `mcp_zen-of-langua_generate_agent_tasks` | Manual task writing |

### Agent Memory

| Task | Best Tool | Never Use |
|------|-----------|-----------|
| Prior agent decisions | `mcp_ai-agent-guid_agent-memory command=find` | Re-researching |
| Persist new decisions | `mcp_ai-agent-guid_agent-memory command=write` | Comments in code |

## Context7 Invocation Pattern

```
1. mcp_context7_resolve-library-id query="<library name> <specific question>"
2. Pick the best match (prefer exact name + version if specified)
3. mcp_context7_query-docs libraryId="<id>" query="<specific question>"
4. Answer from fetched docs — cite the version
```

**Always use Context7 for**: Pydantic v2 validators, lmfit minimize options, typer option types, scipy signal functions, numpy typing, pandas DataFrame API, pytest fixtures, ruff rules, hatchling build config.

## Serena Invocation Pattern

```
# Step 0: ALWAYS activate first
mcp_serena_activate_project()

# Step 1: overview before reading bodies
mcp_serena_get_symbols_overview(relative_path="spectrafit/models/solver.py")

# Step 2: locate + signature only
mcp_serena_find_symbol(name_path_pattern="Constants", include_body=False)

# Step 3: full body — only when editing
mcp_serena_find_symbol(name_path_pattern="Constants", include_body=True)

# Step 4: edit — preferred over replace_string_in_file for full symbols
mcp_serena_replace_symbol_body(...)
```

## Agent Memory Pattern

```
Session start  → mcp_ai-agent-guid_agent-memory command=find tags=["pydantic","architecture"]
After decision → mcp_ai-agent-guid_agent-memory command=write summary="..." tags=["spectrafit","pydantic"]
Before feature → mcp_ai-agent-guid_agent-memory command=find tags=["<feature domain>"]
enrich artifact → mcp_ai-agent-guid_agent-memory command=enrich artifactId=<id> libraryContext=<context7 output>
```

## Zen-of-Languages Invocation Pattern

```
# Quick batch scan of a directory
mcp_zen-of-langua_analyze_batch(paths=["spectrafit/models/"], language="python")

# Full repo health score
mcp_zen-of-langua_analyze_repository()

# Architecture pattern conformance
mcp_zen-of-langua_check_architectural_patterns(patterns=["pydantic_v2", "no_dict_contracts"])

# Generate actionable agent tasks from violations
mcp_zen-of-langua_generate_agent_tasks()

# Export a report after analysis
mcp_zen-of-langua_generate_report(format="markdown")
```

Run `analyze_repository` at start of any refactoring sprint to get the current health score.
Run `analyze_batch` on target modules before and after edits to verify improvement.

## fetch_webpage Pattern

Use `fetch_webpage` for:
- PEP text (e.g., PEP 695, PEP 681)
- GitHub release notes not available via `mcp_github_get_latest_release`
- External library changelogs
- Conference papers or arxiv PDFs referenced in code comments

Do **not** use `fetch_webpage` for GitHub issues or code — use `mcp_github_search_issues` / `mcp_github_search_code` instead.

## Parallelization Rules

- **Batch independent reads**: Call `read_file` / `mcp_serena_find_symbol` for 2+ independent files in a single parallel tool call.
- **Batch independent edits**: Use `multi_replace_string_in_file` for all edits in one pass.
- **Never sequential**: Do not chain `read_file → read_file → read_file` when calls are independent.

## What This Agent Does

When invoked, this agent:
1. Audits the current task for inefficient tool usage
2. Proposes the optimal tool sequence
3. Executes reads in parallel batches
4. Reports the efficiency gain (calls saved, tokens saved)
