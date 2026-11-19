# Archived scripts

These scripts are kept for reproducibility only. They are **not** part of the
normal application, pipeline, evaluation, or test path.

| Group | Files | Why archived |
|---|---|---|
| v1 evaluators | `evaluate_answers.py`, `evaluate_retrieval.py` | Superseded by `scripts/evaluation/`. |
| Gold builders | `build_gold_v2.py`, `update_gold_v3_1.py` | One-time dataset construction; gold is now frozen. |
| Diagnostics | `_inspect.py`, `audit_v31_state.py`, `compare_v3_v31.py`, `diagnose_failures_v31.py`, `inspect_q78.py`, `inspect_v31_rows.py` | One-off investigations for earlier phases. |
| Experiments | `experiment_q56_variants.py`, `experiment_q56_variants2.py`, `experiment_query_variants.py` | Read-only query/retrieval experiments. |
| Old tests / smoke checks | `e2e_format_test.py`, `smoke_retrieval_v3.py`, `smoke_test.py`, `test_app_flows.py`, `test_retrieval.py`, `ui_expander_test.py` | Superseded by `tests/` or depended on historical fixtures. |
| Calibration | `calibrate_threshold.py` | The `0.08` threshold is now locked. |
| Reporting | `make_report_pdf.py` | One-off progress-report generator. |

## Running archived scripts

Some archived scripts read historical files now stored under
`data/evaluation/archive/` or `docs/history/`. If a replay is needed, update
that script's input/output paths first. The active suites in `tests/` are the
supported regression path.

Use the current equivalents whenever possible:

| Old script | Current replacement |
|---|---|
| `evaluate_answers.py` | `scripts/evaluation/evaluate_answers.py` |
| `evaluate_retrieval.py` | `scripts/evaluation/evaluate_retrieval.py` |
| `test_*.py` smoke checks | `tests/run_all.py` |
