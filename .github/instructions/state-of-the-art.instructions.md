---
applyTo: "spectrafit/**/*.py,prototype/**/*.py,docs/**/*.md"
---

# State of the Art — Scientific Context

## SpectraFit's Scientific Domain

SpectraFit fits **1D–3D X-ray absorption / emission spectra** using least-squares
minimisation (`lmfit` / `scipy`). Key use cases: RIXS, XAS, XPS peak decomposition
with Gaussian, Lorentzian, pseudo-Voigt, Pearson, and related line shapes.

## Reference Projects (Current State of the Art)

| Project | Relevance |
|---------|-----------|
| [lmfit](https://lmfit.github.io/lmfit-py/) | Core fitting engine; supports emcee MCMC, confidence intervals, named parameters, model composition |
| [pyglotaran](https://github.com/glotaran/pyglotaran) | Protocol-driven, modular global/target analysis for time-resolved spectra — **primary architecture reference** for FittingStep Protocol |
| [jaxspec](https://github.com/renecotyfanboy/jaxspec) | JAX-accelerated Bayesian X-ray spectral fitting — future reference for GPU acceleration |
| [arviz](https://python.arviz.org/) | Bayesian inference visualisation for MCMC output (post-fit UQ) |
| [emcee](https://emcee.readthedocs.io/) | MCMC ensemble sampler; integrated into lmfit via `method="emcee"` |

## Implemented Scientific Features

- **Least-squares minimisation** — via lmfit (`leastsq`, `least_squares`, `nelder`, etc.)
- **Confidence interval estimation** — via `lmfit.conf_interval` (postprocessing)
- **Global fitting** — shared parameters across multiple spectra (`GlobalMode.GLOBAL`)
- **Cross-component constraints** — `expr = "p1.center + 1.0"` dot-notation
- **v1 backward compatibility** — `migrate_v1_format()` in `UnifiedFittingConfig`

## Planned / In-Progress Scientific Features

### MCMC / Bayesian UQ (SCI-001)

`lmfit` integrates `emcee` natively. To use it:

```python
from spectrafit.core.fitting_config import UnifiedFittingConfig
cfg = UnifiedFittingConfig(peaks={...}, minimizer={"nan_policy": "propagate"})
# Set method="emcee" in SolverConfig when SolverConfig is wired (Phase 8)
```

Status: **lmfit support exists**; `SolverConfig.method = "emcee"` wiring is Phase 8.

### Batch / Parallel Fitting (SCI-002)

For batch processing of many spectra, `BatchFittingConfig` (Phase 8) will use
`concurrent.futures.ProcessPoolExecutor`:

```python
# Planned API (Phase 8)
from spectrafit.core.batch import BatchFittingConfig
batch = BatchFittingConfig(spectra=[DataConfig(...)], workers=4)
results = batch.run()
```

### Interactive Visualisation (Phase 8 evaluation)

Currently: static `seaborn` / `matplotlib` plots. Evaluation of `plotly` or `altair`
for HTML-embedded interactive output is planned in a spike:
`docs/spikes/visualization-interactive-output-spike.md`.

### MCP Server (Deferred — After Phase 5+)

`UnifiedFittingConfig.model_json_schema()` will directly serve as the MCP input schema.
MCP tool surface is defined in `docs/spikes/api-mcp-server-design-spike.md`.
**Do not start MCP implementation until `UnifiedFittingConfig` is the sole pipeline entry point.**

## Known Gaps vs. State of the Art

| Gap | Priority | Notes |
|-----|----------|-------|
| GPU acceleration (JAX backend) | Low | Relevant for large-scale batch fitting; jaxspec is the reference |
| Full Bayesian posterior sampling | Medium | lmfit/emcee is available; needs API surface |
| ML-assisted initial parameter guessing | Low | Could use `scipy.signal.find_peaks` heuristics |
| Polars for large-file loading | Low | Spike needed if >2× speedup demonstrated |
| Interactive HTML reports | Medium | Plotly/Altair spike planned |
| Time-resolved global analysis | Medium | `FittingContext(mode=FittingMode.TIME_RESOLVED)` skeleton exists; pyglotaran is reference |

## Python / Ecosystem Versions

| Component | Minimum | Tested |
|-----------|---------|--------|
| Python | 3.10 | 3.10 – 3.13 |
| lmfit | 1.3 | latest |
| pydantic | 2.0 | v2.x |
| numpy | 1.26 | latest |
| pandas | 2.0 | latest |
| scipy | 1.10 | latest |

Always target the **oldest supported Python** (3.10) for syntax choices. Use `X | Y`
union syntax (not `Union[X, Y]`) and `dict[K, V]` (not `Dict[K, V]`).
