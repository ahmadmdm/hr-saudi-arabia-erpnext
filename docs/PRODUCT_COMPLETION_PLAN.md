# Saudi HR — Product Completion Plan

## Objective

Deliver Saudi HR as an auditable, Arabic-first HR operating product on ERPNext v15 and v16. The product must turn the attached Saudi Labor Law Executive Regulations into guided controls, evidence, alerts, and tested employee-lifecycle workflows.

## Definition of done

The release is complete only when all of the following are true:

- Every implemented legal rule has a source page, operational control, owner, evidence requirement, and automated test where calculation is possible.
- Overtime, compensatory leave, alternative work, leave, settlement, document return, disciplinary, records, inclusion, and maternity rules match the attached regulation.
- The same critical behavior passes on ERPNext v15 and v16.
- The Arabic experience is native RTL, concise, readable, keyboard-accessible, responsive at 375, 768, 1024, and 1440 pixels, and does not depend on English to understand an action.
- A compliance owner can see risks, deadlines, missing evidence, and the next action from one command center.
- Employee and manager journeys use guided actions and permission-aware self-service.
- Demo data covers healthy, warning, overdue, rejected, and boundary scenarios without changing real production data.
- Unit, integration, migration, quality, and visual checks are recorded in `docs/RELEASE_READINESS.md`.
- Known legal interpretations or non-automated obligations are clearly marked for qualified legal review; the product does not present itself as legal advice.

## Delivery slices and acceptance criteria

### 1. Legal baseline

- Publish a controlled compliance matrix from the attached PDF.
- Add stable rule identifiers, effective dates, Arabic and English summaries, severity, source pages, and test references.
- Acceptance: no critical rule exists only in prose; every critical rule points to a working control or a clearly labeled manual review.

### 2. Statutory calculations and deadlines

- Correct overtime cash calculation and compensatory-leave conversion, use deadline, annual cap, and unused balance treatment.
- Align final settlement and document return to the 7-day employer / 14-day employee termination timelines.
- Complete flexible-work eligibility, monthly limits, overtime threshold, Nitaqat credit, excluded benefits, and contract conversion warnings.
- Acceptance: automated boundary tests pass for every numeric threshold.

### 3. Compliance operations

- Seed the legal reference matrix and regulatory tasks idempotently.
- Provide evidence status, owner, due date, severity, and guided remediation.
- Acceptance: re-running setup creates no duplicates and overdue items appear in the command center.

### 4. Professional command center

- Consolidate people operations, compliance health, urgent cases, guided journeys, and reports.
- Provide loading, empty, permission, and error states with recovery actions.
- Acceptance: HR Manager can reach every primary action in two interactions or fewer.

### 5. Arabic-first design and content

- Repair corrupted Arabic catalog content and apply shared design tokens.
- Use Arabic-first labels, active-verb buttons, plain recovery messages, logical CSS properties, and reduced-motion support.
- Acceptance: no mojibake, clipped RTL text, unexplained English-only control, or inaccessible focus state remains in tested pages.

### 6. Demo and verification

- Seed safe demo employees and records for normal and edge scenarios.
- Run logical, permission, migration, and quality tests on both versions.
- Run interactive visual checks at desktop, tablet, and mobile widths.
- Acceptance: release-readiness evidence lists the environment, commands, passed checks, visual findings, and any residual limitation.

## Product patterns adopted

The implementation uses mature HCM patterns: one employee source of truth, role-aware self-service, guided employee events, proactive alerts, evidence completeness, case ownership, localized compliance, and actionable analytics. These patterns are adapted to ERPNext and Saudi regulation rather than copied as vendor-specific screens.

## Release checkpoints

1. Legal rules and tests approved.
2. Operational command center usable with demo data.
3. Arabic and accessibility review passed.
4. v15 and v16 migration and regression checks passed.
5. Visual evidence and release notes complete.
