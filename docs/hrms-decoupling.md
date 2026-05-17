# HRMS Decoupling Notes

Saudi HR is designed to run without the HRMS app.

## Current Contract

| Item | Status |
|------|--------|
| Required Frappe app | `frappe` |
| Required ERP app | `erpnext` |
| Required HRMS app | Not required |
| Saudi shift management | Provided by Saudi HR |
| Saudi check-in and attendance records | Provided by Saudi HR |
| Mobile attendance flow | Provided by Saudi HR |
| Professional HR Hub | Provided by Saudi HR |

## What Was Decoupled

Saudi HR includes its own Saudi-specific operational layer for:

- Saudi shift types and assignments
- Saudi employee check-ins
- Saudi daily attendance
- Monthly attendance records
- Mobile attendance APIs and UI
- Professional HR Hub and Workspace links
- Employee Org Tree and attendance review pages

This avoids pulling HRMS into environments that only need ERPNext plus Saudi HR.

## Verification Commands

Check installed apps:

```bash
bench --site <your-site-name> list-apps
```

Expected core set:

```text
frappe
erpnext
saudi_hr
```

Run the dependency contract test:

```bash
bench --site <your-site-name> run-tests --app saudi_hr --module saudi_hr.saudi_hr.test_dependency_contract
```

Search for accidental runtime dependency references:

```bash
rg -n "required_apps|hrms|HRMS" apps/saudi_hr
```

References in changelog, documentation, and tests can exist to explain or verify the decoupling. Runtime install requirements should not include HRMS.

