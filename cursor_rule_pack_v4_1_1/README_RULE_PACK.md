# Cursor Rule Pack v4.1.1 (YAML-aligned)

```yaml
user_rules_settings_v4_1_1:
  output:
    language: "KR concise + EN-inline"
    default_lines_max: 4
    number_format: "2-dec"
    section_order: ["ExecSummary","Visual","Options","Roadmap","Automation","QA"]
    end_with_cmds: 3
  edit_scope:
    allowed_paths: ["src/**"]
  tdd:
    source_of_truth: "plan.md"
    go_behavior: "next_unmarked_test"
    loop: ["Red","Green","Refactor"]
    test_sla: {unit_s: 0.20, integration_s: 2.00, e2e_min: 5.00}
  git:
    commits: "Conventional Commits"
    branch_model: "Trunk + short-lived feature/*"
    structural_types: ["refactor","style","docs","chore"]
    behavioral_types: ["feat","fix","perf","test"]
  ci_quality_security:
    coverage_min: 85.00
    linters: ["black","flake8","isort"]
    security: ["bandit","pip-audit --strict","ggshield"]
    codeowners_required_approvals: 2
  python_excel:
    excel_new: "XlsxWriter"
    excel_edit: "openpyxl"
    pandas_role: "IO layer"
    sheet_update: 'if_sheet_exists="replace"'
  domain_hvdc:
    triggers:
      rate_change_pct: 10.00
      eta_delay_h: 24.00
      pressure_t_per_m2_max: 4.00
      cert_expiry_days_min: 30.00
    human_gate: ["FANR","MOIAT"]
  modes: ["PRIME","ORACLE","ZERO","LATTICE","RHYTHM","COST-GUARD"]
```

Install
1) Copy `.cursor/rules/*` to the repo root.
2) `pip install pre-commit` → `pre-commit install` → `pre-commit install --hook-type commit-msg`
3) GitHub: Protect `main` + Require review from Code Owners (2 approvals).
4) Open a PR and check CI gates (coverage ≥ 85.00; lint=0; bandit High=0; secrets=0).
