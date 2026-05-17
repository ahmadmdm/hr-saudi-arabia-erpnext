# Saudi HR Dependency Contract

This app is designed to move between Frappe benches without requiring HRMS.

## Required Bench Apps

- `frappe` v15 or newer
- `erpnext` v15 or newer

`hrms` is intentionally not a required app. Saudi HR owns its Saudi shift, attendance, payroll, leave, WPS, GOSI, and compliance records directly.

## Base Python Dependencies

These are installed automatically from the package metadata during `bench get-app` / `bench install-app`:

- `openpyxl>=3.1.0`
- `openlocationcode>=1.0.1`

The same base dependencies are declared in:

- `setup.py`
- `pyproject.toml`
- `requirements.txt`

## Optional Voice Dependencies

Full biometric voice verification is optional. Install it only when the deployment needs local speech and speaker models:

```bash
./env/bin/pip install -e "apps/saudi_hr[voice-full]"
```

For CPU-only servers or restricted package indexes, use:

```bash
./env/bin/pip install -r apps/saudi_hr/requirements-voice-cpu.txt
```

Optional voice packages:

- `numpy<2`
- `torch`
- `torchaudio`
- `speechbrain`
- `faster-whisper`

## Transfer Checklist

```bash
bench get-app <saudi-hr-repo-url>
bench --site <site> install-app saudi_hr
bench --site <site> migrate
bench build --app saudi_hr
bench --site <site> clear-cache
```

Verify the installed app set:

```bash
bench --site <site> list-apps
```

Expected app list:

```text
frappe
erpnext
saudi_hr
```

Verify base dependencies:

```bash
./env/bin/python -c "import openpyxl, openlocationcode; print('base dependencies ok')"
```

Verify optional voice dependencies only after installing the voice extra:

```bash
./env/bin/python -c "import torch, torchaudio, speechbrain, faster_whisper; print('voice dependencies ok')"
```

Run the app tests:

```bash
bench --site <site> run-tests --app saudi_hr
```

## Shipped App Artifacts

The app ships its standard DocTypes, reports, pages, workspaces, dashboard charts, number cards, print formats, workflows, notifications, patches, and public assets through the app files and migrations.

Fixtures are reserved for site-level customizations filtered to the Saudi HR module, plus Attendance Location records when exported from a configured source site.
