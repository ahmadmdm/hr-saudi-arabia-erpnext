# Saudi HR — Enterprise Product Phase

## Objective

Turn the completed Saudi HR compliance application into an Arabic-first enterprise operating product. The phase reuses the existing payroll, WPS, policy acknowledgement, legal catalog, employee lifecycle, and compliance modules; it adds a governed integration layer, self-service experience, executive analytics, grounded legal guidance, and deployment-readiness controls.

## Architecture decisions

- Government platforms use a provider adapter and auditable transaction ledger. File exchange is usable immediately; live API mode remains disabled until the organization supplies an approved endpoint and encrypted credentials.
- No outbound government submission is made implicitly. Every transfer has an explicit preview, confirmation, actor, fingerprint, and outcome.
- Employee and manager self-service reuses the existing Saudi HR documents and permission rules rather than creating duplicate records.
- Legal guidance is deterministic and grounded in the effective-dated 28-rule catalog. It returns sources and operational actions and does not present itself as legal advice.
- Enterprise security readiness reports configuration and gaps; identity enforcement remains under the standard Frappe authentication controls.

## Visual direction

- Subject: a Saudi HR operations room for HR managers, payroll teams, managers, and employees.
- Palette: Registry green `#0B5D4B`, palm `#13795B`, ink `#13251F`, parchment `#F3F0E7`, sand `#D6C7A1`, urgent clay `#B54432`.
- Type: `Noto Kufi Arabic` for restrained display headings, `Noto Sans Arabic`/`Tajawal` for body copy, and the system monospace stack for transaction fingerprints.
- Layout: an RTL operating ledger with a government-provider rail, capability rows, and evidence-first action panels.
- Signature element: a four-station government route rail that shows Qiwa, GOSI, Mudad, and Muqeem readiness without imitating their brands.

```text
┌──────────────────────────────────────────────────────────┐
│ readiness seal       title + scope         primary action │
├──────────────────────────────────────────────────────────┤
│ Qiwa ── GOSI ── Mudad ── Muqeem   provider route rail    │
├───────────────────────────┬──────────────────────────────┤
│ capability ledger         │ risks, deadlines, evidence   │
├───────────────────────────┴──────────────────────────────┤
│ transactions / analytics / legal guidance / readiness    │
└──────────────────────────────────────────────────────────┘
```

## Task plan and acceptance criteria

### Task 1 — Government integration ledger

- Add provider profiles for Qiwa, GOSI, Mudad, and Muqeem with file/API modes and encrypted credential fields.
- Add immutable-style transaction records with actor, direction, status, fingerprint, count, reference, and evidence.
- Reject live mode without an approved endpoint and credentials; never expose credentials through whitelisted responses.
- Verification: schema migration and provider/transaction unit tests pass.

### Task 2 — Safe provider exports and reconciliation

- Provide previewable Qiwa contract, GOSI contribution, Mudad WPS, and Muqeem authorization payloads from existing records.
- Record every confirmed export in the integration ledger and keep dry-run previews side-effect free.
- Add payroll/WPS readiness and rejection follow-up to the enterprise summary.
- Verification: adapter tests cover provider validation, deterministic fingerprints, empty data, dry runs, and confirmed transactions.

### Task 3 — Arabic employee and manager self-service

- Resolve the signed-in user's employee record without bypassing permissions.
- Present personal requests, policy acknowledgements, attendance, documents, payroll links, and manager approvals in Arabic.
- Provide empty and no-employee states with a clear next action.
- Verification: service permission tests and responsive visual checks pass.

### Task 4 — Enterprise operations center

- Show live capability readiness, providers, WPS, policies, compliance, analytics, legal-release status, and security gaps.
- Link each card to a real page, report, or document list; no decorative dead actions.
- Use an Arabic-first RTL experience with keyboard focus, 44-pixel mobile targets, reduced motion, and no horizontal overflow.
- Verification: API contract tests, JavaScript syntax, build, and browser checks at 375/768/1024/1440 pixels pass.

### Task 5 — Grounded Arabic HR guide

- Search the effective legal catalog using normalized Arabic terms.
- Return article/page/source citations, operational controls, evidence requirements, and safe draft templates.
- Display an explicit legal-review notice and never fabricate a source.
- Verification: Arabic normalization and citation-presence tests pass.

### Task 6 — Legal updates and enterprise readiness

- Compare the source catalog with synchronized rules and surface additions, changes, removals, and activation status.
- Report MFA/identity, email, backups, scheduled jobs, integration credentials, permissions, and demo-data readiness without leaking secrets.
- Provide an actionable production checklist and white-label organization settings.
- Verification: readiness checks behave correctly when configuration is complete, partial, or absent.

### Task 7 — Product registration, Arabic copy, and demo proof

- Register the new pages in the professional HR catalog/workspace and Arabic translation file.
- Seed safe provider profiles and successful/warning/error demo transactions idempotently.
- Keep v15 and v16 source parity.
- Verification: repeated demo seed preserves identifiers and the catalog has complete Arabic titles/descriptions.

### Task 8 — Release verification and visual repair

- Run compile, JSON, translation, quality, unit, logical, migration, build, HTTP, and Socket.IO checks on v15 and v16.
- Visually exercise all new routes, provider filters, self-service state, legal search, and mobile layouts.
- Repair every reproducible application defect found and document any environment-only limitation.

## Definition of done

- Each capability has persistent data or a live computed service, a permission-aware API, an Arabic user path, automated verification, and a real navigation target.
- No secret appears in API responses, logs, demo data, screenshots, or source control.
- No government API is described as live unless an approved production endpoint and credentials are configured and a confirmed transaction succeeds.
- Both supported ERPNext versions migrate, build, and pass the same critical acceptance suite.
- Visual acceptance covers desktop, tablet, and mobile with RTL, keyboard accessibility, meaningful empty/error states, and no clipped controls.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Government API access is unavailable | Ship file exchange and adapter contracts now; require explicit approved credentials for live mode. |
| Government schemas change | Version every adapter payload and transaction fingerprint; keep provider mapping isolated. |
| Employee data exposure | Resolve the current employee server-side and reuse Frappe permissions; never accept an arbitrary employee from the client. |
| Legal guidance is mistaken for advice | Cite the catalog/PDF, label guidance operational, and route fact-specific cases to qualified review. |
| Existing dirty worktree is overwritten | Touch only scoped files and mirror the same scoped files to v15 after verification. |
