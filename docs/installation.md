# Installation Guide

This guide installs Saudi HR on a Frappe/ERPNext v15 bench.

## Requirements

| Component | Version |
|-----------|---------|
| Python | 3.10 or newer |
| Frappe Framework | v15 |
| ERPNext | v15 |
| MariaDB | 10.6 or newer |
| Node.js | 18 or newer |

Saudi HR does not require HRMS. The app runs on `frappe` and `erpnext`.

## Install

```bash
bench get-app --branch version-15 https://github.com/ahmadmdm/hr-saudi-arabia-erpnext.git
bench --site <your-site-name> install-app saudi_hr
bench --site <your-site-name> migrate
bench build --app saudi_hr
bench --site <your-site-name> clear-cache
```

## Verify Base Dependencies

```bash
./env/bin/python -c "import openpyxl, openlocationcode; print('base runtime dependencies ok')"
```

The base install intentionally keeps voice biometric AI packages optional. The lightweight mobile attendance challenge can run without the heavy voice stack.

## Optional Voice Runtime

Install full voice verification only when you need server-side biometric matching:

```bash
./env/bin/pip install "saudi_hr[voice-full]"
```

CPU-only environments with restricted package indexes can use:

```bash
./env/bin/pip install -r apps/saudi_hr/requirements-voice-cpu.txt
```

Then verify:

```bash
./env/bin/python -c "import torch, torchaudio, speechbrain, faster_whisper; print('voice dependencies ok')"
```

## Smoke Test

```bash
bench --site <your-site-name> run-tests --app saudi_hr --skip-test-records
```

For a faster post-install check, run the focused lifecycle and compliance modules:

```bash
bench --site <your-site-name> run-tests --app saudi_hr \
  --module saudi_hr.saudi_hr.test_employee_lifecycle_smoke \
  --module saudi_hr.saudi_hr.test_dependency_contract \
  --module saudi_hr.saudi_hr.test_professional_hr_catalog
```

