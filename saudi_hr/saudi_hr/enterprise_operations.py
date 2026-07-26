"""Enterprise operating services for Saudi HR.

The module deliberately separates file preparation from live government submission.
It never exposes integration credentials and records every confirmed export.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from datetime import date, datetime
from decimal import Decimal

import frappe
from frappe import _
from frappe.utils import cint, cstr, get_datetime, getdate, now_datetime, nowdate

from saudi_hr.saudi_hr.doctype.saudi_government_integration.saudi_government_integration import (
	FILE_MODE,
	safe_profile_dict,
)
from saudi_hr.saudi_hr.legal_rule_catalog import CATALOG_VERSION, LEGAL_RULES, SOURCE_DOCUMENT


ENTERPRISE_ROLES = {"System Manager", "HR Manager", "HR User", "Accounts Manager"}
PROVIDER_CODES = {
	"QIWA": "Qiwa / قوى",
	"GOSI": "GOSI / التأمينات",
	"MUDAD": "Mudad / مدد",
	"MUQEEM": "Muqeem / مقيم",
}
PROVIDER_META = {
	"Qiwa / قوى": {
		"code": "QIWA",
		"title_ar": "قوى",
		"purpose_ar": "العقود والموظفون وحالة العلاقة الوظيفية",
		"operation": "Contract Export / تصدير العقود",
		"format": "json",
	},
	"GOSI / التأمينات": {
		"code": "GOSI",
		"title_ar": "التأمينات",
		"purpose_ar": "الاشتراكات وأجور الاشتراك والمراجع المالية",
		"operation": "Contribution Export / تصدير الاشتراكات",
		"format": "csv",
	},
	"Mudad / مدد": {
		"code": "MUDAD",
		"title_ar": "مُدد",
		"purpose_ar": "ملف حماية الأجور ومطابقة صافي الرواتب",
		"operation": "WPS Export / تصدير حماية الأجور",
		"format": "csv",
	},
	"Muqeem / مقيم": {
		"code": "MUQEEM",
		"title_ar": "مقيم",
		"purpose_ar": "الإقامات ورخص العمل وحالات الانتهاء",
		"operation": "Permit Export / تصدير الرخص",
		"format": "json",
	},
}
CONFIRMATION_PHRASE = "تأكيد التصدير"
MAX_EXPORT_ROWS = 5000


def _require_logged_in():
	if frappe.session.user == "Guest":
		frappe.throw(_("Sign in to use Saudi HR services."), frappe.PermissionError)


def _require_enterprise_access():
	_require_logged_in()
	if frappe.session.user == "Administrator":
		return
	if not ENTERPRISE_ROLES.intersection(set(frappe.get_roles())):
		frappe.throw(_("You do not have permission to access the Saudi HR enterprise center."), frappe.PermissionError)


def _provider_label(provider):
	value = cstr(provider).strip()
	if value in PROVIDER_META:
		return value
	key = value.upper()
	if key in PROVIDER_CODES:
		return PROVIDER_CODES[key]
	frappe.throw(_("Unsupported government provider: {0}").format(value))


def _json_default(value):
	if isinstance(value, (date, datetime)):
		return value.isoformat()
	if isinstance(value, Decimal):
		return float(value)
	return cstr(value)


def _stable_json(value):
	return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=_json_default)


def _fingerprint(value):
	return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _mask(value, visible=4):
	value = cstr(value)
	if not value:
		return ""
	if len(value) <= visible:
		return "•" * len(value)
	return "•" * min(8, len(value) - visible) + value[-visible:]


def _date_filter(fieldname, from_date=None, to_date=None):
	filters = {}
	if from_date:
		filters[fieldname] = [">=", getdate(from_date)]
	if to_date:
		if fieldname in filters:
			filters[fieldname] = ["between", [getdate(from_date), getdate(to_date)]]
		else:
			filters[fieldname] = ["<=", getdate(to_date)]
	return filters


def _doctype_exists(doctype):
	return bool(frappe.db.exists("DocType", doctype))


def _count(doctype, filters=None):
	if not _doctype_exists(doctype):
		return 0
	return frappe.db.count(doctype, filters or {})


def _profile(profile_name):
	profile = frappe.get_doc("Saudi Government Integration", profile_name)
	frappe.has_permission(profile.doctype, "read", doc=profile, throw=True)
	if not profile.enabled:
		frappe.throw(_("The selected integration profile is disabled."))
	return profile


def sync_enterprise_defaults():
	"""Idempotently create safe file-exchange profiles for every company."""
	if not _doctype_exists("Saudi Government Integration"):
		return {"created": 0, "updated": 0, "skipped": 0}
	# Existing Single documents do not automatically receive defaults when fields
	# are added by a migration. Seed the mandatory brand values directly so the
	# next save cannot fail before a settings form has ever been opened.
	if _doctype_exists("Saudi HR Settings"):
		branding_defaults = {
			"organization_name_ar": "الموارد البشرية السعودية",
			"organization_name_en": "Saudi HR",
			"portal_welcome_ar": "كل ما تحتاجه للعمل والحقوق والطلبات في مسار واضح وآمن.",
			"brand_primary_color": "#0B5D4B",
			"enable_employee_self_service": 1,
			"enable_manager_self_service": 1,
		}
		settings_meta = frappe.get_meta("Saudi HR Settings")
		brand_was_uninitialized = frappe.db.get_single_value(
			"Saudi HR Settings", "organization_name_ar"
		) in (None, "")
		for fieldname, value in branding_defaults.items():
			current_value = frappe.db.get_single_value("Saudi HR Settings", fieldname)
			should_initialize = current_value in (None, "") or (
				brand_was_uninitialized
				and fieldname in {"enable_employee_self_service", "enable_manager_self_service"}
			)
			if settings_meta.has_field(fieldname) and should_initialize:
				frappe.db.set_single_value("Saudi HR Settings", fieldname, value)
	created = updated = 0
	for company in frappe.get_all("Company", pluck="name", order_by="creation asc"):
		for provider, meta in PROVIDER_META.items():
			name = frappe.db.get_value(
				"Saudi Government Integration",
				{"provider": provider, "company": company},
				"name",
			)
			values = {
				"integration_name": f"SAU-GOV-{meta['code']}-{company}",
				"provider": provider,
				"company": company,
				"enabled": 1,
				"mode": FILE_MODE,
				"api_version": "2026.1",
				"data_classification": "Confidential Payroll / رواتب سرية" if provider in {"GOSI / التأمينات", "Mudad / مدد"} else "Restricted HR Data / بيانات موارد بشرية مقيدة",
				"owner_user": "Administrator",
			}
			if name:
				doc = frappe.get_doc("Saudi Government Integration", name)
				# Never downgrade an explicitly configured API profile or overwrite credentials.
				for fieldname in ("api_version", "data_classification"):
					if not doc.get(fieldname):
						doc.set(fieldname, values[fieldname])
				doc.save(ignore_permissions=True)
				updated += 1
			else:
				frappe.get_doc({"doctype": "Saudi Government Integration", **values}).insert(ignore_permissions=True)
				created += 1
	return {"created": created, "updated": updated, "skipped": 0}


def _contract_payload(company, from_date=None, to_date=None):
	filters = {"company": company, "docstatus": ["<", 2]}
	if to_date:
		filters["start_date"] = ["<=", getdate(to_date)]
	rows = frappe.get_all(
		"Saudi Employment Contract",
		filters=filters,
		fields=[
			"name", "employee", "employee_name", "contract_type", "contract_status",
			"start_date", "end_date", "designation", "basic_salary", "total_salary",
			"nationality", "iqama_number", "probation_end_date",
		],
		order_by="start_date desc, name asc",
		limit_page_length=MAX_EXPORT_ROWS,
	)
	if from_date:
		start = getdate(from_date)
		rows = [row for row in rows if not row.end_date or getdate(row.end_date) >= start]
	records = []
	warnings = []
	for row in rows:
		records.append({
			"contract_reference": row.name,
			"employee_reference": row.employee,
			"employee_name": row.employee_name,
			"contract_type": row.contract_type,
			"status": row.contract_status,
			"start_date": row.start_date,
			"end_date": row.end_date,
			"job_title": row.designation,
			"basic_salary_sar": row.basic_salary,
			"total_salary_sar": row.total_salary,
			"nationality": row.nationality,
			"iqama_or_national_reference": row.iqama_number,
			"probation_end_date": row.probation_end_date,
		})
		if not row.start_date or not row.contract_type:
			warnings.append({"record": row.name, "message_ar": "العقد يحتاج تاريخ بداية ونوع عقد قبل الرفع."})
	return records, [], warnings, "SaudiHR-QIWA-2026.1"


def _gosi_payload(company, from_date=None, to_date=None):
	filters = {"company": company, "docstatus": ["<", 2]}
	rows = frappe.get_all(
		"GOSI Contribution",
		filters=filters,
		fields=[
			"name", "employee", "employee_name", "nationality", "month", "year",
			"contribution_base", "employee_contribution", "employer_contribution",
			"total_contribution", "payment_status", "reference_number",
		],
		order_by="year desc, month desc, employee asc",
		limit_page_length=MAX_EXPORT_ROWS,
	)
	if from_date or to_date:
		start = getdate(from_date) if from_date else None
		end = getdate(to_date) if to_date else None
		filtered = []
		for row in rows:
			try:
				period_date = getdate(f"{cint(row.year):04d}-{max(1, min(12, cint(row.month))):02d}-01")
			except Exception:
				period_date = None
			if period_date and ((not start or period_date >= start.replace(day=1)) and (not end or period_date <= end.replace(day=1))):
				filtered.append(row)
		rows = filtered
	records = [{
		"contribution_reference": row.name,
		"employee_reference": row.employee,
		"employee_name": row.employee_name,
		"nationality": row.nationality,
		"month": row.month,
		"year": row.year,
		"contribution_base_sar": row.contribution_base,
		"employee_contribution_sar": row.employee_contribution,
		"employer_contribution_sar": row.employer_contribution,
		"total_contribution_sar": row.total_contribution,
		"payment_status": row.payment_status,
		"payment_reference": row.reference_number,
	} for row in rows]
	warnings = [
		{"record": row.name, "message_ar": "مرجع السداد غير مسجل؛ راجعه قبل المطابقة النهائية."}
		for row in rows if row.payment_status and "Paid" in row.payment_status and not row.reference_number
	]
	return records, [], warnings, "SaudiHR-GOSI-2026.1"


def _employee_bank_fields():
	available = []
	for fieldname in ("iban", "bank_ac_no", "bank_account_no"):
		if frappe.db.has_column("Employee", fieldname):
			available.append(fieldname)
	return available


def _mudad_payload(company, from_date=None, to_date=None):
	filters = {"company": company, "docstatus": 1}
	filters.update(_date_filter("posting_date", from_date, to_date))
	payrolls = frappe.get_all(
		"Saudi Monthly Payroll",
		filters=filters,
		fields=["name", "period_label", "posting_date", "total_net_payable"],
		order_by="posting_date desc, name desc",
		limit_page_length=24,
	)
	bank_fields = _employee_bank_fields()
	records = []
	errors = []
	warnings = []
	for payroll in payrolls:
		items = frappe.get_all(
			"Saudi Monthly Payroll Employee",
			filters={"parent": payroll.name, "parenttype": "Saudi Monthly Payroll"},
			fields=["employee", "employee_name", "net_salary", "gosi_registration", "nationality"],
			order_by="idx asc",
			limit_page_length=MAX_EXPORT_ROWS,
		)
		for item in items:
			bank_data = frappe.db.get_value("Employee", item.employee, bank_fields, as_dict=True) if bank_fields else {}
			bank_data = bank_data or {}
			iban = next((bank_data.get(field) for field in bank_fields if bank_data.get(field)), "")
			record = {
				"payroll_reference": payroll.name,
				"pay_period": payroll.period_label,
				"posting_date": payroll.posting_date,
				"employee_reference": item.employee,
				"employee_name": item.employee_name,
				"nationality": item.nationality,
				"gosi_registration": item.gosi_registration,
				"iban": iban,
				"net_salary_sar": item.net_salary,
			}
			records.append(record)
			if not iban:
				errors.append({"record": f"{payroll.name}:{item.employee}", "message_ar": "رقم الآيبان مفقود ولا يمكن اعتماد ملف حماية الأجور."})
			if not item.net_salary or item.net_salary <= 0:
				warnings.append({"record": f"{payroll.name}:{item.employee}", "message_ar": "صافي الراتب صفر أو غير موجب؛ يلزم التحقق."})
	return records, errors, warnings, "SaudiHR-MUDAD-2026.1"


def _muqeem_payload(company, from_date=None, to_date=None):
	filters = {"company": company, "docstatus": ["<", 2]}
	if to_date:
		filters["iqama_expiry_date"] = ["<=", getdate(to_date)]
	rows = frappe.get_all(
		"Work Permit Iqama",
		filters=filters,
		fields=[
			"name", "employee", "employee_name", "nationality", "profession", "iqama_number",
			"iqama_issue_date", "iqama_expiry_date", "iqama_status", "work_permit_number",
			"work_permit_issue_date", "work_permit_expiry_date", "work_permit_status",
		],
		order_by="iqama_expiry_date asc, employee asc",
		limit_page_length=MAX_EXPORT_ROWS,
	)
	if from_date:
		start = getdate(from_date)
		rows = [row for row in rows if (row.iqama_expiry_date and getdate(row.iqama_expiry_date) >= start) or (row.work_permit_expiry_date and getdate(row.work_permit_expiry_date) >= start)]
	records = [{
		"authorization_reference": row.name,
		"employee_reference": row.employee,
		"employee_name": row.employee_name,
		"nationality": row.nationality,
		"profession": row.profession,
		"iqama_number": row.iqama_number,
		"iqama_issue_date": row.iqama_issue_date,
		"iqama_expiry_date": row.iqama_expiry_date,
		"iqama_status": row.iqama_status,
		"work_permit_number": row.work_permit_number,
		"work_permit_issue_date": row.work_permit_issue_date,
		"work_permit_expiry_date": row.work_permit_expiry_date,
		"work_permit_status": row.work_permit_status,
	} for row in rows]
	errors = []
	for row in rows:
		if not row.iqama_number:
			errors.append({"record": row.name, "message_ar": "رقم الإقامة مفقود."})
		if not row.work_permit_number:
			errors.append({"record": row.name, "message_ar": "رقم رخصة العمل مفقود."})
	return records, errors, [], "SaudiHR-MUQEEM-2026.1"


def _build_payload(profile, from_date=None, to_date=None):
	provider = profile.provider
	builders = {
		"Qiwa / قوى": _contract_payload,
		"GOSI / التأمينات": _gosi_payload,
		"Mudad / مدد": _mudad_payload,
		"Muqeem / مقيم": _muqeem_payload,
	}
	if provider not in builders:
		frappe.throw(_("No adapter is registered for provider {0}.").format(provider))
	records, errors, warnings, schema_version = builders[provider](profile.company, from_date, to_date)
	payload = {
		"schema_version": schema_version,
		"provider": provider,
		"company": profile.company,
		"period": {"from": cstr(from_date), "to": cstr(to_date)},
		"record_count": len(records),
		"records": records,
	}
	return payload, errors, warnings


def _safe_sample(provider, records):
	sample = []
	for source in records[:5]:
		row = dict(source)
		for fieldname in ("employee_reference", "iqama_or_national_reference", "iqama_number", "work_permit_number", "iban", "gosi_registration"):
			if row.get(fieldname):
				row[fieldname] = _mask(row[fieldname])
		sample.append(row)
	return sample


@frappe.whitelist()
def preview_provider_export(profile_name, from_date=None, to_date=None):
	"""Build a masked, side-effect-free provider preview."""
	_require_enterprise_access()
	profile = _profile(profile_name)
	payload, errors, warnings = _build_payload(profile, from_date, to_date)
	return {
		"profile": safe_profile_dict(profile),
		"provider": PROVIDER_META[profile.provider],
		"schema_version": payload["schema_version"],
		"record_count": payload["record_count"],
		"fingerprint": _fingerprint(payload),
		"sample": _safe_sample(profile.provider, payload["records"]),
		"errors": errors[:50],
		"warnings": warnings[:50],
		"can_confirm": not errors and bool(payload["record_count"]),
		"confirmation_phrase": CONFIRMATION_PHRASE,
		"notice_ar": "هذه معاينة محلية ولم تُرسل أي بيانات إلى الجهة الحكومية.",
	}


def _csv_content(records):
	if not records:
		return ""
	stream = io.StringIO(newline="")
	writer = csv.DictWriter(stream, fieldnames=list(records[0].keys()), extrasaction="ignore")
	writer.writeheader()
	for row in records:
		writer.writerow({key: _json_default(value) for key, value in row.items()})
	return "\ufeff" + stream.getvalue()


def _file_content(meta, payload):
	if meta["format"] == "csv":
		return _csv_content(payload["records"])
	return json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default)


@frappe.whitelist()
def confirm_provider_export(profile_name, confirmation_phrase, from_date=None, to_date=None):
	"""Create a private exchange file and an auditable transaction; never calls an external API."""
	_require_enterprise_access()
	if cstr(confirmation_phrase).strip() != CONFIRMATION_PHRASE:
		frappe.throw(_("Type the Arabic confirmation phrase exactly before creating the exchange file."))
	profile = _profile(profile_name)
	payload, errors, warnings = _build_payload(profile, from_date, to_date)
	if errors:
		frappe.throw(_("Resolve all blocking validation errors before confirming the export."))
	if not payload["records"]:
		frappe.throw(_("No eligible records were found for the selected period."))

	meta = PROVIDER_META[profile.provider]
	fingerprint = _fingerprint(payload)
	idempotency_key = f"{profile.name}:{meta['operation']}:{fingerprint}"
	existing = frappe.db.get_value(
		"Saudi Government Transaction",
		{"idempotency_key": idempotency_key, "status": "Succeeded / ناجح"},
		["name", "evidence_attachment"],
		as_dict=True,
	)
	if existing:
		return {
			"transaction": existing.name,
			"file_url": existing.evidence_attachment,
			"record_count": payload["record_count"],
			"fingerprint": fingerprint,
			"reused": True,
			"notice_ar": "أعيد استخدام ملف مطابق سبق إنشاؤه؛ لم تُكرر المعاملة.",
		}

	extension = meta["format"]
	file_name = f"saudi-hr-{meta['code'].lower()}-{getdate(nowdate()).isoformat()}-{fingerprint[:10]}.{extension}"
	private_file = frappe.get_doc({
		"doctype": "File",
		"file_name": file_name,
		"is_private": 1,
		"content": _file_content(meta, payload),
	}).insert(ignore_permissions=True)

	transaction = frappe.get_doc({
		"doctype": "Saudi Government Transaction",
		"integration_profile": profile.name,
		"provider": profile.provider,
		"company": profile.company,
		"operation": meta["operation"],
		"direction": "Outbound / صادر",
		"status": "Succeeded / ناجح",
		"dry_run": 0,
		"initiated_by": frappe.session.user,
		"started_on": now_datetime(),
		"completed_on": now_datetime(),
		"record_count": payload["record_count"],
		"payload_schema_version": payload["schema_version"],
		"request_fingerprint": fingerprint,
		"idempotency_key": idempotency_key,
		"payload_summary": _stable_json({
			"company": profile.company,
			"period": payload["period"],
			"record_count": payload["record_count"],
			"warning_count": len(warnings),
		}),
		"response_summary": _stable_json({
			"outcome": "private exchange file created",
			"external_submission": False,
			"file_name": file_name,
		}),
		"evidence_attachment": private_file.file_url,
	}).insert(ignore_permissions=True)
	private_file.db_set("attached_to_doctype", transaction.doctype)
	private_file.db_set("attached_to_name", transaction.name)
	profile.db_set("last_successful_sync_on", now_datetime(), update_modified=False)

	return {
		"transaction": transaction.name,
		"file_url": private_file.file_url,
		"record_count": payload["record_count"],
		"fingerprint": fingerprint,
		"reused": False,
		"warning_count": len(warnings),
		"notice_ar": "تم إنشاء ملف خاص وسجل تدقيق. لم تُرسل البيانات خارج النظام.",
	}


def _latest_transactions(company, limit=10):
	if not _doctype_exists("Saudi Government Transaction"):
		return []
	rows = frappe.get_all(
		"Saudi Government Transaction",
		filters={"company": company} if company else {},
		fields=["name", "provider", "operation", "status", "record_count", "started_on", "request_fingerprint", "evidence_attachment"],
		order_by="started_on desc",
		limit_page_length=limit,
	)
	for row in rows:
		row.request_fingerprint = cstr(row.request_fingerprint)[:12]
	return rows


def _legal_release_diff(company):
	if not company or not _doctype_exists("Legal Reference Matrix"):
		return {"version": CATALOG_VERSION, "current": 0, "missing": len(LEGAL_RULES), "outdated": 0, "extra": 0, "all_current": False}
	rows = frappe.get_all(
		"Legal Reference Matrix",
		filters={"company": company},
		fields=["rule_id", "source_document_version", "status"],
		limit_page_length=0,
	)
	stored = {row.rule_id: row for row in rows if row.rule_id}
	current_ids = {rule["rule_id"] for rule in LEGAL_RULES}
	missing = sorted(current_ids - set(stored))
	extra = sorted(set(stored) - current_ids)
	outdated = sorted(rule_id for rule_id in current_ids & set(stored) if stored[rule_id].source_document_version != CATALOG_VERSION)
	current = len(current_ids) - len(missing) - len(outdated)
	return {
		"version": CATALOG_VERSION,
		"source_document": SOURCE_DOCUMENT,
		"current": current,
		"missing": len(missing),
		"outdated": len(outdated),
		"extra": len(extra),
		"missing_ids": missing[:20],
		"outdated_ids": outdated[:20],
		"extra_ids": extra[:20],
		"all_current": not missing and not outdated,
	}


def _system_setting(fieldname, default=0):
	if not _doctype_exists("System Settings") or not frappe.get_meta("System Settings").has_field(fieldname):
		return default
	return frappe.db.get_single_value("System Settings", fieldname) or default


def _branding():
	defaults = {
		"organization_name_ar": "الموارد البشرية السعودية",
		"organization_name_en": "Saudi HR",
		"portal_welcome_ar": "كل ما تحتاجه للعمل والحقوق والطلبات في مسار واضح وآمن.",
		"brand_primary_color": "#0B5D4B",
		"support_email": "",
		"enable_employee_self_service": 1,
		"enable_manager_self_service": 1,
	}
	if not _doctype_exists("Saudi HR Settings"):
		return defaults
	settings_meta = frappe.get_meta("Saudi HR Settings")
	for fieldname in tuple(defaults):
		if settings_meta.has_field(fieldname):
			value = frappe.db.get_single_value("Saudi HR Settings", fieldname)
			if value not in (None, ""):
				defaults[fieldname] = value
	defaults["enable_employee_self_service"] = bool(cint(defaults["enable_employee_self_service"]))
	defaults["enable_manager_self_service"] = bool(cint(defaults["enable_manager_self_service"]))
	return defaults


def _readiness_checks(company, profiles):
	conf = frappe.get_conf()
	legal = _legal_release_diff(company)
	provider_codes = {profile["provider"] for profile in profiles if profile["enabled"]}
	checks = [
		{"id": "legal-catalog", "label_ar": "القواعد النظامية محدثة", "passed": legal["all_current"], "action_route": "/app/legal-reference-matrix"},
		{"id": "providers", "label_ar": "ملفات الجهات الأربع مهيأة", "passed": set(PROVIDER_META).issubset(provider_codes), "action_route": "/app/saudi-government-integration"},
		{"id": "mfa", "label_ar": "المصادقة الثنائية مفعلة", "passed": bool(cint(_system_setting("enable_two_factor_auth", 0))), "action_route": "/app/system-settings"},
		{"id": "scheduler", "label_ar": "المهام المجدولة غير متوقفة", "passed": not bool(cint(conf.get("pause_scheduler", 0))), "action_route": "/app/scheduled-job-type"},
		{"id": "email", "label_ar": "قناة بريد صادرة مفعلة", "passed": bool(_count("Email Account", {"enable_outgoing": 1})), "action_route": "/app/email-account"},
		{"id": "backup-encryption", "label_ar": "تشفير النسخ الاحتياطي مضبوط", "passed": bool(conf.get("backup_encryption_key") or conf.get("encryption_key")), "action_route": "/app/system-settings"},
		{"id": "role-separation", "label_ar": "أدوار الموارد البشرية والمالية موجودة", "passed": bool(_count("Has Role", {"role": "HR Manager"}) and _count("Has Role", {"role": "Accounts Manager"})), "action_route": "/app/user"},
		{"id": "demo-data", "label_ar": "لا توجد علامات بيانات تجريبية", "passed": not bool(_count("Saudi Sick Leave", {"medical_certificate_no": ["like", "DEMO-%"]})), "action_route": "/app/saudi-sick-leave"},
	]
	passed = sum(1 for item in checks if item["passed"])
	return {"score": round(passed / len(checks) * 100) if checks else 0, "passed": passed, "total": len(checks), "checks": checks}


def _capability_metrics(company):
	return {
		"employees": _count("Employee", {"company": company, "status": "Active"}) if company else _count("Employee", {"status": "Active"}),
		"open_overtime": _count("Overtime Request", {"company": company, "docstatus": 0}) if company else _count("Overtime Request", {"docstatus": 0}),
		"pending_policy_acknowledgements": _count("Policy Acknowledgement", {"company": company, "acknowledgement_status": "Pending / بانتظار الإقرار"}) if company else _count("Policy Acknowledgement", {"acknowledgement_status": "Pending / بانتظار الإقرار"}),
		"wps_follow_up": _count("WPS Submission", {"company": company, "status": ["in", ["Rejected / مرفوض", "Corrective Action Required / يحتاج تصحيح"]]}) if company else _count("WPS Submission", {"status": ["in", ["Rejected / مرفوض", "Corrective Action Required / يحتاج تصحيح"]]}),
		"expiring_permits": _count("Work Permit Iqama", {"company": company, "iqama_status": ["in", ["Expiring Soon / ينتهي قريباً", "Expired / منتهي"]]}) if company else _count("Work Permit Iqama", {"iqama_status": ["in", ["Expiring Soon / ينتهي قريباً", "Expired / منتهي"]]}),
		"open_compliance_actions": _count("HR Compliance Action Log", {"company": company, "completed_on": ["is", "not set"]}) if company else _count("HR Compliance Action Log", {"completed_on": ["is", "not set"]}),
	}


@frappe.whitelist()
def get_enterprise_operations_center(company=None):
	_require_enterprise_access()
	companies = frappe.get_all("Company", pluck="name", order_by="creation asc")
	company = company if company in companies else (companies[0] if companies else None)
	profiles = []
	if _doctype_exists("Saudi Government Integration"):
		profile_docs = frappe.get_all(
			"Saudi Government Integration",
			filters={"company": company} if company else {},
			fields=["name"],
			order_by="provider asc",
			limit_page_length=20,
		)
		profiles = [safe_profile_dict(frappe.get_doc("Saudi Government Integration", row.name)) for row in profile_docs]
	metrics = _capability_metrics(company)
	legal = _legal_release_diff(company)
	readiness = _readiness_checks(company, profiles)
	capabilities = [
		{"id": "government", "title_ar": "التكاملات الحكومية", "summary_ar": "معاينة وتصدير ومطابقة بآثار تدقيق واضحة.", "value": len([p for p in profiles if p["enabled"]]), "unit_ar": "جهات مهيأة", "tone": "green", "route": "/app/saudi-government-integration"},
		{"id": "self-service", "title_ar": "الخدمة الذاتية", "summary_ar": "طلبات الموظف وموافقات المدير من مسار عربي واحد.", "value": metrics["employees"], "unit_ar": "موظف نشط", "tone": "ink", "route": "/app/saudi-self-service"},
		{"id": "wages", "title_ar": "الأجور والمطابقة", "summary_ar": "ملفات حماية الأجور وأخطاء الرفض والمتابعة.", "value": metrics["wps_follow_up"], "unit_ar": "تحتاج متابعة", "tone": "clay" if metrics["wps_follow_up"] else "green", "route": "/app/wps-submission"},
		{"id": "documents", "title_ar": "الوثائق والإقرارات", "summary_ar": "نسخ السياسات وإقرارات إلكترونية قابلة للإثبات.", "value": metrics["pending_policy_acknowledgements"], "unit_ar": "إقرار معلق", "tone": "sand", "route": "/app/policy-acknowledgement"},
		{"id": "analytics", "title_ar": "التحليلات التنفيذية", "summary_ar": "مؤشرات العاملين والمخاطر والتشغيل حسب الشركة.", "value": metrics["open_compliance_actions"], "unit_ar": "إجراء مفتوح", "tone": "ink", "route": "/app/saudi-compliance-command-center"},
		{"id": "legal-guide", "title_ar": "الدليل النظامي", "summary_ar": "بحث عربي موثق بالمادة والصفحة وإجراء التشغيل.", "value": len(LEGAL_RULES), "unit_ar": "قاعدة موثقة", "tone": "green", "route": "/app/saudi-hr-legal-guide"},
		{"id": "legal-release", "title_ar": "التحديث التشريعي", "summary_ar": "فروقات الإصدار الفعال وتغطية قواعد الشركات.", "value": legal["current"], "unit_ar": f"من {len(LEGAL_RULES)} محدثة", "tone": "green" if legal["all_current"] else "clay", "route": "/app/legal-reference-matrix"},
		{"id": "enterprise-readiness", "title_ar": "جاهزية الإنتاج", "summary_ar": "الهوية والأمان والنسخ الاحتياطي والبيانات التجريبية.", "value": readiness["score"], "unit_ar": "% جاهزية", "tone": "green" if readiness["score"] >= 80 else "clay", "route": "/app/saudi-enterprise-center"},
	]
	return {
		"version": "2026.1-enterprise",
		"branding": _branding(),
		"company": company,
		"companies": companies,
		"metrics": metrics,
		"profiles": profiles,
		"providers": [dict(meta, provider=provider) for provider, meta in PROVIDER_META.items()],
		"capabilities": capabilities,
		"legal_release": legal,
		"readiness": readiness,
		"transactions": _latest_transactions(company),
		"external_submission_enabled": False,
		"external_submission_notice_ar": "التصدير الحالي ينشئ ملفات خاصة وسجلات تدقيق. الربط الفعلي يتطلب اعتماد الجهة ومفاتيحها الرسمية.",
	}


def _current_employee(allow_manager_preview=True):
	user = frappe.session.user
	fields = ["name", "employee_name", "company", "department", "designation", "image", "reports_to", "status", "user_id"]
	employee = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, fields, as_dict=True)
	mode = "personal"
	if not employee and allow_manager_preview and (user == "Administrator" or ENTERPRISE_ROLES.intersection(set(frappe.get_roles()))):
		preferred_employee = None
		if _doctype_exists("Policy Acknowledgement"):
			preferred_employee = frappe.db.get_value(
				"Policy Acknowledgement",
				{"acknowledgement_status": "Pending / بانتظار الإقرار"},
				"employee",
				order_by="due_date asc, creation asc",
			)
		rows = frappe.get_all("Employee", filters={"name": preferred_employee, "status": "Active"}, fields=fields, limit_page_length=1) if preferred_employee else []
		if not rows:
			rows = frappe.get_all("Employee", filters={"status": "Active"}, fields=fields, order_by="creation asc", limit_page_length=1)
		employee = rows[0] if rows else None
		mode = "manager_preview" if employee else "unlinked"
	return employee, mode


def _employee_rows(doctype, employee, fields, filters=None, order_by="modified desc", limit=8):
	if not employee or not _doctype_exists(doctype):
		return []
	query_filters = {"employee": employee}
	query_filters.update(filters or {})
	return frappe.get_all(doctype, filters=query_filters, fields=fields, order_by=order_by, limit_page_length=limit)


@frappe.whitelist()
def get_self_service_portal():
	_require_logged_in()
	employee, mode = _current_employee()
	if not employee:
		return {
			"mode": "unlinked",
			"employee": None,
			"message_ar": "لا يرتبط حسابك بسجل موظف نشط. اطلب من الموارد البشرية ربط حقل مستخدم النظام في ملف الموظف.",
			"support_route": "/app/employee",
		}

	emp = employee.name
	pending_ack = _employee_rows(
		"Policy Acknowledgement", emp,
		["name", "policy_document", "policy_title", "policy_version", "assigned_on", "due_date", "acknowledgement_status"],
		{"acknowledgement_status": "Pending / بانتظار الإقرار"},
		"due_date asc, assigned_on desc", 10,
	)
	leaves = _employee_rows("Saudi Annual Leave", emp, ["name", "leave_start_date", "leave_end_date", "total_leave_days", "status", "workflow_state", "docstatus"], {}, "modified desc", 5)
	sick = _employee_rows("Saudi Sick Leave", emp, ["name", "from_date", "to_date", "total_days", "docstatus"], {}, "modified desc", 5)
	overtime = _employee_rows("Overtime Request", emp, ["name", "date", "overtime_hours", "approval_status", "docstatus"], {}, "modified desc", 5)
	permits = _employee_rows("Work Permit Iqama", emp, ["name", "iqama_expiry_date", "iqama_status", "work_permit_expiry_date", "work_permit_status"], {}, "iqama_expiry_date asc", 2)
	payroll = _employee_rows("Saudi Monthly Payroll Employee", emp, ["parent", "employee_name", "gross_salary", "total_deductions", "net_salary", "modified"], {}, "modified desc", 1)
	team = frappe.get_all("Employee", filters={"reports_to": emp, "status": "Active"}, fields=["name", "employee_name", "designation", "department"], order_by="employee_name asc", limit_page_length=50)
	team_ids = [row.name for row in team]
	manager_pending = {
		"annual_leave": _count("Saudi Annual Leave", {"employee": ["in", team_ids], "workflow_state": "Pending Manager Approval"}) if team_ids and frappe.db.has_column("Saudi Annual Leave", "workflow_state") else 0,
		"sick_leave": _count("Saudi Sick Leave", {"employee": ["in", team_ids], "docstatus": 0}) if team_ids else 0,
		"overtime": _count("Overtime Request", {"employee": ["in", team_ids], "approval_status": "Pending / معلق"}) if team_ids else 0,
	}
	return {
		"mode": mode,
		"branding": _branding(),
		"employee": employee,
		"summary": {
			"pending_acknowledgements": len(pending_ack),
			"recent_leave_requests": len(leaves) + len(sick),
			"recent_overtime_requests": len(overtime),
			"team_members": len(team),
			"manager_pending": sum(manager_pending.values()),
		},
		"pending_acknowledgements": pending_ack,
		"annual_leave": leaves,
		"sick_leave": sick,
		"overtime": overtime,
		"permits": permits,
		"latest_payroll": payroll[0] if payroll else None,
		"team": team[:8],
		"manager_pending": manager_pending,
		"quick_actions": [
			{"id": "annual-leave", "label_ar": "طلب إجازة سنوية", "route": "/app/saudi-annual-leave/new"},
			{"id": "sick-leave", "label_ar": "تسجيل إجازة مرضية", "route": "/app/saudi-sick-leave/new"},
			{"id": "overtime", "label_ar": "طلب عمل إضافي", "route": "/app/overtime-request/new"},
			{"id": "attendance", "label_ar": "الحضور عبر الجوال", "route": "/mobile-attendance"},
			{"id": "grievance", "label_ar": "رفع تظلّم", "route": "/app/employee-grievance/new"},
		],
		"privacy_notice_ar": "تعرض هذه الصفحة سجل الموظف المرتبط بالمستخدم فقط. وضع المعاينة الإداري مميز بوضوح ولا يغيّر أي بيانات.",
	}


@frappe.whitelist()
def acknowledge_policy(acknowledgement_name, consent_text):
	_require_logged_in()
	consent = cstr(consent_text).strip()
	if consent != "أقر بالاطلاع والفهم":
		frappe.throw(_("Type the acknowledgement phrase exactly: أقر بالاطلاع والفهم"))
	doc = frappe.get_doc("Policy Acknowledgement", acknowledgement_name)
	employee, mode = _current_employee(allow_manager_preview=False)
	is_hr = frappe.session.user == "Administrator" or ENTERPRISE_ROLES.intersection(set(frappe.get_roles()))
	if not is_hr and (not employee or doc.employee != employee.name):
		frappe.throw(_("You can acknowledge only policies assigned to your employee record."), frappe.PermissionError)
	if doc.acknowledgement_status == "Acknowledged / تم الإقرار":
		return {"name": doc.name, "status": doc.acknowledgement_status, "fingerprint": doc.get("acknowledgement_fingerprint"), "reused": True}
	when = now_datetime()
	request_ip = cstr(getattr(frappe.local, "request_ip", ""))
	fingerprint = _fingerprint({
		"acknowledgement": doc.name,
		"policy": doc.policy_document,
		"version": doc.policy_version,
		"employee": doc.employee,
		"user": frappe.session.user,
		"consent": consent,
		"acknowledged_on": when,
	})
	doc.acknowledged_on = when
	doc.acknowledgement_channel = "Portal / البوابة"
	doc.acknowledgement_status = "Acknowledged / تم الإقرار"
	doc.acknowledgement_user = frappe.session.user
	doc.acknowledgement_consent_text = consent
	doc.acknowledgement_fingerprint = fingerprint
	doc.acknowledgement_ip = request_ip
	doc.flags.ignore_permissions = True
	doc.save()
	return {"name": doc.name, "status": doc.acknowledgement_status, "fingerprint": fingerprint, "acknowledged_on": when, "reused": False}


ARABIC_DIACRITICS = re.compile(r"[\u0617-\u061A\u064B-\u0652\u0670\u06D6-\u06ED]")


def normalize_arabic(value):
	value = ARABIC_DIACRITICS.sub("", cstr(value).lower())
	value = value.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ؤ": "و", "ئ": "ي", "ة": "ه"}))
	value = re.sub(r"[^\w\s-]", " ", value, flags=re.UNICODE)
	return " ".join(value.split())


def _rule_score(rule, query):
	terms = [term for term in normalize_arabic(query).split() if len(term) > 1]
	if not terms:
		return 1 if "Critical" in rule["risk_level"] else 0
	fields = {
		"topic": normalize_arabic(rule["reference_topic"]),
		"obligation": normalize_arabic(rule["obligation_summary"]),
		"control": normalize_arabic(rule["evidence_requirement"]),
		"id": normalize_arabic(rule["rule_id"]),
	}
	score = 0
	for term in terms:
		score += 8 if term in fields["topic"] else 0
		score += 4 if term in fields["obligation"] else 0
		score += 2 if term in fields["control"] else 0
		score += 10 if term in fields["id"] else 0
	return score


@frappe.whitelist()
def search_hr_guidance(query=None, limit=8):
	_require_logged_in()
	limit = max(1, min(20, cint(limit) or 8))
	ranked = sorted(
		[(rule, _rule_score(rule, query or "")) for rule in LEGAL_RULES],
		key=lambda item: (-item[1], item[0]["source_pdf_page"], item[0]["rule_id"]),
	)
	results = []
	for rule, score in ranked:
		if query and score <= 0:
			continue
		results.append({
			"rule_id": rule["rule_id"],
			"title_ar": rule["reference_topic"],
			"guidance_ar": rule["obligation_summary"],
			"control_ar": rule["evidence_requirement"],
			"risk": rule["risk_level"],
			"lifecycle": rule["lifecycle_stage"],
			"citation": {
				"source": SOURCE_DOCUMENT,
				"pdf_page": rule["source_pdf_page"],
				"printed_page": rule["source_printed_page"],
				"article_reference": rule["article_number"],
				"catalog_version": CATALOG_VERSION,
			},
			"score": score,
		})
		if len(results) >= limit:
			break
	return {
		"query": cstr(query),
		"normalized_query": normalize_arabic(query or ""),
		"count": len(results),
		"results": results,
		"catalog_version": CATALOG_VERSION,
		"source_document": SOURCE_DOCUMENT,
		"notice_ar": "إرشاد تشغيلي موثّق من الكتالوج النظامي، ولا يغني عن مراجعة قانونية للحالات الواقعية.",
	}


@frappe.whitelist()
def get_guided_draft(template_type, subject=None, company=None):
	_require_logged_in()
	company = cstr(company) or "[اسم المنشأة]"
	subject = cstr(subject) or "[الموظف/الموضوع]"
	templates = {
		"policy_acknowledgement": {
			"title_ar": "إقرار اطلاع على سياسة",
			"rule_query": "السجلات السياسات",
			"body_ar": f"أقر أنا {subject} بأنني اطلعت على السياسة المعتمدة لدى {company}، وفهمت نطاقها وإجراءاتها وتاريخ سريانها، واستلمت نسخة قابلة للرجوع إليها.",
		},
		"contract_review": {
			"title_ar": "محضر مراجعة عقد",
			"rule_query": "العقد التجربة",
			"body_ar": f"تمت مراجعة عقد {subject} لدى {company} من حيث نوع العقد، تاريخ البداية، فترة التجربة، الأجر، ساعات العمل، والتوثيق المطلوب. تُعالج أي فروقات قبل الاعتماد.",
		},
		"corrective_action": {
			"title_ar": "خطة إجراء تصحيحي",
			"rule_query": "ازالة المخالفة",
			"body_ar": f"الموضوع: {subject}. تحدد {company} مالك الإجراء وموعد الإغلاق والدليل المطلوب، وتتحقق من إزالة السبب الجذري وتوثيق النتيجة قبل إقفال الحالة.",
		},
		"final_settlement": {
			"title_ar": "قائمة تحقق التسوية النهائية",
			"rule_query": "التسوية الوثائق",
			"body_ar": f"تراجع {company} مستحقات {subject} والأجور والبدلات ورصيد الإجازات والعهد والوثائق، وتثبت تاريخ بدء المهلة وسبب الإنهاء وتاريخ الصرف والتسليم.",
		},
	}
	if template_type not in templates:
		frappe.throw(_("Unsupported guided draft type."))
	template = templates[template_type]
	guidance = search_hr_guidance(template["rule_query"], 3)
	return {
		"template_type": template_type,
		"title_ar": template["title_ar"],
		"body_ar": template["body_ar"],
		"citations": [result["citation"] for result in guidance["results"]],
		"notice_ar": guidance["notice_ar"],
	}


@frappe.whitelist()
def get_legal_release_diff(company=None):
	_require_enterprise_access()
	if not company:
		company = frappe.get_all("Company", pluck="name", order_by="creation asc", limit_page_length=1)
		company = company[0] if company else None
	return _legal_release_diff(company)
