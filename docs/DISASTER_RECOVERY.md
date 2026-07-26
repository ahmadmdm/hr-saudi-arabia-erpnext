# Saudi HR — Disaster Recovery Runbook

Last verified: 2026-07-22

## Verified recovery result

| Environment | Backup set | Restore result | Application verification |
|---|---|---|---|
| ERPNext v16 / `erp.localhost` | `20260722_092941-erp_localhost-*` | Restored into an isolated site with the original encryption key | 25/25 live checks and 38/38 logical tests passed |
| ERPNext v15 / `erp15.localhost` | `20260722_065401-erp15_localhost-*` | Restored into an isolated site with the original encryption key | 25/25 live checks and 38/38 logical tests passed |

Each set contains a compressed database, public files, private files, the protected site configuration, and a `.sha256` manifest. The temporary recovery sites were removed after verification.

## Security requirements

- Treat the site-configuration backup as a secret: it contains database credentials and the encryption key needed to decrypt stored passwords.
- Never commit backups, manifests, credentials, or encryption keys to source control.
- Copy each completed backup set to encrypted storage outside the ERPNext host and restrict access to named recovery administrators.
- Keep at least one offline or immutable copy, and test recovery after framework upgrades or encryption-key changes.

## Backup procedure

Run the appropriate command from its bench root:

```powershell
docker compose exec -T bench bench --site erp.localhost backup --with-files --compress --verbose
```

```powershell
docker compose -f v15\docker-compose.yml exec -T bench bench --site erp15.localhost backup --with-files --compress --verbose
```

Generate and verify a SHA-256 manifest for the four generated files. Record the timestamp, operator, target encrypted storage, and verification outcome in the release record.

## Isolated restore procedure

1. Confirm the temporary site name does not exist and that it is not the default or production site.
2. Create the temporary site against the same major ERPNext/Frappe version and a separate database.
3. Restore the database with `bench --site <temporary-site> restore <database.sql.gz>` and include `--with-public-files` and `--with-private-files`.
4. Copy only the original `encryption_key` from the protected configuration backup into the temporary site's configuration. Do not replace the temporary site's database name or password.
5. Verify installed apps include `frappe`, `erpnext`, and `saudi_hr`.
6. Run:

```powershell
bench --site <temporary-site> execute saudi_hr.saudi_hr.demo_lifecycle.get_demo_acceptance_snapshot
bench --site <temporary-site> execute saudi_hr.saudi_hr.demo_lifecycle.run_logical_acceptance_suite
```

7. Accept the drill only when the result is 25/25 live checks, 38/38 logical tests, zero failures, and all archive checksums match.
8. Drop only the verified temporary site, using its exact name, after preserving the recovery record.

## Current go-live boundary

Backup recovery, scheduling, legal-catalog synchronization, provider file-exchange profiles, and role separation are ready. MFA enrollment, an approved outgoing email account, removal of intentional demo data, live government credentials/endpoints, real payroll-bank validation, and legal/HR approval remain production prerequisites.
