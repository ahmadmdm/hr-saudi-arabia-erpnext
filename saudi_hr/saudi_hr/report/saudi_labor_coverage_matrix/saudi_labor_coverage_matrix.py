import frappe
from frappe import _

from saudi_hr import hooks as app_hooks


IMPLEMENTED = "Implemented / منفذ"
PARTIAL = "Partial / جزئي"
GAP = "Gap / فجوة"


def execute(filters=None):
	data = get_data(filters or {})
	return get_columns(), data, None, get_chart(data), get_report_summary(data)


def get_columns():
	return [
		{"fieldname": "coverage_area", "label": _("Coverage Area / مجال التغطية"), "fieldtype": "Data", "width": 150},
		{"fieldname": "legal_reference", "label": _("Legal Reference / المرجع النظامي"), "fieldtype": "Data", "width": 160},
		{"fieldname": "requirement", "label": _("Requirement / المتطلب"), "fieldtype": "Data", "width": 260},
		{"fieldname": "component_type", "label": _("Component Type / نوع المكوّن"), "fieldtype": "Data", "width": 150},
		{"fieldname": "component_name", "label": _("Component / المكوّن"), "fieldtype": "Data", "width": 220},
		{"fieldname": "implementation_status", "label": _("Implementation Status / حالة التنفيذ"), "fieldtype": "Data", "width": 145},
		{"fieldname": "evidence", "label": _("Evidence / الدليل"), "fieldtype": "Small Text", "width": 250},
		{"fieldname": "notes", "label": _("Notes / ملاحظات"), "fieldtype": "Small Text", "width": 340},
	]


def get_data(filters):
	rows = []
	for item in get_coverage_items():
		status = evaluate_item(item)
		row = {
			"coverage_area": item["coverage_area"],
			"legal_reference": item["legal_reference"],
			"requirement": item["requirement"],
			"component_type": item["component_type"],
			"component_name": item["component_name"],
			"implementation_status": status,
			"evidence": resolve_copy(item, status, "evidence"),
			"notes": resolve_copy(item, status, "notes"),
		}
		if filters.get("implementation_status") and row["implementation_status"] != filters["implementation_status"]:
			continue
		if filters.get("coverage_area") and row["coverage_area"] != filters["coverage_area"]:
			continue
		rows.append(row)

	rows.sort(key=lambda row: (status_rank(row["implementation_status"]), row["coverage_area"], row["legal_reference"]))
	return rows


def evaluate_item(item):
	if item.get("implementation_status"):
		return item["implementation_status"]

	validator_name = item.get("validator")
	if validator_name:
		validator = globals().get(validator_name)
		if validator:
			return validator(item)

	checks = item.get("checks", [])
	if not checks:
		return GAP

	if all(run_check(check) for check in checks):
		return item.get("implemented_status", IMPLEMENTED)

	return GAP


def resolve_copy(item, status, fieldname):
	status_key = status.lower().split(" /")[0].replace(" ", "_")
	return item.get(f"{status_key}_{fieldname}", item.get(fieldname, ""))


def run_check(check):
	kind = check["kind"]
	name = check.get("name")

	if kind == "doctype":
		return bool(frappe.db.exists("DocType", name))
	if kind == "report":
		return bool(frappe.db.exists("Report", name))
	if kind == "workflow":
		return bool(frappe.db.exists("Workflow", name))
	if kind == "notification":
		return bool(frappe.db.exists("Notification", name))
	if kind == "print_format":
		return bool(frappe.db.exists("Print Format", name))
	if kind == "scheduler":
		return scheduler_method_exists(name)

	return False


def scheduler_method_exists(method_path):
	for event_group in app_hooks.scheduler_events.values():
		if isinstance(event_group, list) and method_path in event_group:
			return True
	return False


def validate_annual_leave_coverage(item):
	if not all(run_check(check) for check in item.get("checks", [])):
		return GAP

	return IMPLEMENTED if frappe.db.exists("Leave Type", "Saudi Annual Leave / إجازة سنوية") else PARTIAL


def validate_special_leave_coverage(item):
	if not all(run_check(check) for check in item.get("checks", [])):
		return GAP

	options = frappe.db.get_value(
		"DocField",
		{"parent": "Special Leave", "fieldname": "leave_type"},
		"options",
	) or ""

	expected_options = (
		"Hajj Leave / إجازة حج (م.113 – 15 يوم)",
		"Bereavement Leave / إجازة وفاة (م.113 – 5 أيام)",
		"Marriage Leave / إجازة زواج (م.113 – 5 أيام)",
	)
	return IMPLEMENTED if all(option in options for option in expected_options) else PARTIAL


def validate_gosi_coverage(item):
	if not all(run_check(check) for check in item.get("checks", [])):
		return GAP

	if scheduler_method_exists("saudi_hr.saudi_hr.tasks.send_gosi_due_alerts") and frappe.db.exists(
		"Notification", "GOSI Status Update Alert"
	):
		return IMPLEMENTED

	notification = frappe.db.get_value(
		"Notification",
		"GOSI Status Update Alert",
		["event", "value_changed"],
		as_dict=True,
	) or {}

	if notification.get("event") == "Change" and notification.get("value_changed") == "payment_status":
		return PARTIAL

	return IMPLEMENTED


def status_rank(status):
	return {
		GAP: 0,
		PARTIAL: 1,
		IMPLEMENTED: 2,
	}.get(status, 99)


def get_chart(data):
	implemented_count = sum(1 for row in data if row["implementation_status"] == IMPLEMENTED)
	partial_count = sum(1 for row in data if row["implementation_status"] == PARTIAL)
	gap_count = sum(1 for row in data if row["implementation_status"] == GAP)

	return {
		"data": {
			"labels": [IMPLEMENTED, PARTIAL, GAP],
			"datasets": [{"name": _("Coverage Status / حالة التغطية"), "values": [implemented_count, partial_count, gap_count]}],
		},
		"type": "bar",
		"colors": ["#2F9E44", "#F08C00", "#C92A2A"],
	}


def get_report_summary(data):
	total = len(data)
	implemented_count = sum(1 for row in data if row["implementation_status"] == IMPLEMENTED)
	partial_count = sum(1 for row in data if row["implementation_status"] == PARTIAL)
	gap_count = sum(1 for row in data if row["implementation_status"] == GAP)

	return [
		{
			"label": _("Implemented / منفذ"),
			"value": implemented_count,
			"indicator": "Green",
			"datatype": "Int",
		},
		{
			"label": _("Partial / جزئي"),
			"value": partial_count,
			"indicator": "Orange",
			"datatype": "Int",
		},
		{
			"label": _("Gap / فجوة"),
			"value": gap_count,
			"indicator": "Red",
			"datatype": "Int",
		},
		{
			"label": _("Coverage Ratio / نسبة التغطية"),
			"value": f"{round((implemented_count / total) * 100, 1) if total else 0}%",
			"indicator": "Blue",
			"datatype": "Data",
		},
	]


def get_coverage_items():
	return [
		{
			"coverage_area": _("Employment / التوظيف"),
			"legal_reference": "Art. 37-46 / م.37-46",
			"requirement": _("Employment contracts and terms / عقود العمل وشروطها"),
			"component_type": "DocType",
			"component_name": "Saudi Employment Contract",
			"checks": [{"kind": "doctype", "name": "Saudi Employment Contract"}],
			"evidence": _("Contract DocType with probation, hours, and expiry tracking."),
			"notes": _("Core contract coverage is implemented in the employment lifecycle."),
		},
		{
			"coverage_area": _("Employment / التوظيف"),
			"legal_reference": "Art. 53 / م.53",
			"requirement": _("Probation controls and alerts / ضوابط وتنبيهات فترة التجربة"),
			"component_type": "Scheduler + DocType",
			"component_name": "Saudi Employment Contract + Probation End Alert",
			"checks": [
				{"kind": "doctype", "name": "Saudi Employment Contract"},
				{"kind": "scheduler", "name": "saudi_hr.saudi_hr.tasks.send_probation_end_alerts"},
			],
			"evidence": _("Probation validation in contract plus scheduled reminder before end date."),
			"notes": _("Covers probation cap, end-date calculation, and proactive reminders."),
		},
		{
			"coverage_area": _("Employment / التوظيف"),
			"legal_reference": "Art. 60-64 / م.60-64",
			"requirement": _("Training records and compliance / سجلات التدريب والامتثال"),
			"component_type": "DocType",
			"component_name": "Training Record",
			"checks": [{"kind": "doctype", "name": "Training Record"}],
			"evidence": _("Dedicated training register for mandatory and planned training."),
			"notes": _("Training compliance is modeled as a standalone HR record."),
		},
		{
			"coverage_area": _("Employment / التوظيف"),
			"legal_reference": "Art. 65-80 / م.65-80",
			"requirement": _("Disciplinary process and appeals / الإجراءات التأديبية والاعتراضات"),
			"component_type": "DocType + Workflow",
			"component_name": "Disciplinary Procedure + Disciplinary Appeal",
			"checks": [
				{"kind": "doctype", "name": "Disciplinary Procedure"},
				{"kind": "doctype", "name": "Disciplinary Appeal"},
			],
			"evidence": _("Progressive discipline record plus appeal tracking with committee notes."),
			"notes": _("Operational coverage exists for both disciplinary action and appeal review."),
		},
		{
			"coverage_area": _("Employment / التوظيف"),
			"legal_reference": "Art. 75-76 / م.75-76",
			"requirement": _("Termination notice approvals / موافقات إشعار إنهاء الخدمة"),
			"component_type": "DocType + Workflow",
			"component_name": "Termination Notice + Termination Approval Workflow",
			"checks": [
				{"kind": "doctype", "name": "Termination Notice"},
				{"kind": "workflow", "name": "Termination Approval Workflow"},
			],
			"evidence": _("Termination notice document with approval routing and notice-period handling."),
			"notes": _("Covers structured termination notice processing and approvals."),
		},
		{
			"coverage_area": _("Payroll & Benefits / الرواتب والمزايا"),
			"legal_reference": "Art. 84 / م.84",
			"requirement": _("End of service benefit / مكافأة نهاية الخدمة"),
			"component_type": "DocType + Report",
			"component_name": "End of Service Benefit + EOSB Calculation Report",
			"checks": [
				{"kind": "doctype", "name": "End of Service Benefit"},
				{"kind": "report", "name": "EOSB Calculation Report"},
			],
			"evidence": _("EOSB computation record with supporting calculation report."),
			"notes": _("Benefit calculation and analytical reporting are both implemented."),
		},
		{
			"coverage_area": _("Payroll & Benefits / الرواتب والمزايا"),
			"legal_reference": "Art. 90-102 / م.90-102",
			"requirement": _("Payroll, attendance, and official records / الرواتب والحضور والسجلات الرسمية"),
			"component_type": "DocType",
			"component_name": "Saudi Monthly Payroll + Monthly Attendance Record",
			"checks": [
				{"kind": "doctype", "name": "Saudi Monthly Payroll"},
				{"kind": "doctype", "name": "Monthly Attendance Record"},
			],
			"evidence": _("Monthly payroll batch plus official attendance register with daily details."),
			"notes": _("Core wage and attendance registers are present in the app."),
		},
		{
			"coverage_area": _("Payroll & Benefits / الرواتب والمزايا"),
			"legal_reference": "Art. 107 / م.107",
			"requirement": _("Overtime compensation and approval / العمل الإضافي والاعتماد"),
			"component_type": "DocType + Workflow",
			"component_name": "Overtime Request + Overtime Approval Workflow",
			"checks": [
				{"kind": "doctype", "name": "Overtime Request"},
				{"kind": "workflow", "name": "Overtime Approval Workflow"},
			],
			"evidence": _("Overtime request flow with approval routing and payroll integration."),
			"notes": _("Overtime is modeled as a controlled request with approval states."),
		},
		{
			"coverage_area": _("Leave Management / الإجازات"),
			"legal_reference": "Art. 109 / م.109",
			"requirement": _("Annual leave entitlement / استحقاق الإجازة السنوية"),
			"component_type": "DocType",
			"component_name": "Annual Leave Disbursement",
			"checks": [{"kind": "doctype", "name": "Annual Leave Disbursement"}],
			"validator": "validate_annual_leave_coverage",
			"evidence": _("Annual leave disbursement and entitlement tracking."),
			"notes": _("Annual leave coverage exists as an operational leave component."),
			"partial_evidence": _("Annual leave processing exists, but coverage also depends on the supported annual leave type being available on the site."),
			"partial_notes": _("The component is present, but the site is only partially compliant until a recognized annual leave type is installed."),
		},
		{
			"coverage_area": _("Leave Management / الإجازات"),
			"legal_reference": "Art. 113 / م.113",
			"requirement": _("Special leave events / الإجازات الخاصة"),
			"component_type": "DocType",
			"component_name": "Special Leave",
			"checks": [{"kind": "doctype", "name": "Special Leave"}],
			"validator": "validate_special_leave_coverage",
			"evidence": _("Special leave register for Hajj, bereavement, marriage, and similar events."),
			"notes": _("Special leave categories are represented in a dedicated record."),
			"partial_evidence": _("The Special Leave record exists, but the configured entitlement options do not fully match the expected statutory setup."),
			"partial_notes": _("Review the leave-type options and entitlement values before treating this article as fully implemented."),
		},
		{
			"coverage_area": _("Leave Management / الإجازات"),
			"legal_reference": "Art. 117 / م.117",
			"requirement": _("Sick leave thresholds and pay tiers / الإجازة المرضية وشرائح الأجر"),
			"component_type": "DocType + Scheduler",
			"component_name": "Saudi Sick Leave + Sick Leave Alerts",
			"checks": [
				{"kind": "doctype", "name": "Saudi Sick Leave"},
				{"kind": "scheduler", "name": "saudi_hr.saudi_hr.tasks.send_sick_leave_threshold_alerts"},
			],
			"evidence": _("Sick leave record plus threshold alerts and pay-rate handling."),
			"notes": _("Sick leave coverage includes operational tracking and alerts."),
		},
		{
			"coverage_area": _("Leave Management / الإجازات"),
			"legal_reference": "Art. 151 & 160 / م.151 و160",
			"requirement": _("Parental leave / إجازة الأمومة والأبوة"),
			"component_type": "DocType",
			"component_name": "Maternity Paternity Leave",
			"checks": [{"kind": "doctype", "name": "Maternity Paternity Leave"}],
			"evidence": _("Dedicated parental leave record for maternity and paternity cases."),
			"notes": _("Parental leave is modeled as a dedicated leave component."),
		},
		{
			"coverage_area": _("Compliance / الامتثال"),
			"legal_reference": "Art. 148-156 / م.148-156",
			"requirement": _("Work injuries and GOSI reporting / إصابات العمل والإبلاغ للتأمينات"),
			"component_type": "DocType",
			"component_name": "Work Injury",
			"checks": [{"kind": "doctype", "name": "Work Injury"}],
			"evidence": _("Work injury record with Form 25 and deadline controls."),
			"notes": _("Reactive injury compliance is implemented and linked to GOSI timing."),
		},
		{
			"coverage_area": _("Compliance / الامتثال"),
			"legal_reference": "Art. 218-221 / م.218-221",
			"requirement": _("Labor disputes and escalation / النزاعات العمالية والتصعيد"),
			"component_type": "DocType",
			"component_name": "Labor Dispute",
			"checks": [{"kind": "doctype", "name": "Labor Dispute"}],
			"evidence": _("Labor dispute register for ministry and court escalation tracking."),
			"notes": _("Dispute handling exists as a separate compliance record."),
		},
		{
			"coverage_area": _("Compliance / الامتثال"),
			"legal_reference": _("GOSI / التأمينات الاجتماعية"),
			"requirement": _("Monthly social insurance processing / المعالجة الشهرية للتأمينات"),
			"component_type": "DocType + Report + Notification + Scheduler",
			"component_name": "GOSI Contribution + GOSI Monthly Report + Status Alert",
			"checks": [
				{"kind": "doctype", "name": "GOSI Contribution"},
				{"kind": "report", "name": "GOSI Monthly Report"},
				{"kind": "notification", "name": "GOSI Status Update Alert"},
				{"kind": "scheduler", "name": "saudi_hr.saudi_hr.tasks.send_gosi_due_alerts"},
			],
			"validator": "validate_gosi_coverage",
			"evidence": _("Contribution record, monthly report, and due alert notification."),
			"notes": _("GOSI processing is implemented across transaction, reporting, and notification layers."),
			"partial_evidence": _("Core GOSI transaction and reporting exist, but the current due alert is still tied to payment-status changes rather than a monthly due cycle."),
			"partial_notes": _("Treat this area as partially implemented until the due alert models the intended monthly compliance reminder."),
		},
		{
			"coverage_area": _("Compliance / الامتثال"),
			"legal_reference": _("Nitaqat / نطاقات"),
			"requirement": _("Saudization ratio monitoring / مراقبة نسبة السعودة"),
			"component_type": "DocType + Report",
			"component_name": "Nitaqat Record + Nitaqat Compliance Report",
			"checks": [
				{"kind": "doctype", "name": "Nitaqat Record"},
				{"kind": "report", "name": "Nitaqat Compliance Report"},
			],
			"evidence": _("Saudization compliance record and analytical report."),
			"notes": _("Nitaqat monitoring is implemented for tracking and reporting."),
		},
		{
			"coverage_area": _("Compliance / الامتثال"),
			"legal_reference": _("WPS / حماية الأجور"),
			"requirement": _("Wage protection file generation / إنشاء ملف حماية الأجور"),
			"component_type": "Report",
			"component_name": "WPS Export Report",
			"checks": [{"kind": "report", "name": "WPS Export Report"}],
			"implemented_status": PARTIAL,
			"evidence": _("SIF export exists for WPS file generation."),
			"notes": _("Export is implemented, but rejection handling and full compliance lifecycle are not yet modeled."),
		},
		{
			"coverage_area": _("Compliance / الامتثال"),
			"legal_reference": _("Internal Compliance / الامتثال الداخلي"),
			"requirement": _("Policy and legal obligation mapping / ربط السياسات بالالتزامات النظامية"),
			"component_type": "DocType + Report",
			"component_name": "HR Policy Document + Legal Reference Matrix",
			"checks": [
				{"kind": "doctype", "name": "HR Policy Document"},
				{"kind": "doctype", "name": "Legal Reference Matrix"},
				{"kind": "report", "name": "Policy Compliance Register"},
			],
			"evidence": _("Policy register, legal reference matrix, and compliance register report."),
			"notes": _("Internal compliance layer is operational and tied to the Saudi HR workspace."),
		},
		{
			"coverage_area": _("Compliance / الامتثال"),
			"legal_reference": _("Executive Regulations / اللائحة التنفيذية"),
			"requirement": _("Labor inspection and violations / التفتيش العمالي والمخالفات"),
			"component_type": "DocType + Report",
			"component_name": "Labor Inspection + Labor Inspection Tracker",
			"checks": [
				{"kind": "doctype", "name": "Labor Inspection"},
				{"kind": "doctype", "name": "Labor Inspection Violation"},
				{"kind": "report", "name": "Labor Inspection Tracker"},
			],
			"evidence": _("Dedicated inspection register with violation rows, fines, and corrective follow-up reporting."),
			"notes": _("Inspection findings are now tracked operationally and linked to compliance actions for remediation."),
			"gap_evidence": _("No dedicated inspection, violation, fine, or corrective-order entity was found."),
			"gap_notes": _("This is the highest-value next compliance module to implement after the coverage matrix."),
		},
		{
			"coverage_area": _("Recommended Next Phase / المرحلة التالية المقترحة"),
			"legal_reference": _("Executive Regulations / اللائحة التنفيذية"),
			"requirement": _("Preventive occupational safety controls / ضوابط السلامة المهنية الوقائية"),
			"component_type": _("Proposed Module / مكوّن مقترح"),
			"component_name": _("Safety Inspection & Risk Controls"),
			"implementation_status": GAP,
			"evidence": _("Work injury tracking exists, but preventive safety inspections and risk controls are not modeled as standalone records."),
			"notes": _("Recommended to complement work injury compliance with preventive controls and inspection logs."),
		},
		{
			"coverage_area": _("Recommended Next Phase / المرحلة التالية المقترحة"),
			"legal_reference": _("Executive Regulations / اللائحة التنفيذية"),
			"requirement": _("Flexible, part-time, and remote work controls / ضوابط العمل المرن والجزئي وعن بعد"),
			"component_type": _("Proposed Module / مكوّن مقترح"),
			"component_name": _("Work Arrangement Controls"),
			"implementation_status": GAP,
			"evidence": _("No dedicated module was found for alternative work arrangements beyond the core employment contract."),
			"notes": _("Implement if the target regulatory scope includes these arrangements explicitly."),
		},
		{
			"coverage_area": _("Recommended Next Phase / المرحلة التالية المقترحة"),
			"legal_reference": _("Executive Regulations / اللائحة التنفيذية"),
			"requirement": _("Special employment category controls / ضوابط الفئات الخاصة من العمالة"),
			"component_type": _("Proposed Module / مكوّن مقترح"),
			"component_name": _("Women & Young Workers Controls"),
			"implementation_status": GAP,
			"evidence": _("No standalone control layer was found for special employment categories beyond leave and general contract data."),
			"notes": _("Implement only if required by the target interpretation of the executive regulations and annexes."),
		},
	]