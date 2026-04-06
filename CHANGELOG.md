# Changelog

All notable changes to `saudi_hr` are documented in this file.

## v1.10.0 - 2026-04-06

- Added payroll workbook validation with blocking errors so imports fail fast when net salary, required field, duplicate, or structural workbook issues are detected.
- Added a downloadable payroll import template with `Instructions`, `Example`, and upload sheets to standardize payroll workbook preparation.
- Added automatic Employee creation during payroll import with configurable default gender, date of birth, and joining date values on the payroll document.
- Added row-level payroll cost center support, automatic cost center resolution/creation from workbook values, and cost-center-aware payroll expense posting.
- Merged duplicate journal entry account rows during payroll posting to avoid repeated credit/debit lines for the same account and cost center combination.
- Reorganized the Saudi HR workspace for operational use with Arabic section headings, start/daily action blocks, reduced top charts, and separated employee relations from compliance/legal sections.

## v1.9.0 - 2026-04-05

- Added the new `Exit Interview` DocType and linked it to `Exit Clearance` so offboarding can track interview completion from the same separation workflow.
- Added the new `Salary Adjustment` DocType with calculated adjustment amount/percentage and back-link synchronization to `Performance Review`.
- Added the new `Promotion Transfer` DocType to capture employee movement decisions and synchronize recommendation state with `Performance Review`.
- Extended the Saudi HR workspace so the new lifecycle features are grouped under `Performance & Development` and `Separation & Offboarding`.
- Revalidated the new DocTypes on the live Frappe v15 site, including migration, asset build, cache clear, and direct UI route checks.

## v1.8.1 - 2026-04-02

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