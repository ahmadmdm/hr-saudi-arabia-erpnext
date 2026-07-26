from __future__ import annotations

import frappe
from frappe.utils import add_days, getdate, now_datetime, nowdate


def _first_company() -> str:
	companies = frappe.get_all("Company", pluck="name", limit_page_length=1)
	if not companies:
		frappe.throw("Create a Company before seeding Saudi HR lifecycle demo data.")
	return companies[0]


def _first_gender() -> str:
	for candidate in ("Prefer not to say", "Male", "Female"):
		if frappe.db.exists("Gender", candidate):
			return candidate
	genders = frappe.get_all("Gender", pluck="name", limit_page_length=1)
	if genders:
		return genders[0]
	frappe.throw("Create at least one Gender before seeding Employee data.")


def _ensure_user(email: str, first_name: str, roles: tuple[str, ...]) -> str:
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name,
				"enabled": 1,
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	else:
		user = frappe.get_doc("User", email)
		user.enabled = 1
		user.save(ignore_permissions=True)

	for role in roles:
		user.add_roles(role)
	return email


def _ensure_employee(email: str, first_name: str, company: str, gender: str, reports_to: str | None = None) -> str:
	existing = frappe.db.get_value("Employee", {"user_id": email}, "name")
	if existing:
		employee = frappe.get_doc("Employee", existing)
	else:
		employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": first_name,
				"employee_name": first_name,
				"gender": gender,
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2026-01-01",
				"company": company,
				"user_id": email,
				"status": "Active",
			}
		)
	if reports_to:
		employee.reports_to = reports_to
	if frappe.get_meta("Employee").has_field("nationality") and frappe.db.exists("Country", "Saudi Arabia"):
		employee.nationality = "Saudi Arabia"
	employee.status = "Active"
	employee.save(ignore_permissions=True)
	return employee.name


def _ensure_contract(employee: str, company: str):
	existing = frappe.db.get_value(
		"Saudi Employment Contract",
		{"employee": employee, "company": company, "start_date": "2026-01-01", "docstatus": ("<", 2)},
		"name",
	)
	if existing:
		contract = frappe.get_doc("Saudi Employment Contract", existing)
		if not contract.nationality:
			contract.nationality = "Saudi / سعودي"
			contract.save(ignore_permissions=True)
		return existing

	return frappe.get_doc(
		{
			"doctype": "Saudi Employment Contract",
			"employee": employee,
			"company": company,
			"contract_type": "محدد المدة / Fixed Term",
			"contract_status": "Active / نشط",
			"start_date": "2026-01-01",
			"end_date": "2026-12-31",
			"nationality": "Saudi / سعودي",
			"basic_salary": 8000,
			"housing_allowance": 2000,
			"transport_allowance": 750,
			"other_allowances": 250,
		}
	).insert(ignore_permissions=True).name


def _ensure_warning(employee: str, company: str):
	existing = frappe.db.get_value(
		"Employee Warning Notice",
		{"employee": employee, "warning_date": "2026-02-10", "docstatus": ("<", 2)},
		"name",
	)
	if existing:
		return existing

	return frappe.get_doc(
		{
			"doctype": "Employee Warning Notice",
			"employee": employee,
			"company": company,
			"warning_date": "2026-02-10",
			"warning_level": "First Written Warning / إنذار كتابي أول",
			"issue_reason": "Repeated late arrival during probation review.",
			"corrective_action": "Manager follow-up and weekly attendance review.",
			"due_date": "2026-02-17",
		}
	).insert(ignore_permissions=True).name


def _ensure_leave(employee: str, company: str):
	existing = frappe.db.get_value(
		"Saudi Annual Leave",
		{"employee": employee, "leave_start_date": "2026-03-01", "docstatus": ("<", 2)},
		"name",
	)
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Saudi Annual Leave",
			"employee": employee,
			"company": company,
			"leave_start_date": "2026-03-01",
			"leave_end_date": "2026-03-03",
			"description": "Demo lifecycle annual leave request.",
		}
	)
	doc.flags.ignore_permissions = True
	doc.flags.ignore_mandatory = False
	from frappe.workflow.doctype.workflow_action import workflow_action

	original_enqueue = workflow_action.enqueue
	workflow_action.enqueue = lambda *args, **kwargs: None
	try:
		return doc.insert(ignore_permissions=True).name
	finally:
		workflow_action.enqueue = original_enqueue


def _ensure_payroll(employee: str, company: str):
	existing = frappe.db.get_value(
		"Saudi Monthly Payroll",
		{"company": company, "month": "March / مارس", "year": 2026, "notes": "Saudi HR demo lifecycle payroll run.", "docstatus": ("<", 2)},
		"name",
	)
	if existing:
		return existing

	payroll = frappe.get_doc(
		{
			"doctype": "Saudi Monthly Payroll",
			"company": company,
			"month": "March / مارس",
			"year": 2026,
			"posting_date": "2026-03-31",
			"employees": [
				{
					"employee": employee,
					"basic_salary": 8000,
					"housing_allowance": 2000,
					"transport_allowance": 750,
					"other_allowances": 250,
					"other_deductions": 150,
				}
			],
			"notes": "Saudi HR demo lifecycle payroll run.",
		}
	).insert(ignore_permissions=True)
	payroll.flags.ignore_permissions = True
	payroll.submit()
	return payroll.name


def _ensure_sick_leave_demo(employee: str, company: str):
	"""Create an approved 25-day balance and a 10-day mixed-tier preview."""
	approved_name = frappe.db.get_value(
		"Saudi Sick Leave",
		{"employee": employee, "from_date": "2026-04-01", "docstatus": ["<", 2]},
		"name",
	)
	if not approved_name:
		approved = frappe.get_doc(
			{
				"doctype": "Saudi Sick Leave",
				"employee": employee,
				"company": company,
				"from_date": "2026-04-01",
				"to_date": "2026-04-25",
				"medical_certificate_no": "DEMO-SICK-25",
				"hospital_name": "Demo Saudi Hospital / مستشفى سعودي تجريبي",
				"medical_certificate_attached": 1,
			}
		)
		approved.flags.ignore_permissions = True
		approved.insert(ignore_permissions=True)
		approved.submit()
		approved_name = approved.name

	mixed_name = frappe.db.get_value(
		"Saudi Sick Leave",
		{"employee": employee, "from_date": "2026-07-10", "docstatus": ["<", 2]},
		"name",
	)
	if not mixed_name:
		mixed_name = frappe.get_doc(
			{
				"doctype": "Saudi Sick Leave",
				"employee": employee,
				"company": company,
				"from_date": "2026-07-10",
				"to_date": "2026-07-19",
				"medical_certificate_no": "DEMO-SICK-MIXED-10",
				"hospital_name": "Demo Saudi Hospital / مستشفى سعودي تجريبي",
				"medical_certificate_attached": 1,
			}
		).insert(ignore_permissions=True).name

	return {"approved_25_days": approved_name, "mixed_tier_10_days": mixed_name}


def _ensure_compliance_demo(employee: str, departing_employee: str, company: str):
	"""Create idempotent normal, warning, and overdue examples for the command center."""
	from saudi_hr.saudi_hr.legal_rule_catalog import sync_legal_rule_catalog

	def keep_first_demo_draft(doctype, filters):
		"""Return the oldest matching demo draft and remove only its marked duplicates."""
		names = frappe.get_all(
			doctype,
			filters=filters,
			pluck="name",
			order_by="creation asc, name asc",
		)
		for duplicate in names[1:]:
			frappe.delete_doc(doctype, duplicate, ignore_permissions=True, force=True)
		return names[0] if names else None

	catalog_result = sync_legal_rule_catalog(company)

	arrangement_name = frappe.db.get_value(
		"Work Arrangement Control",
		{"employee": employee, "platform_reference": "DEMO-FLEX-120", "status": ["!=", "Cancelled / ملغى"]},
		"name",
	)
	if not arrangement_name:
		arrangement_name = frappe.get_doc(
			{
				"doctype": "Work Arrangement Control",
				"employee": employee,
				"company": company,
				"arrangement_type": "Flexible Work / العمل المرن",
				"status": "Active / نشط",
				"start_date": nowdate(),
				"end_date": add_days(nowdate(), 180),
				"monthly_hours": 120,
				"platform_reference": "DEMO-FLEX-120",
				"legal_reference": "SHR-REG-027",
				"notes": "حالة تجريبية سليمة: 120 ساعة، منها 25 ساعة فوق حد 95، ولم تبلغ نقطة نطاقات بعد.",
			}
		).insert(ignore_permissions=True).name

	boundary_arrangement_name = frappe.db.get_value(
		"Work Arrangement Control",
		{"employee": departing_employee, "platform_reference": "DEMO-FLEX-160", "status": ["!=", "Cancelled / ملغى"]},
		"name",
	)
	if not boundary_arrangement_name:
		boundary_arrangement_name = frappe.get_doc(
			{
				"doctype": "Work Arrangement Control",
				"employee": departing_employee,
				"company": company,
				"arrangement_type": "Flexible Work / العمل المرن",
				"status": "Active / نشط",
				"start_date": nowdate(),
				"end_date": add_days(nowdate(), 180),
				"monthly_hours": 160,
				"platform_reference": "DEMO-FLEX-160",
				"legal_reference": "SHR-REG-027-B",
				"notes": "حالة حدّية سليمة: 160 ساعة بالضبط، تستحق نقطة نطاقات واحدة ولا تتجاوز الحد الشهري.",
			}
		).insert(ignore_permissions=True).name

	overtime_name = keep_first_demo_draft(
		"Overtime Request",
		{"employee": employee, "written_consent_reference": "DEMO-CONSENT-1.5", "docstatus": ["<", 2]},
	)
	if not overtime_name:
		overtime_name = frappe.get_doc(
			{
				"doctype": "Overtime Request",
				"employee": employee,
				"company": company,
				"date": nowdate(),
				"normal_hours": 8,
				"overtime_hours": 2,
				"compensation_method": "Compensatory Leave / إجازة تعويضية",
				"written_consent_reference": "DEMO-CONSENT-1.5",
				"approval_status": "Pending / معلق",
			}
		).insert(ignore_permissions=True).name

	rejected_overtime_name = keep_first_demo_draft(
		"Overtime Request",
		{
			"employee": employee,
			"approval_status": "Rejected / مرفوض",
			"overtime_hours": 3,
			"compensation_method": "Cash Payment / بدل نقدي",
			"docstatus": ["<", 2],
		},
	)
	if not rejected_overtime_name:
		rejected_overtime_name = frappe.get_doc(
			{
				"doctype": "Overtime Request",
				"employee": employee,
				"company": company,
				"date": add_days(nowdate(), -1),
				"normal_hours": 8,
				"overtime_hours": 3,
				"compensation_method": "Cash Payment / بدل نقدي",
				"approval_status": "Rejected / مرفوض",
				"rejection_reason": "DEMO-REJECTED-BOUNDARY",
			}
		).insert(ignore_permissions=True).name
	elif not frappe.db.get_value("Overtime Request", rejected_overtime_name, "rejection_reason"):
		frappe.db.set_value("Overtime Request", rejected_overtime_name, "rejection_reason", "DEMO-REJECTED-BOUNDARY")

	settlement_name = frappe.db.get_value(
		"Final Settlement SLA",
		{"employee": departing_employee, "status": ["!=", "Cancelled / ملغى"]},
		"name",
	)
	if not settlement_name:
		settlement_name = frappe.get_doc(
			{
				"doctype": "Final Settlement SLA",
				"employee": departing_employee,
				"company": company,
				"last_working_day": add_days(nowdate(), -20),
				"termination_initiated_by": "Employee / الموظف",
				"status": "Open / مفتوح",
				"risk_level": "Critical / حرج",
				"unused_compensatory_leave_hours": 6,
				"actual_hourly_wage_for_leave": 31.25,
				"notes": "حالة تجريبية متأخرة لاختبار مهلة 14 يوماً ورد المستندات في التاريخ نفسه.",
			}
		).insert(ignore_permissions=True).name

	rule_name = frappe.db.get_value("Legal Reference Matrix", {"company": company, "rule_id": "SHR-REG-OT-LEAVE"}, "name")
	task_name = frappe.db.get_value("Saudi Regulatory Task", {"company": company, "source_reference": "DEMO-OVERDUE-EVIDENCE"}, "name")
	if not task_name:
		task_name = frappe.get_doc(
			{
				"doctype": "Saudi Regulatory Task",
				"task_title": "أرفق إثبات اتفاق الإجازة التعويضية التجريبي",
				"company": company,
				"status": "Open / مفتوح",
				"priority": "Urgent / عاجل",
				"task_date": add_days(nowdate(), -10),
				"due_date": add_days(nowdate(), -5),
				"assigned_to": "Administrator",
				"legal_reference_matrix": rule_name,
				"article_reference": "SHR-REG-OT-LEAVE · PDF p.17",
				"lifecycle_stage": "Time, Leave & Payroll",
				"task_category": "Document / مستند",
				"source_type": "Gap Assessment / تقييم فجوات",
				"source_reference": "DEMO-OVERDUE-EVIDENCE",
				"obligation_summary": "حالة متأخرة مقصودة لاختبار ترتيب المخاطر ورسالة الاسترداد في مركز القيادة.",
			}
		).insert(ignore_permissions=True).name

	return {
		"legal_catalog": catalog_result,
		"work_arrangement": arrangement_name,
		"boundary_work_arrangement": boundary_arrangement_name,
		"overtime_request": overtime_name,
		"rejected_overtime_request": rejected_overtime_name,
		"overdue_settlement": settlement_name,
		"overdue_regulatory_task": task_name,
	}


def _ensure_enterprise_demo(employee: str, company: str, payroll: str):
	"""Seed idempotent enterprise operations evidence without external submission."""
	from saudi_hr.saudi_hr.enterprise_operations import sync_enterprise_defaults

	integration_result = sync_enterprise_defaults()
	profiles = {
		row.provider: row.name
		for row in frappe.get_all(
			"Saudi Government Integration",
			filters={"company": company},
			fields=["name", "provider"],
		)
	}
	transaction_specs = [
		{
			"provider": "Qiwa / قوى",
			"operation": "Contract Export / تصدير العقود",
			"status": "Succeeded / ناجح",
			"record_count": 2,
			"idempotency_key": f"DEMO:QIWA:{company}:2026.1",
			"request_fingerprint": "demo-qiwa-a9f4138d9d6b",
			"response_summary": '{"external_submission": false, "outcome_ar": "ملف تبادل تجريبي جاهز"}',
		},
		{
			"provider": "GOSI / التأمينات",
			"operation": "Contribution Export / تصدير الاشتراكات",
			"status": "Partially Succeeded / ناجح جزئياً",
			"record_count": 1,
			"idempotency_key": f"DEMO:GOSI:{company}:2026.1",
			"request_fingerprint": "demo-gosi-f42286cd2137",
			"response_summary": '{"external_submission": false, "warning_ar": "مرجع السداد يحتاج مطابقة"}',
		},
		{
			"provider": "Mudad / مدد",
			"operation": "WPS Export / تصدير حماية الأجور",
			"status": "Failed / فشل",
			"record_count": 1,
			"idempotency_key": f"DEMO:MUDAD:{company}:2026.1",
			"request_fingerprint": "demo-mudad-10b75a2c6c81",
			"error_code": "DEMO-IBAN-MISSING",
			"error_detail": "حالة تجريبية: الآيبان مفقود ويجب تصحيحه قبل اعتماد ملف حماية الأجور.",
			"response_summary": '{"external_submission": false, "outcome_ar": "مرفوض قبل التصدير"}',
		},
	]
	transactions = []
	for spec in transaction_specs:
		profile = profiles.get(spec["provider"])
		if not profile:
			continue
		name = frappe.db.get_value("Saudi Government Transaction", {"idempotency_key": spec["idempotency_key"]}, "name")
		if not name:
			name = frappe.get_doc(
				{
					"doctype": "Saudi Government Transaction",
					"integration_profile": profile,
					"company": company,
					"direction": "Outbound / صادر",
					"initiated_by": "Administrator",
					"started_on": now_datetime(),
					"completed_on": now_datetime(),
					"payload_schema_version": "SaudiHR-DEMO-2026.1",
					"payload_summary": '{"demo": true, "external_submission": false}',
					**spec,
				}
			).insert(ignore_permissions=True).name
		transactions.append(name)

	policy_name = frappe.db.get_value(
		"HR Policy Document",
		{"company": company, "policy_title": "سياسة حماية البيانات والخصوصية التجريبية"},
		"name",
	)
	if not policy_name:
		policy_name = frappe.get_doc(
			{
				"doctype": "HR Policy Document",
				"policy_title": "سياسة حماية البيانات والخصوصية التجريبية",
				"policy_category": "Conduct / السلوك",
				"company": company,
				"status": "Active / سارية",
				"effective_date": nowdate(),
				"review_date": add_days(nowdate(), 365),
				"owner_user": "Administrator",
				"acknowledgement_required": 1,
				"policy_version": "2026.1-DEMO",
				"acknowledgement_due_days": 7,
				"legal_reference": "Demo enterprise evidence / إثبات مؤسسي تجريبي",
				"article_reference": "SHR-REG-017",
				"compliance_risk": "High / مرتفع",
				"summary": "حالة تجريبية لاختبار الإقرار الإلكتروني وبصمة الإثبات في بوابة الموظف.",
			}
		).insert(ignore_permissions=True).name

	acknowledgement_name = frappe.db.get_value(
		"Policy Acknowledgement",
		{"policy_document": policy_name, "policy_version": "2026.1-DEMO", "employee": employee},
		"name",
	)
	if not acknowledgement_name:
		acknowledgement_name = frappe.get_doc(
			{
				"doctype": "Policy Acknowledgement",
				"policy_document": policy_name,
				"employee": employee,
				"assigned_on": nowdate(),
				"due_date": add_days(nowdate(), 7),
				"acknowledgement_status": "Pending / بانتظار الإقرار",
			}
		).insert(ignore_permissions=True).name

	wps_name = frappe.db.get_value("WPS Submission", {"payroll_document": payroll}, "name")
	if not wps_name:
		wps_name = frappe.get_doc(
			{
				"doctype": "WPS Submission",
				"payroll_document": payroll,
				"status": "Rejected / مرفوض",
				"responsible_user": "Administrator",
				"submission_date": add_days(nowdate(), -2),
				"rejection_date": add_days(nowdate(), -1),
				"rejection_reason": "حالة تجريبية: رقم الآيبان مفقود في سجل الموظف.",
				"correction_due_date": add_days(nowdate(), 3),
				"notes": "DEMO-ENTERPRISE-WPS-REJECTION",
			}
		).insert(ignore_permissions=True).name

	return {
		"integration_sync": integration_result,
		"profiles": profiles,
		"transactions": transactions,
		"policy": policy_name,
		"policy_acknowledgement": acknowledgement_name,
		"wps_submission": wps_name,
	}


def seed_employee_lifecycle_demo():
	frappe.set_user("Administrator")
	company = _first_company()
	gender = _first_gender()
	manager_email = _ensure_user("saudi.lifecycle.manager@example.com", "Saudi Lifecycle Manager", ("Department Approver",))
	employee_email = _ensure_user("saudi.lifecycle.employee@example.com", "Saudi Lifecycle Employee", ("Employee Self Service",))
	departing_email = _ensure_user("saudi.lifecycle.departing@example.com", "Saudi Demo Departing Employee", ("Employee Self Service",))

	manager = _ensure_employee(manager_email, "Saudi Lifecycle Manager", company, gender)
	employee = _ensure_employee(employee_email, "Saudi Lifecycle Employee", company, gender, reports_to=manager)
	departing_employee = _ensure_employee(departing_email, "موظف تجريبي مغادر", company, gender, reports_to=manager)

	contract = _ensure_contract(employee, company)
	warning = _ensure_warning(employee, company)
	leave = _ensure_leave(employee, company)
	sick_leave = _ensure_sick_leave_demo(employee, company)
	payroll = _ensure_payroll(employee, company)
	compliance_demo = _ensure_compliance_demo(employee, departing_employee, company)
	enterprise_demo = _ensure_enterprise_demo(employee, company, payroll)

	settings = frappe.get_single("Saudi HR Settings")
	settings.mobile_attendance_base_url = frappe.utils.get_url().rstrip("/")
	settings.save(ignore_permissions=True)

	frappe.db.commit()
	return {
		"company": company,
		"manager": manager,
		"employee": employee,
		"contract": contract,
		"warning": warning,
		"leave": leave,
		"sick_leave": sick_leave,
		"payroll": payroll,
		"departing_employee": departing_employee,
		"compliance_demo": compliance_demo,
		"enterprise_demo": enterprise_demo,
		"seeded_on": nowdate(),
		"next_review_date": add_days(nowdate(), 30),
	}


def get_demo_acceptance_snapshot():
	"""Return an executable acceptance record for the seeded Saudi HR lifecycle.

	The checks deliberately cover statutory boundary values rather than only
	confirming that demo documents exist. This makes the seed useful for release
	verification on both supported ERPNext major versions.
	"""
	from saudi_hr.saudi_hr.compliance_command_center import get_compliance_command_center
	from saudi_hr.saudi_hr.enterprise_operations import get_enterprise_operations_center, get_self_service_portal, search_hr_guidance

	frappe.set_user("Administrator")
	company = _first_company()
	employee = frappe.db.get_value("Employee", {"user_id": "saudi.lifecycle.employee@example.com"}, "name")
	departing_employee = frappe.db.get_value(
		"Employee", {"user_id": "saudi.lifecycle.departing@example.com"}, "name"
	)

	def required_name(doctype, filters):
		name = frappe.db.get_value(doctype, filters, "name")
		if not name:
			frappe.throw(f"Missing seeded acceptance document: {doctype} {filters}")
		return name

	mixed_sick_leave = frappe.get_doc(
		"Saudi Sick Leave",
		required_name("Saudi Sick Leave", {"employee": employee, "medical_certificate_no": "DEMO-SICK-MIXED-10"}),
	)
	normal_flexible = frappe.get_doc(
		"Work Arrangement Control",
		required_name("Work Arrangement Control", {"company": company, "platform_reference": "DEMO-FLEX-120"}),
	)
	boundary_flexible = frappe.get_doc(
		"Work Arrangement Control",
		required_name("Work Arrangement Control", {"company": company, "platform_reference": "DEMO-FLEX-160"}),
	)
	compensatory_overtime = frappe.get_doc(
		"Overtime Request",
		required_name("Overtime Request", {"employee": employee, "written_consent_reference": "DEMO-CONSENT-1.5"}),
	)
	settlement = frappe.get_doc(
		"Final Settlement SLA",
		required_name("Final Settlement SLA", {"employee": departing_employee}),
	)
	command_center = get_compliance_command_center()
	enterprise_center = get_enterprise_operations_center(company)
	self_service = get_self_service_portal()
	legal_search = search_hr_guidance("إجازة مرضية")

	checks = []

	def check(code, description_ar, actual, expected, tolerance=None):
		if tolerance is None:
			passed = actual == expected
		else:
			passed = abs(float(actual or 0) - float(expected)) <= tolerance
		checks.append(
			{
				"code": code,
				"description_ar": description_ar,
				"actual": actual,
				"expected": expected,
				"passed": passed,
			}
		)

	check("LEGAL-CATALOG", "اكتمال كتالوج القواعد النظامية", frappe.db.count("Legal Reference Matrix", {"company": company}), 28)
	check("SICK-ROLLING-BEFORE", "احتساب 25 يوماً سابقة داخل سنة الاستحقاق المتحركة", mixed_sick_leave.sick_days_this_year_before, 25, 0.001)
	check("SICK-FULL-TIER", "تخصيص الأيام الخمسة المتبقية بأجر كامل", mixed_sick_leave.full_pay_days, 5, 0.001)
	check("SICK-PARTIAL-TIER", "تخصيص خمسة أيام تالية بأجر 75%", mixed_sick_leave.partial_pay_days, 5, 0.001)
	check("SICK-EFFECTIVE-RATE", "حساب نسبة الأجر الفعلية للحالة المختلطة", mixed_sick_leave.pay_rate, 87.5, 0.001)
	check("FLEX-95-THRESHOLD", "احتساب 25 ساعة فوق حد العمل المرن 95", normal_flexible.flexible_overtime_hours, 25, 0.001)
	check("FLEX-160-MAX", "قبول حد 160 ساعة دون تجاوزه", boundary_flexible.monthly_hours, 160, 0.001)
	check("FLEX-NITAQAT", "احتساب نقطة نطاقات واحدة عند 160 ساعة", boundary_flexible.flexible_nitaqat_credit, 1, 0.001)
	check("OT-COMP-FACTOR", "تحويل ساعتين إضافيتين إلى ثلاث ساعات إجازة", compensatory_overtime.compensatory_leave_hours, 3, 0.001)
	check("OT-COMP-DEADLINE", "تحديد مهلة استخدام الإجازة التعويضية بعد 60 يوماً", str(compensatory_overtime.compensatory_leave_use_by), str(add_days(getdate(compensatory_overtime.date), 60)))
	check("DEMO-OT-UNIQUE", "بقاء حالة الإجازة التعويضية التجريبية فريدة بعد تكرار البذرة", frappe.db.count("Overtime Request", {"employee": employee, "written_consent_reference": "DEMO-CONSENT-1.5", "docstatus": ["<", 2]}), 1)
	check("DEMO-REJECTED-UNIQUE", "بقاء حالة الرفض التجريبية فريدة بعد تكرار البذرة", frappe.db.count("Overtime Request", {"employee": employee, "rejection_reason": "DEMO-REJECTED-BOUNDARY", "docstatus": ["<", 2]}), 1)
	check("SETTLEMENT-14-DAYS", "تطبيق مهلة 14 يوماً عند إنهاء الموظف للعلاقة", str(settlement.settlement_due_date), str(add_days(getdate(settlement.last_working_day), 14)))
	check("DOCUMENT-SAME-SLA", "توحيد مهلة رد المستندات مع مهلة التسوية", str(settlement.document_return_due_date), str(settlement.settlement_due_date))
	check("COMP-LEAVE-PAYOUT", "تعويض 6 ساعات غير مستخدمة بسعر 31.25", settlement.compensatory_leave_payout_amount, 187.5, 0.001)
	check("COMMAND-CATALOG", "عرض 28 قاعدة في مركز الامتثال", command_center["metrics"]["legal_rules"], 28)
	check("COMMAND-AUTOMATION", "قياس أتمتة 27 قاعدة", command_center["metrics"]["automated_rules"], 27)
	check("COMMAND-RISK", "إظهار حالة تسوية ومهمة نظامية متأخرتين", [command_center["metrics"]["overdue_settlements"], command_center["metrics"]["overdue_tasks"]], [1, 1])
	check("ENTERPRISE-PROVIDERS", "تهيئة ملفات الجهات الحكومية الأربع", len(enterprise_center["profiles"]), 4)
	check("ENTERPRISE-TRANSACTIONS", "وجود معاملات تجريبية ناجحة وتحذيرية ومرفوضة", frappe.db.count("Saudi Government Transaction", {"idempotency_key": ["like", "DEMO:%"]}), 3)
	check("ENTERPRISE-WPS-REJECTION", "إظهار حالة حماية أجور تحتاج تصحيحاً", enterprise_center["metrics"]["wps_follow_up"], 1)
	check("ENTERPRISE-LEGAL-RELEASE", "تطابق إصدار القواعد المؤرخ مع سجلات الشركة", enterprise_center["legal_release"]["all_current"], True)
	check("SELF-SERVICE-PENDING-ACK", "إظهار إقرار السياسة التجريبي في بوابة الموظف", self_service["summary"]["pending_acknowledgements"], 1)
	check("LEGAL-ARABIC-SEARCH", "البحث العربي يعيد قواعد الإجازة المرضية", legal_search["count"] >= 2, True)
	check("LEGAL-CITATIONS", "كل نتيجة بحث نظامي تحمل مرجع الصفحة والمصدر", all(item["citation"]["pdf_page"] and item["citation"]["source"] for item in legal_search["results"]), True)

	return {
		"company": company,
		"catalog_version": command_center["catalog_version"],
		"checks": checks,
		"passed": sum(1 for item in checks if item["passed"]),
		"failed": sum(1 for item in checks if not item["passed"]),
		"all_passed": all(item["passed"] for item in checks),
	}


def run_logical_acceptance_suite():
	"""Run Saudi HR's critical logical tests inside an initialized Frappe site.

	This intentionally bypasses Frappe's global test-record generator: that
	generator traverses unrelated ERPNext doctypes before running this app's
	tests and can fail when optional core test fixtures are not installed.
	"""
	import io
	import unittest

	modules = (
		"saudi_hr.saudi_hr.doctype.overtime_request.test_overtime_request",
		"saudi_hr.saudi_hr.doctype.final_settlement_sla.test_final_settlement_sla",
		"saudi_hr.saudi_hr.doctype.work_arrangement_control.test_work_arrangement_control",
		"saudi_hr.saudi_hr.doctype.maternity_paternity_leave.test_maternity_paternity_leave",
		"saudi_hr.saudi_hr.doctype.saudi_sick_leave.test_saudi_sick_leave",
		"saudi_hr.saudi_hr.test_legal_rule_catalog",
		"saudi_hr.saudi_hr.test_compliance_command_center",
		"saudi_hr.saudi_hr.test_enterprise_operations",
	)
	suite = unittest.TestSuite()
	loader = unittest.TestLoader()
	for module in modules:
		suite.addTests(loader.loadTestsFromName(module))

	stream = io.StringIO()
	result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
	return {
		"modules": list(modules),
		"tests_run": result.testsRun,
		"failures": len(result.failures),
		"errors": len(result.errors),
		"skipped": len(result.skipped),
		"all_passed": result.wasSuccessful(),
		"details": stream.getvalue(),
	}
