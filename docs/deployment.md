# Deployment and Transfer Guide

Use this guide when moving Saudi HR to a new server, staging bench, or production environment.

## Recommended Flow

```bash
bench get-app --branch version-15 https://github.com/ahmadmdm/hr-saudi-arabia-erpnext.git
bench --site <your-site-name> install-app saudi_hr
bench --site <your-site-name> migrate
bench build --app saudi_hr
bench --site <your-site-name> clear-cache
bench restart
```

If the target site already has Saudi HR installed, replace `install-app` with:

```bash
bench --site <your-site-name> migrate
bench build --app saudi_hr
bench --site <your-site-name> clear-cache
bench restart
```

## Dependency Contract

Base runtime dependencies:

```bash
./env/bin/python -c "import openpyxl, openlocationcode; print('base dependencies ok')"
```

Optional voice dependencies:

```bash
./env/bin/python -c "import torch, torchaudio, speechbrain, faster_whisper; print('voice dependencies ok')"
```

The full dependency contract is documented in [DEPENDENCIES.md](../DEPENDENCIES.md).

## Production Checklist

| Area | Check |
|------|-------|
| Branch | Use `version-15` with ERPNext v15 |
| Apps | Confirm `frappe`, `erpnext`, and `saudi_hr` are installed |
| HRMS | HRMS is not required |
| Assets | Run `bench build --app saudi_hr` after updates |
| Workers | Restart services after `migrate` |
| Mobile attendance | Clear cache and reload service worker after deploy |
| Voice runtime | Install optional voice packages only when needed |

## Post-Transfer Validation

```bash
bench --site <your-site-name> list-apps
bench --site <your-site-name> run-tests --app saudi_hr --module saudi_hr.saudi_hr.test_dependency_contract
```

Open these pages after deployment:

| Experience | Route |
|------------|-------|
| Saudi HR Workspace | `/app/saudi-hr` |
| Professional HR Hub | `/app/professional-hr-hub` |
| Attendance Action Hub | `/app/attendance-action-hub` |
| Employee Org Tree | `/app/employee-org-tree` |
| Mobile Attendance | `/mobile-attendance` |

