/**
 * pydantic-type-audit — SpectraFit Copilot Extension
 *
 * Scans Python source files for vague type annotations that violate the
 * "Pydantic-first, ty-hard-fail" policy of SpectraFit v2. Reports findings
 * grouped by severity and suggests concrete typed replacements.
 *
 * Trigger phrases:
 *   "audit types", "find type gaps", "type hardening", "pydantic audit"
 */

import { execFile } from "node:child_process";
import { approveAll } from "@github/copilot-sdk";
import { joinSession } from "@github/copilot-sdk/extension";

// ────────────────────────────────────────────────────────────────────────────
// Pattern catalogue
// ────────────────────────────────────────────────────────────────────────────

const PATTERNS = [
    // ── CRITICAL: garbage collector dicts ────────────────────────────────────
    {
        id: "model_dump_garbage",
        severity: "critical",
        label: "model_dump() → immediate dict access (Pydantic model dumped to garbage dict)",
        regex: "\\.model_dump\\(\\)",
        suggestion:
            "Do NOT call .model_dump() and then access by string key. " +
            "Keep the Pydantic model and access typed attributes directly. " +
            "E.g. config.minimizer.nan_policy, not args_solver['minimizer']['nan_policy'].",
    },
    {
        id: "self_args_garbage",
        severity: "critical",
        label: "self.args = {} (catch-all mutable dict accumulator)",
        regex: "self\\.args\\s*=\\s*\\{\\}",
        suggestion:
            "Replace self.args with a typed Pydantic model (FitResult, SolverResults). " +
            "Never use a plain dict as a class-level state accumulator.",
    },
    {
        id: "args_out_garbage",
        severity: "critical",
        label: "args_out: dict[str, object] (untyped result dict passed to export)",
        regex: "args_out\\s*:\\s*dict\\[str,\\s*object\\]",
        suggestion:
            "Replace args_out with PostProcessingResult or a typed FitResult. " +
            "The export boundary must be a typed model, not a plain dict.",
    },
    // ── HIGH ─────────────────────────────────────────────────────────────────
    {
        id: "magic_int_range",
        severity: "high",
        label: "global_: int with magic 0/1/2 values (use FittingMode enum)",
        regex: "global_.*int.*ge=0.*le=2|ge=0.*le=2.*global_|global_.*int.*Field",
        suggestion:
            "Replace int field with FittingMode enum. " +
            "0/1/2 without an enum makes intent opaque. " +
            "Minimum: Literal[0, 1, 2]; preferred: FittingMode.",
    },
    {
        id: "bool_int_smell",
        severity: "high",
        label: "bool | int anti-pattern (HIGH: opaque mode flags must be enums)",
        regex: "bool\\s*\\|\\s*int|int\\s*\\|\\s*bool",
        suggestion:
            "Use FittingMode enum or explicit int. Never mix bool and int — " +
            "it is semantically opaque. bool|int for global_fitting hides " +
            "whether the value is a flag (bool) or a mode selector (int).",
    },
    {
        id: "vague_object",
        severity: "high",
        label: "dict[str, object] / list[object]",
        regex: "dict\\[str,\\s*object\\]|list\\[object\\]|dict\\[str,\\s*list\\[object\\]\\]",
        suggestion:
            "Replace with a TypedDict, a Pydantic BaseModel, or a concrete scalar alias " +
            "(e.g. dict[str, list[float]], NumericSplitDict, ConfidenceIntervalResult).",
    },
    {
        id: "any_leak",
        severity: "high",
        label: "dict[str, Any] / Any annotation",
        regex: "dict\\[str,\\s*Any\\]|:\\s*Any\\b|->\\s*Any\\b|\\[Any\\]",
        suggestion:
            "Use explicit types. Remove 'from typing import Any' in production modules. " +
            "Use TYPE_CHECKING guard for heavy imports.",
    },
    {
        id: "bool_int_smell",
        severity: "medium",
        label: "bool | int anti-pattern",
        regex: "bool\\s*\\|\\s*int|int\\s*\\|\\s*bool",
        suggestion:
            "Use 'int' alone (0/1/2 convention) or a proper enum (FittingMode). " +
            "Never mix bool and int in the same union — it hides semantic intent.",
    },
    {
        id: "type_ignore_assignment",
        severity: "medium",
        label: "# type: ignore[assignment]",
        regex: "#\\s*type:\\s*ignore\\[assignment\\]",
        suggestion:
            "Introduce a concrete TypedDict or BaseModel so the assignment type is " +
            "correct without suppression. DataSplitDict → NumericSplitDict eliminates " +
            "all postprocessing ignores.",
    },
    {
        id: "legacy_args_get",
        severity: "high",
        label: "Legacy dict access: args.get() / args[key]",
        regex: "\\.args\\.get\\(|\\.args\\[",
        suggestion:
            "Replace with typed model attribute access. Use DataConfig, " +
            "UnifiedFittingConfig, or a typed parameter passed to __init__.",
    },
    {
        id: "permissive_split_dict",
        severity: "high",
        label: "DataSplitDict (float|str|None data) on numeric fields",
        regex: "DataSplitDict",
        suggestion:
            "For purely numeric outputs (correlation, regression, descriptive stats) " +
            "use NumericSplitDict with data: list[list[float]] instead.",
    },
    {
        id: "vague_union_object",
        severity: "medium",
        label: "Union containing bare 'object'",
        regex: "tuple\\[object",
        suggestion:
            "Express the actual union concretely, e.g. " +
            "ConfidenceIntervalResult | ConfidenceIntervalWithTrace.",
    },
    {
        id: "vague_report_buffer",
        severity: "high",
        label: "FitReportBuffer = dict[str, dict[str, object]]",
        regex: "FitReportBuffer",
        suggestion:
            "Replace with a TypedDict that names the known sections " +
            "(statistics, variables, errorbars, correlations).",
    },
];

// ────────────────────────────────────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────────────────────────────────────

function runRg(pattern, paths) {
    return new Promise((resolve) => {
        const args = ["-n", "--no-heading", "-e", pattern, ...paths];
        execFile("rg", args, { maxBuffer: 4 * 1024 * 1024 }, (err, stdout) => {
            resolve(stdout || "");
        });
    });
}

function parseRgOutput(raw) {
    return raw
        .split("\n")
        .filter(Boolean)
        .map((line) => {
            const m = line.match(/^([^:]+):(\d+):(.*)$/);
            return m ? { file: m[1], line: m[2], text: m[3].trim() } : null;
        })
        .filter(Boolean);
}

function formatReport(results) {
    if (results.length === 0) return "✅ No type gaps found.";

    const byFile = {};
    for (const r of results) {
        if (!byFile[r.file]) byFile[r.file] = [];
        byFile[r.file].push(r);
    }

    const severityOrder = { high: 0, medium: 1, low: 2 };
    const sorted = Object.entries(byFile).sort(([a], [b]) => {
        const maxSev = (entries) =>
            Math.min(
                ...entries.map((e) => severityOrder[e.severity] ?? 99)
            );
        return maxSev(byFile[a]) - maxSev(byFile[b]);
    });

    const lines = [`\n${"═".repeat(70)}`, "  SpectraFit Pydantic Type-Hardening Audit", `${"═".repeat(70)}`];
    let high = 0, medium = 0;

    for (const [file, entries] of sorted) {
        lines.push(`\n📄 ${file}`);
        for (const e of entries) {
            const icon = e.severity === "high" ? "🔴" : e.severity === "medium" ? "🟡" : "🟢";
            lines.push(`  ${icon} [${e.severity.toUpperCase()}] L${e.line} — ${e.label}`);
            lines.push(`     Found: ${e.text.slice(0, 90)}`);
            lines.push(`     Fix:   ${e.suggestion.slice(0, 100)}`);
            if (e.severity === "high") high++;
            if (e.severity === "medium") medium++;
        }
    }

    lines.push(`\n${"─".repeat(70)}`);
    lines.push(`Summary: 🔴 ${high} high  🟡 ${medium} medium`);
    lines.push(`${"─".repeat(70)}`);
    return lines.join("\n");
}

// ────────────────────────────────────────────────────────────────────────────
// Session
// ────────────────────────────────────────────────────────────────────────────

const DEFAULT_SCAN_PATHS = [
    "spectrafit/cli",
    "spectrafit/core",
    "spectrafit/jupyter",
    "spectrafit/models",
    "spectrafit/plotting.py",
    "spectrafit/report",
];

const session = await joinSession({
    onPermissionRequest: approveAll,
    tools: [
        {
            name: "audit_type_gaps",
            description:
                "Scan SpectraFit Python sources for vague type annotations " +
                "(dict[str,object], Any, bool|int, DataSplitDict, legacy args.get) " +
                "and report them by severity with concrete typed replacements. " +
                "Use when asked to: audit types, find type gaps, type hardening, pydantic audit.",
            parameters: {
                type: "object",
                properties: {
                    paths: {
                        type: "array",
                        items: { type: "string" },
                        description:
                            "Paths to scan (relative to project root). " +
                            "Defaults to spectrafit/cli, spectrafit/core, spectrafit/jupyter, " +
                            "spectrafit/models, spectrafit/plotting.py, spectrafit/report.",
                    },
                    severity_filter: {
                        type: "string",
                        enum: ["all", "high", "medium"],
                        description: "Only show gaps at or above this severity. Default: all.",
                    },
                    pattern_ids: {
                        type: "array",
                        items: { type: "string" },
                        description:
                            "Optional subset of pattern IDs to run. " +
                            "Available: vague_object, any_leak, bool_int_smell, " +
                            "type_ignore_assignment, legacy_args_get, permissive_split_dict, " +
                            "vague_union_object, vague_report_buffer.",
                    },
                },
                required: [],
            },
            handler: async (args) => {
                const paths = args.paths?.length ? args.paths : DEFAULT_SCAN_PATHS;
                const severityFilter = args.severity_filter ?? "all";
                const activePatterns = args.pattern_ids?.length
                    ? PATTERNS.filter((p) => args.pattern_ids.includes(p.id))
                    : PATTERNS;

                const severityOrder = { high: 0, medium: 1, low: 2 };
                const maxSeverity = severityOrder[severityFilter] ?? 99;

                const filtered = activePatterns.filter(
                    (p) => (severityOrder[p.severity] ?? 99) <= maxSeverity
                );

                const allResults = [];
                for (const pattern of filtered) {
                    const raw = await runRg(pattern.regex, paths);
                    const hits = parseRgOutput(raw);
                    for (const hit of hits) {
                        allResults.push({ ...hit, ...pattern });
                    }
                }

                return formatReport(allResults);
            },
        },

        {
            name: "list_type_gap_patterns",
            description:
                "List all registered type-gap patterns with their IDs, severity, and suggested fixes. " +
                "Call this before audit_type_gaps to understand what patterns will be checked.",
            parameters: { type: "object", properties: {}, required: [] },
            handler: async () => {
                const lines = ["\n📋 Registered type-gap patterns:\n"];
                for (const p of PATTERNS) {
                    const icon = p.severity === "high" ? "🔴" : p.severity === "medium" ? "🟡" : "🟢";
                    lines.push(`${icon} [${p.id}] ${p.label}`);
                    lines.push(`   ${p.suggestion}`);
                    lines.push("");
                }
                return lines.join("\n");
            },
        },
    ],
});
