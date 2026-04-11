# Changelog

All notable changes to `saudi_hr` are documented in this file.

## v1.12.0 - 2026-04-11

- Hardened Saudi Monthly Payroll workbook imports with blocking validation for missing required columns and critical duplicate-name warnings when rows omit an explicit cost center.
- Added persistent upload guidance on the payroll form, plus a pre-import review gate so risky workbooks are stopped before import.
- Expanded workbook analysis and validation dialogs to surface critical review items directly in the UI.
- Strengthened the detailed payroll import template with highlighted required fields, dropdown-based cost center and payout mode inputs, and numeric validation rules.
- Added a simplified Arabic payroll upload template for end users alongside the detailed administrative template.
- Extended payroll regression coverage for required workbook headers, critical warning detection, zero-salary leave skipping, stricter employee matching, and generated template validations.

## v1.11.0 - 2026-04-07

- Added employee paid payroll history directly on the Employee salary tab, sourced from completed Saudi Monthly Payroll runs with linked journal entries.
- Introduced Salary Adjustment, Promotion Transfer, and Exit Interview DocTypes and linked them into performance review and exit clearance workflows.
- Expanded Saudi Monthly Payroll with workbook validation, import templates, automatic employee creation defaults, cost-center-aware payroll distribution, and grouped journal entry generation.
- Refreshed the Saudi HR workspace structure and shortcuts to surface daily operations, payroll, and lifecycle navigation more clearly.

## v1.8.1 - 2026-04-02

- Extended `Saudi Monthly Payroll Employee` rows to persist workbook-only payroll context fields: work location, designation, salary mode, GOSI registration, working days, absence days, and late hours.
- Updated payroll workbook import mapping so those fields survive the actual import flow and remain visible in imported payroll rows.
- Normalized workbook gross salary when `إجمالي البدلات` already includes `الإضافي`, eliminating false `net salary mismatch` warnings during live payroll imports.
- Allowed placeholder employee creation from imported payroll rows to reuse a valid `Designation` where available.
- Expanded payroll regression coverage and reverified the full `saudi_hr` suite with 78 passing tests.

## v1.8.0 - 2026-04-02

- Removed remaining runtime `ignore_permissions` bypasses from mobile attendance/leave APIs and key compliance, policy, legal, and settings flows.
- Added explicit doctype permission checks for journal entries, compliance actions, regulatory tasks, policy acknowledgements, employee warnings, and disciplinary decision logs.
- Hardened payroll calculations with prorated sick-leave deduction across month boundaries, zero-basic-salary protection, and import audit comments.
- Added concurrency protection for payroll loan deductions so the same installment cannot be deducted by conflicting payroll runs.
- Unified EOSB calculation logic between document validation, helper functions, and preview API, with stricter validation for invalid/over-deducted cases.
- Tightened annual leave validation so requests cannot cross calendar years or start before employee joining date.
- Verified packaging dependencies remain aligned across `pyproject.toml`, `setup.py`, and `requirements.txt` with only `openpyxl` and `openlocationcode` as runtime package dependencies.
- Expanded regression coverage to 77 tests and verified the full `saudi_hr` suite passes.

## v1.7.0 - 2026-04-01

- Added the comprehensive employee print format and related workspace shortcut.

## v1.6.0 - 2026-03-31

- Expanded automated unit coverage for payroll and account lookup behavior.

## v1.5.0 - 2026-03-27

- Delivered the standalone release above `frappe` and `erpnext` only, with payroll loans and governance doctypes.