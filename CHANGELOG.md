# Changelog

All notable changes to `saudi_hr` are documented in this file.

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