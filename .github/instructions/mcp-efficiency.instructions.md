---
applyTo: "spectrafit/**/*.py,tests/**/*.py"
---

# SpectraFit MCP Efficiency Rules

These rules apply when any agent works with `spectrafit/` or `tests/`. They ensure
the fastest, most context-efficient tool is always used.

## Mandatory Tool Selection

### Serena — Activate First

**Always call `mcp_serena_activate_project()` before any other Serena tool.**
Without activation, symbol lookups return stale or empty results.

Always prefer in this order:
1. `mcp_serena_get_symbols_overview(relative_path=<file>)` — module overview
2. `mcp_serena_find_symbol(name_path_pattern=<symbol>, include_body=False)` — locate symbol
3. `mcp_serena_find_symbol(name_path_pattern=<symbol>, include_body=True)` — read only when editing
4. `read_file` with a tight line range — only if serena doesn't cover the case

**Never** read an entire file when only one symbol is needed.

### Searching Code

| Need | Tool |
|------|------|
| Find symbol by name | `mcp_serena_find_symbol` |
| Find all usages of a symbol | `mcp_serena_find_referencing_symbols` |
| Find text pattern | `grep_search` |
| Find file by name glob | `file_search` |
| Find by semantic meaning | `semantic_search` |

**Never** use terminal `grep`, `find`, or `rg` when the custom tools work.

### GitHub Search

| Need | Tool |
|------|------|
| Find code patterns across repos | `mcp_github_search_code` |
| Find issues / bug reports | `mcp_github_search_issues` |
| Discover related repositories | `mcp_github_search_repositories` |
| Read file at remote ref | `mcp_github_get_file_contents` |

Use `mcp_github_search_code` before writing new utilities — the pattern may already exist
in the upstream `lmfit-py` or `docker-stacks` vendors.

### Zen-of-Languages Analysis

| Need | Tool |
|------|------|
| Batch scan for idiom violations | `mcp_zen-of-langua_analyze_batch` |
| Full repo health score | `mcp_zen-of-langua_analyze_repository` |
| Architecture pattern conformance | `mcp_zen-of-langua_check_architectural_patterns` |
| Generate actionable tasks | `mcp_zen-of-langua_generate_agent_tasks` |
| Export report | `mcp_zen-of-langua_generate_report` |

Run `analyze_batch` on any module **before and after** a refactoring to measure improvement.

### External Web / Docs

Use `fetch_webpage` for: PEP text, external changelogs, arxiv/paper references in code.
Do **not** use it for GitHub issues or code — use `mcp_github_search_*` instead.

### Library Documentation

**Always** use Context7 for library-specific questions:
```
mcp_context7_resolve-library-id → mcp_context7_query-docs
```

Libraries that **must** be looked up via Context7 (not training data):
- `pydantic` (v2 validators, model_config, computed_field, ConfigDict)
- `lmfit` (minimize, Parameters, Model, CompositeModel)
- `typer` (Option, Argument, callback, result_callback)
- `pytest` (fixtures, parametrize, mark, approx)
- `scipy` (curve_fit, minimize, signal functions)
- `numpy` (typing, NDArray, array creation)
- `hatchling` (build config, src layout, entry points)

### Editing Code

- Multiple independent edits → `multi_replace_string_in_file` (one call, all changes)
- Full symbol replacement → `mcp_serena_replace_symbol_body` (preferred)
- Insert after/before symbol → `mcp_serena_insert_after_symbol` / `mcp_serena_insert_before_symbol`

### Agent Memory

```
Session start   → mcp_ai-agent-guid_agent-memory command=find (check prior decisions)
After discovery → mcp_ai-agent-guid_agent-memory command=write (persist new decisions)
Enrich artifact → mcp_ai-agent-guid_agent-memory command=enrich artifactId=<id> libraryContext=<context7 docs>
```

Tags to always include: `pydantic`, `architecture`, `spectrafit`.

## Parallelization Contract

Independent reads **must** be batched:
```python
# CORRECT: parallel
read_file(file_A), read_file(file_B), mcp_serena_find_symbol(symbol_C)

# WRONG: sequential when independent
read_file(file_A)
read_file(file_B)
mcp_serena_find_symbol(symbol_C)
```

Independent edits **must** be batched via `multi_replace_string_in_file`.

## Context Window Discipline

- Read only what is needed for the current step
- Use `mcp_serena_get_symbols_overview` before deciding which symbols to read fully
- Use tight line ranges in `read_file` (never read 500 lines when 50 suffice)
- Avoid re-reading files that were already read in the same session
