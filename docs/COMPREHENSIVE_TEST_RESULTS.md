# نتائج الاختبار الشامل — Saudi HR

Date: 2026-07-22  
Application: Saudi HR 1.16.5  
Targets: ERPNext v15.117.0 and v16.28.0

## Executive result

The product has been exercised as connected Saudi HR business cycles rather than as isolated schema checks. The deterministic suite discovers 57 test modules and runs 236 tests per ERPNext version. The final result is 236/236 on v15 and 236/236 on v16 (472 successful results, with no skips).

All mutation-heavy automated tests run only on the isolated sites `saudi-qa-v15.localhost` and `saudi-qa-v16.localhost`. The user sites are used only for visual acceptance and targeted schema synchronization.

## Final confirmation

| Target | Modules | Tests | Failures | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: | ---: |
| ERPNext v16.28.0 | 57 | 236 | 0 | 0 | 0 |
| ERPNext v15.117.0 | 57 | 236 | 0 | 0 | 0 |
| Total | 114 module executions | 472 | 0 | 0 | 0 |

Both final runs were executed after the schema, business-logic, core Arabic translation and v15 mobile-route fixes. The final Desk accessibility refinements are JavaScript-only and were verified separately in the live browser and by source checks. Source verification passed on both trees: application quality validation, `git diff --check`, Python byte-compilation, JavaScript syntax checking and shell syntax checking.

## Business-cycle coverage

| Cycle | Real acceptance exercised |
| --- | --- |
| Recruitment and onboarding | Requisition, candidate, employee, contract, onboarding readiness, linked master data, invalid inputs |
| Employment development | Performance review, salary adjustment, promotion/transfer, rating and date limits, salary invariants |
| Exit and settlement | Termination, settlement SLA, EOSB, employee status change, exit interview, clearance |
| Attendance | Shift, check-in/out, daily/monthly attendance, absence, reversed-time rejection, location/mobile states |
| Leave | Annual, sick, special, maternity/paternity, overlap and holiday rules, disbursement |
| Payroll and statutory | Monthly payroll, GOSI cap/contributions, WPS, Nitaqat, permits, loans and protected exports |
| Working time | Overtime, compensatory time, flexible arrangements, statutory working-time controls |
| Governance | Policies, acknowledgements, training, regulatory tasks and audit evidence |
| Employee relations | Grievance, investigation, warning, discipline, decision, appeal and labor dispute |
| Safety and compliance | Injury, medical examination, inspection, violations, corrective actions and legal references |
| Security and integrations | Role scope, self-service, secret masking, HTTPS enforcement, idempotency, private files, protected audit records, guest denial |

## Defects found and corrected

1. Performance reviews accepted invalid date ranges and could average unrated zero rows.
2. Salary adjustments did not reject negative values on every path.
3. Promotion/transfer validation depended on translated labels instead of stable values.
4. GOSI contribution calculations did not cap the contribution base before calculation.
5. Daily attendance accepted an out-time earlier than the in-time.
6. `Special Leave.naming_series` had an invalid/incomplete field definition that blocked real insertion.
7. Medical examination logic wrote to a missing `Work Injury.medical_examination_done` field.
8. ERPNext v16 removed an XLSX helper used by legacy tests; compatibility coverage was updated.
9. ERPNext v15 had stale asset hashes and rendered Desk without CSS; assets were rebuilt and cache cleared.
10. ERPNext v15 lacked the `/app/mobile-attendance` Page route; the standard Desk redirect Page was added and verified.
11. Arabic Desk lists retained English empty states, filters and action labels; application-level Arabic translations were added and verified.
12. The development Procfile ran an asset watcher continuously and aggravated Docker memory pressure; watch is now opt-in (`ENABLE_WATCH=1`) and Gunicorn workers default to 2.
13. ERPNext v15 hooks referenced a missing Desk shortcut asset; the asset was added and its mobile-attendance redirect was verified.
14. Frappe's list-filter widgets exposed `undefined` tooltips and an English Awesomplete accessibility status; a throttled Desk cleanup/localization layer now removes the invalid attributes and announces results in Arabic.
15. Disabling the deterministic visual-QA user left its newest session active and produced a 417 page on the next request; cleanup now force-closes every session before handoff.
16. The v15 workspace inherited a v16-specific description and advanced compliance links retained English titles; the description is now version-neutral and all user-facing module/report names use concise Saudi HR terminology in Arabic.
17. Frappe v15 charts could raise a transient `ResizeObserver/removeChild` exception when the Saudi HR workspace was entered repeatedly; the Desk compatibility layer now ignores only stale chart-node removals, and three consecutive navigation cycles completed with no console errors.

## Visual acceptance

Desktop route checks covered the professional hub, attendance action hub, organization tree, feature and entry pages, compliance command center, enterprise operations center, legal guide, employee/manager self-service and both mobile-attendance routes.

Responsive checks at 390×844 covered five high-value surfaces on each version:

- Professional HR Hub
- Saudi Compliance Command Center
- Saudi Enterprise Center
- Saudi Self-Service
- Mobile Attendance

The measured acceptance result was RTL direction, no horizontal overflow and zero broken images on all responsive routes. Representative v16 record lists were also checked for Employee, Saudi Monthly Payroll, HR Policy Document, Employee Grievance, Labor Inspection and Saudi Government Integration. The v15 Labor Inspection list was re-tested as a representative legacy Desk surface, and the full v15 workspace completed three repeated leave-and-return cycles without console errors after the chart lifecycle correction. Arabic search, notifications, filters, empty states, primary actions and accessibility status were re-tested after translation updates, with zero remaining `undefined` tooltips.

## Environment and safety evidence

- Verified backups were restored into dedicated QA sites before data-heavy testing.
- Government exchanges remained in file/preview or mocked adapter mode; no government, bank or email submission was sent.
- Test exports stayed private and secret values were checked for response/log leakage.
- The visual test user is deterministic, Arabic-enabled and disabled after verification.
- An `OSError: [Errno 12] Cannot allocate memory` observed during one preliminary confirmation run was classified as host/Docker memory exhaustion because the traceback failed while listing an existing source directory. The runtime was changed to remove the continuous watcher, then both final suites passed in isolated low-memory containers.
- Live v15 and v16 acceptance was completed sequentially after a 16 GB workstation could not sustain both complete development stacks plus concurrent Docker workloads. Both web and Socket.IO endpoints passed after recovery; v15 was left as the active user-facing stack and the inactive v16 stack can be started with the documented switch commands.

## Remaining external acceptance

The following cannot be truthfully certified without organization-owned production prerequisites:

- Live Qiwa, GOSI, Mudad and Muqeem credentials/endpoints
- A bank-approved WPS submission channel
- Production SMTP/SMS providers and delivery evidence
- Real device GPS, microphone permissions and voice capture under field conditions
- Production-scale load, disaster-recovery timing and formal legal sign-off

These are deployment gates, not unimplemented application cycles. The application provides preview/file exchange, validation, audit and failure paths for them.

## Reproduction

Run the deterministic suite on each isolated QA site:

```text
bench --site saudi-qa-v16.localhost execute saudi_hr.saudi_hr.comprehensive_testing.run_comprehensive_test_suite
bench --site saudi-qa-v15.localhost execute saudi_hr.saudi_hr.comprehensive_testing.run_comprehensive_test_suite
```

The returned JSON includes module names, counts, failures/errors, identifiers and concise tracebacks.
