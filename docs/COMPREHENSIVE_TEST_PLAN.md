# Saudi HR — Comprehensive Product Test Plan

Date: 2026-07-22  
Scope: Saudi HR 1.16.5 on ERPNext v15.117.0 and v16.28.0

## Objective

Prove every material Saudi HR capability through repeatable application tests and live Arabic user journeys. A feature is not considered covered by schema presence alone: coverage requires valid creation, negative validation, permission enforcement, state transition, calculated or persisted outcome, and a visible user path where applicable.

## Baseline inventory

- 71 parent DocTypes and 11 child-table DocTypes.
- 13 workflow definitions covering 12 document types.
- 10 custom Desk pages and 19 reports.
- 52 existing Python test modules.
- 32 parent DocTypes have a directly named test file; 39 do not.
- The former critical suite executes 8 modules and 38 tests, so it remains a release smoke suite rather than full product coverage.

## Coverage standard

Each business cycle must demonstrate:

1. Valid data creation with realistic Saudi HR values and linked master data.
2. Rejection of missing, contradictory, duplicate, expired, overlapping, or out-of-range data.
3. Correct permissions for employee, manager, HR, finance, and system roles.
4. Every allowed workflow transition and rejection of an unauthorized transition.
5. Correct calculations, deadlines, generated child records, accounting/export output, and audit evidence.
6. Idempotent retry behavior for imports, synchronization, scheduled jobs, and government file exchange.
7. Arabic and RTL rendering, responsive layout, keyboard access, loading/empty/error/success states, and no console errors.
8. Identical acceptance on ERPNext v15 and v16 unless a documented framework difference is unavoidable.

## Execution phases

### Phase 1 — Test infrastructure and baseline

- Discover and execute all Saudi HR test modules without ERPNext's unrelated global test-record generator.
- Produce a machine-readable coverage inventory for DocTypes, workflows, pages, reports, and API services.
- Run only on isolated QA sites restored from verified backups.

Acceptance: every existing test is executed on both versions; failures are recorded by module and are reproducible.

### Phase 2 — Employee lifecycle

- Hiring requisition, candidate, employment contract, onboarding, probation/readiness, promotion/transfer, performance, warning/discipline, grievance/investigation/appeal, termination, clearance, interview, EOSB, and settlement SLA.

Acceptance: the same employee can traverse the complete lifecycle, with role boundaries and statutory deadlines verified.

### Phase 3 — Time, leave, payroll, and statutory exchange

- Shift types and assignments, check-in, daily/monthly attendance, absence, annual/sick/special/maternity leave, overlap rules, flexible work, overtime, payroll calculation/import/journal entry, loans, GOSI, WPS, Nitaqat, work permits, and government exports.

Acceptance: calculations reconcile from attendance through payroll and statutory output; invalid IBAN, overlaps, limits, duplicates, and failed exports are rejected or routed for correction.

### Phase 4 — Governance, safety, and compliance

- Policies and acknowledgements, legal catalog/releases, inspections, safety risks, work injuries, medical examinations, training, disability accommodations, recruitment-provider controls, regulatory filings, document custody, disputes, and compliance actions.

Acceptance: deadlines, evidence, immutable audit identity, escalation, and closed-loop resolution are verified.

### Phase 5 — Security and self-service

- Employee-only data, manager team scope, HR/finance separation, secret masking, export confirmation, tamper resistance, portal actions, error states, and scheduled jobs.

Acceptance: privilege escalation and cross-employee access attempts fail; secrets never appear in responses, logs, screenshots, or fixtures.

### Phase 6 — Live visual acceptance

- Exercise every custom page plus representative create/read/update/submit/workflow/report paths at 375, 768, 1024, and 1440 pixels.
- Verify Arabic copy, RTL direction, focus order, 44-pixel touch targets, contrast, internal scrolling, dialogs, and browser console/network health.

Acceptance: every route has a captured pass/fail record and every reproducible UI defect is fixed and re-tested.

## Release gates

- Zero failing or errored comprehensive tests on v15 and v16.
- Zero uncovered critical workflow transitions.
- All parent DocTypes classified as fully covered, schema-only, configuration-only, or intentionally delegated to ERPNext, with evidence.
- All custom pages and reports have a live route check; critical cycles have full visual interaction checks.
- Final coverage matrix, defect log, backup/restore evidence, and remaining external prerequisites are documented.

## Safety rules

- Comprehensive tests run on isolated QA sites, never directly against the user's live data.
- Government operations stay in preview/file-exchange mode without approved credentials and endpoints.
- Test exports remain private and no email, bank, or government submission is sent.
- QA sites and records use stable markers and can be removed without selecting broad filesystem or database targets.
