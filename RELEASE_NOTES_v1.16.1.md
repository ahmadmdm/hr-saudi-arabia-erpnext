# Saudi HR v1.16.1

## Highlights

- Added a lightweight voice-verification mode that validates a spoken challenge using the browser transcript without requiring AI voice-biometric packages.
- Kept full voice-biometric verification available as an optional runtime through the `voice-full` package extra.
- Added a new Professional HR Hub Desk page for teams that want a focused Saudi HR operating surface instead of the default ERPNext module layout.
- Improved the Saudi HR Workspace daily section so the most common HR actions appear first.
- Added focused test coverage for the lightweight voice runtime and revalidated the mobile attendance and runtime-permission flows.

## Voice Verification

- Added `Challenge Only / تحدي فقط` and `Full Biometric / بصمة كاملة` runtime modes in Saudi HR Settings.
- Challenge-only mode no longer requires employee voiceprint enrollment.
- Challenge-only mode accepts browser speech-to-text transcripts and checks them against the issued numeric challenge.
- Full biometric mode still supports speaker matching, anti-spoofing, Whisper transcription, and enrollment when optional dependencies are installed.
- Runtime status now reports mode, readiness, missing dependencies, enrollment support, browser transcript support, and voice language.

## Mobile Attendance

- Added Web Speech API transcript capture while recording a voice sample.
- Added Arabic and English messages for missing browser speech recognition support and missing transcripts.
- Updated mobile check-in so lightweight mode does not block first attendance because of missing voice enrollment.
- Exposed voice runtime mode, browser transcript support, enrollment support, and voice language to the mobile attendance UI.

## Professional HR Hub

- Added `/app/professional-hr-hub` as a curated Desk page.
- Added quick access to Mobile Attendance, Attendance Action Hub, Team Attendance Review, and Saudi HR Settings.
- Added a Fast Work Queue for attendance, annual leave, payroll, WPS, org tree, Iqama/work permits, and legal references.
- Added operating routes for employee lifecycle, time/leave/payroll, compliance, location and voice setup, reports, and system setup.
- Added responsive layout checks for the new page with no horizontal overflow or clipped controls in the tested Desk viewport.

## Workspace Improvements

- Added `Professional HR Hub` as a top shortcut in the Saudi HR Workspace.
- Reordered the daily section to start with Professional HR Hub, Mobile Attendance, Attendance Action Hub, Team Attendance Review, Saudi Monthly Payroll, and Employee Org Tree.
- Force-imported and cache-cleared the Workspace on the ERPNext site so the new shortcut and order appear in Desk.

## Packaging

- Kept base dependencies lightweight: `openpyxl` and `openlocationcode`.
- Moved heavy voice packages to optional `voice-full` dependencies: `numpy`, `torch`, `torchaudio`, `speechbrain`, and `faster-whisper`.
- Updated README dependency notes for lightweight and full voice runtime installation paths.

## Install and Migration Hardening

- Hardened install hooks so Department Approver permission sync skips absent Employee approver columns instead of failing during installation or migration.

## Tests and Verification

- Added `saudi_hr.saudi_hr.test_voice_lightweight` with 5 unit tests for challenge-only runtime readiness, Arabic digit transcript matching, missing transcript rejection, enrollment blocking, and full-biometric missing dependency reporting.
- Re-ran focused Saudi HR API and runtime-permission tests: 15 tests passed.
- Validated JavaScript syntax, Python compilation, JSON syntax, migration, asset build, cache clearing, and Desk visual navigation.