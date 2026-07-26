# Saudi HR — Release Readiness

Date: 2026-07-22  
Candidate: Saudi HR 1.16.5 on ERPNext 15.117.0 and 16.28.0  
Legal source: `اللائحة التنفيذية لنظام العمل وملحقاتها.pdf` (109 PDF pages)

## Scope delivered in source

- Controlled, effective-dated legal catalog with 28 unique rules and PDF page references.
- Automated controls for overtime cash pay, 720-hour annual limit, 1.5x compensatory leave, 60-day use window, 30-day ordinary annual cap, and unused-balance exit payout.
- Employer/employee termination settlement and document-return deadlines of 7/14 days.
- Flexible-work Saudi eligibility, 95/160-hour thresholds, Nitaqat credit, excluded entitlements, one-year maximum, consent, and conversion review.
- Rolling sick-leave benefit year from the first absence, auditable 30/60/30 pay-tier allocation, overlap prevention, and cycle-boundary review.
- 12-week maternity controls and related child-care extensions.
- Permission-aware Saudi compliance command center and Arabic-first RTL professional HR hub.
- Idempotent demo pack covering healthy, warning, boundary (160 hours), rejected, overdue, exit-payout, and mixed sick-leave pay-tier scenarios.
- Idempotent legal-catalog synchronization across every configured company.
- Arabic encoding, RTL, keyboard focus, reduced motion, legal-catalog integrity, and demo-scenario checks in the quality gate.
- Enterprise integration profiles and auditable transactions for Qiwa, GOSI, Mudad, and Muqeem, with masked previews and no unapproved outbound submission.
- Arabic employee/manager self-service, electronic policy acknowledgements, grievance access controls, payroll summaries, and production-readiness checks.
- A grounded Arabic legal guide with normalized search, PDF-page citations, operational controls, and safe draft templates.

## Verification record

| Check | ERPNext v15 | ERPNext v16 | Evidence |
|---|---|---|---|
| Python compile | Passed | Passed | `python -m compileall -q saudi_hr` |
| JavaScript syntax | Passed | Passed | `node --check` for command center and HR hub |
| JSON validity | Passed | Passed | all application JSON parsed by quality gate |
| Git whitespace check | Passed | Passed | `git diff --check` |
| Saudi HR quality gate | Passed | Passed | `python scripts/validate_quality.py` |
| Legal catalog | Passed | Passed | 28 IDs, exactly aligned with the documented matrix |
| Arabic source integrity | Passed | Passed | Arabic content present; no mojibake markers |
| Pure legal boundary assertions | Passed | Passed | overtime, compensatory leave, settlement, flexible work, maternity, rolling sick-leave cycle, and mixed pay tiers |
| Isolated service assertions | Passed | Passed | HR role enforcement, command-center payload/health, and 28-rule synchronization across two companies |
| Schema and migration hooks | Passed | Passed | v16 completed the full migration; v15 completed enterprise schema sync, then the corrected cross-version `after_migrate` hook separately after a transient Docker shared-filesystem `ENOMEM` during the repeat full scan |
| Application asset build | Passed | Passed | `bench build --app saudi_hr`; translations compiled |
| Demo seed and repeat safety | Passed | Passed | repeated seed retained the same employee, contract, leave, overtime, settlement, and task IDs; legal sync reported 0 created / 28 updated |
| Full backup and isolated restore drill | Passed | Passed | fresh database/public/private/config backups were archive-tested, restored into isolated sites, verified by 25/25 live checks and 38/38 logical tests, and protected with SHA-256 manifests; see `docs/DISASTER_RECOVERY.md` |
| Live database acceptance | 25/25 passed | 25/25 passed | `get_demo_acceptance_snapshot`; 0 failed on both sites |
| Critical logical suite | 38/38 passed | 38/38 passed | 8 modules executed inside initialized Frappe sites; 0 failures, errors, or skips |
| Command-center service | Passed | Passed | 28 legal rules, 27 automated, 96% automation, health 85, and seeded overdue actions |
| HTTP health | 200 | 200 | `/api/method/ping` on ports 19015 and 19001 |
| Realtime health | 200 | 200 | Engine.IO handshake on ports 9015 and 9000; v15 container/client port mismatch corrected |
| Interactive visual acceptance | Passed at 375/768/1024/1440 | Shared frontend built and service-verified | Live v15 browser run covered the enterprise center, self-service, policy dialog, provider preview, legal search, tablet/desktop layouts, mobile RTL, internal table scrolling, and 44-pixel controls; the same source and assets were built on v16 |

## Live acceptance result

The executable acceptance snapshot verified these statutory and operating boundaries against seeded database records on both versions:

- 28 catalog rules and 27 automated controls.
- A rolling sick-leave year with 25 prior days, a 10-day request allocated 5 days at 100% and 5 days at 75%, and an 87.5% effective rate.
- Flexible-work overtime beginning after 95 hours and one Nitaqat credit at exactly 160 hours.
- Two overtime hours converted to three paid compensatory-leave hours with a 60-day use deadline.
- A 14-day employee-initiated settlement deadline, the same document-return deadline, and SAR 187.50 payout for six unused hours at SAR 31.25.
- One intended overdue settlement and one intended overdue regulatory task in the command center.
- One and only one copy of each marked overtime demo after repeated seeding across a date boundary.
- Four government-provider profiles, three audit-ledger outcomes, one WPS rejection follow-up, one pending electronic policy acknowledgement, and a fully synchronized legal release.
- Arabic sick-leave search with a cited PDF source and page on every returned rule.

The first attempt to use Frappe v16's global `run-tests` record generator stopped before loading Saudi HR tests because the base site does not contain the optional `Payment Gateway` DocType. The release suite therefore loads the same eight Saudi HR test modules directly inside an initialized site. This executes all 38 test methods while avoiding unrelated optional ERPNext fixture generation.

## Visual acceptance result

- Command center: native RTL, Noto Sans Arabic/Tajawal stack, risk-first actions, 44-pixel mobile controls, and responsive 1/2/2/4-column behavior without horizontal overflow at 375, 768, 1024, and 1440 pixels.
- Professional HR Hub: changed from locale-dependent English-first rendering to Arabic-first `dir="rtl" lang="ar"`, with English as supporting copy.
- Arabic search: normalizes the definite article, hamza forms, diacritics, alif maqsura, and ta marbuta. The phrase `إجازة مرضية` returned exactly `سير موافقة الإجازة المرضية` and `الإجازة المرضية السعودية`.
- Search workflow: category cards hide while searching so results are immediately visible on mobile; clearing the input restores all 83 services.
- The v15 browser run verified command-center actions, routing to the professional hub, desktop/tablet/mobile rendering, guided journeys, quick actions, empty-safe search behavior, and absence of clipped content.
- The enterprise-center hero contrast, mobile min-content overflow, internal transaction-table containment, preview fingerprint wrapping, and 44-pixel legal-topic targets were repaired from the live visual findings.
- The employee policy dialog was opened and dismissed without submitting; the provider preview was opened with masked data and dismissed without creating a file or transaction.
- Docker development ports now match inside and outside each container, so Socket.IO can authenticate against the visible origin without `ECONNREFUSED`; no new realtime errors appeared after reload.
- v16 used the same source files and passed its own asset build, API payload, 38 logical tests, and 25 live checks.

## Repeatable release commands

### ERPNext v15

```powershell
Set-Location C:\Users\ahmad\Documents\erpnext\v15
docker compose exec -T bench bench --site erp15.localhost migrate --skip-search-index
docker compose exec -T bench bench build --app saudi_hr
docker compose exec -T bench bench --site erp15.localhost execute saudi_hr.saudi_hr.demo_lifecycle.seed_employee_lifecycle_demo
docker compose exec -T bench bench --site erp15.localhost execute saudi_hr.saudi_hr.demo_lifecycle.get_demo_acceptance_snapshot
docker compose exec -T bench bench --site erp15.localhost execute saudi_hr.saudi_hr.demo_lifecycle.run_logical_acceptance_suite
```

### ERPNext v16

```powershell
Set-Location C:\Users\ahmad\Documents\erpnext
docker compose exec -T bench bench --site erp.localhost migrate --skip-search-index
docker compose exec -T bench bench build --app saudi_hr
docker compose exec -T bench bench --site erp.localhost execute saudi_hr.saudi_hr.demo_lifecycle.seed_employee_lifecycle_demo
docker compose exec -T bench bench --site erp.localhost execute saudi_hr.saudi_hr.demo_lifecycle.get_demo_acceptance_snapshot
docker compose exec -T bench bench --site erp.localhost execute saudi_hr.saudi_hr.demo_lifecycle.run_logical_acceptance_suite
```

## Disaster-recovery verification

- A fresh full backup was created and restored into isolated temporary sites for both supported ERPNext versions on 2026-07-22.
- ERPNext v16 was missing a generated site encryption key before the drill. The standard Frappe key generator was invoked without printing the key, the backup was recreated, and the restored site was verified against the protected key from the configuration backup.
- Both restored sites passed 25/25 live acceptance checks and 38/38 logical tests. Database and file archives also passed integrity checks, and SHA-256 manifests were generated beside the backup sets.
- Production-readiness is now 62% on both sites. The remaining failed checks are MFA, outgoing email, and intentional demo markers; details and the repeatable procedure are in `docs/DISASTER_RECOVERY.md`.

The command center is operational guidance based on the attached regulation and does not replace qualified legal review of fact-specific cases. Before production go-live, replace demo data with the organization's approved policies, owners, evidence, payroll accounts, and qualified legal interpretations.
