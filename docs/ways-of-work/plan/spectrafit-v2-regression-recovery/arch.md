# Epic Architecture Specification: SpectraFit v2 Regression Recovery

## 1. Epic Architecture Overview

This epic restores contract integrity across SpectraFit’s three primary user surfaces: CLI, Jupyter, and result export.

The technical approach is contract-first and test-backed:

- Canonicalize notebook initialization on `UnifiedFittingConfig` + `SpectraFitNotebook.from_config()`.
- Define banner behavior explicitly at Typer entry points for bare + interactive flows.
- Make `_summary.json` use a single authoritative export schema (`FitResult`) and keep report-generation as a transform layer, not a competing source of truth.
- Add integration tests that validate generated notebook execution paths, CLI startup behavior, and summary export/readback contracts.

This architecture minimizes churn in frozen modules by adding adapters at stable boundaries (`cli/commands`, `jupyter/templates`, model mappers).

## 2. System Architecture Diagram

```mermaid
flowchart TD
  %% ---------- User Layer ----------
  subgraph UL["User Layer"]
    U1["CLI User (Terminal)"]
    U2["Notebook User (Jupyter)"]
    U3["Python API User"]
    U4["CI Pipeline (pytest/ruff/ty)"]
  end

  %% ---------- Application Layer ----------
  subgraph AL["Application Layer"]
    A1["Typer App (`spectrafit.cli.main`)"]
    A2["Rich Banner (`render_startup_panel`)"]
    A3["Notebook Surface (`SpectraFitNotebook`)"]
    A4["Config Boundary (`UnifiedFittingConfig`)"]
    A5["Scaffolding (`spectrafit init`)"]
  end

  %% ---------- Service Layer ----------
  subgraph SL["Service Layer"]
    S1["FittingPipeline"]
    S2["SolverModels + lmfit"]
    S3["Contract Mappers\n- from_config()\n- from_legacy_dict()"]
    S4["Export Orchestrators\n- SaveResult (legacy path)\n- FitResult writer (target)"]
    S5["Report Generator (`spectrafit report`)"]
  end

  %% ---------- Data Layer ----------
  subgraph DL["Data Layer"]
    D1["Input Config (TOML/JSON)"]
    D2["Spectra Data (CSV/DataFrame)"]
    D3["`*_summary.json` (authoritative FitResult)"]
    D4["Derived Reports (text/markdown/json)"]
    D5["Regression Tests (unit + integration fixtures)"]
  end

  %% ---------- Infrastructure Layer ----------
  subgraph IL["Infrastructure Layer"]
    I1["Python Runtime (3.10–3.13)"]
    I2["Dockerized CI/Dev Environments"]
    I3["uv + poe task runner"]
    I4["GitHub Actions / local CI gate (`uv run poe ci`)"]
  end

  %% Sync request paths
  U1 --> A1
  U2 --> A3
  U3 --> A4
  U4 --> I4

  A1 --> A2
  A1 --> A4
  A3 --> A4
  A5 --> A3
  A5 --> D1

  A4 --> S1
  S1 --> S2
  S1 --> S3
  S3 --> S4
  S4 --> D3
  D3 --> S5
  S5 --> D4

  D1 --> A4
  D2 --> S1
  D5 --> I4
  I4 --> D5

  %% Async/validation feedback paths
  D5 -. contract regression feedback .-> S3
  D5 -. UX regression feedback .-> A1
  D5 -. generated notebook validation .-> A5

  %% Styling
  classDef user fill:#E3F2FD,stroke:#1565C0,color:#0D47A1;
  classDef app fill:#E8F5E9,stroke:#2E7D32,color:#1B5E20;
  classDef svc fill:#FFF8E1,stroke:#F9A825,color:#E65100;
  classDef data fill:#F3E5F5,stroke:#6A1B9A,color:#4A148C;
  classDef infra fill:#ECEFF1,stroke:#455A64,color:#263238;

  class U1,U2,U3,U4 user;
  class A1,A2,A3,A4,A5 app;
  class S1,S2,S3,S4,S5 svc;
  class D1,D2,D3,D4,D5 data;
  class I1,I2,I3,I4 infra;
```

## 3. High-Level Features & Technical Enablers

### High-Level Features

- Canonical notebook initialization flow for generated and documented notebook usage.
- Deterministic CLI startup/banner behavior for selected invocation modes.
- Single-source summary export contract and explicit report derivation path.
- Regression-proof verification of generated assets and runtime contracts.
- Accurate architecture/status documentation aligned to tested behavior.

### Technical Enablers

- Boundary adapters between legacy dict outputs and typed `FitResult`.
- Targeted integration tests for `init --jupyter` notebook cells and CLI invocation surface.
- Schema validation assertions for `_summary.json` at export and read paths.
- Incremental migration wrappers that avoid broad refactors in frozen modules.
- CI-gate additions ensuring contract tests run with existing `poe ci` workflow.

## 4. Technology Stack

- Python 3.11–3.13
- Pydantic v2 (`UnifiedFittingConfig`, `FitResult`, strict input models)
- Typer + Rich (CLI UX and command surface)
- pandas + lmfit/scipy (fitting engine and data handling)
- pytest (unit/integration contract tests)
- Ruff + ty (lint/type quality gates)
- uv + poe (task orchestration)
- Dockerized CI/runtime environments

## 5. Technical Value

**High**.

This epic removes hard runtime failures (notebook constructor mismatch), resolves conflicting output contracts, and prevents “green tests / broken UX” drift through integration-level contract checks. It directly reduces support burden and restores trust in migration claims.

## 6. T-Shirt Size Estimate

**L**.

The work spans multiple boundaries (CLI, notebook templates, export schema, tests, docs) and includes one architectural decision (`_summary.json` authority), but it remains bounded by additive adapters and targeted test coverage rather than broad subsystem rewrites.
