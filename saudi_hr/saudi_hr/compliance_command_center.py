"""Permission-aware data service for the Saudi HR compliance command center."""

import frappe
from frappe import _
from frappe.utils import cint, getdate, today

from saudi_hr.saudi_hr.legal_rule_catalog import CATALOG_VERSION, LEGAL_RULES


def calculate_compliance_health(overdue_tasks=0, urgent_tasks=0, overdue_settlements=0, review_arrangements=0):
	"""Return a transparent 0-100 operating-health score, not a legal opinion."""
	penalty = (
		min(cint(overdue_tasks), 10) * 3
		+ min(cint(urgent_tasks), 10) * 2
		+ min(cint(overdue_settlements), 5) * 8
		+ min(cint(review_arrangements), 10) * 2
	)
	return max(0, 100 - penalty)


def _can_read(doctype):
	return bool(frappe.db.exists("DocType", doctype) and frappe.has_permission(doctype, "read"))


def _count(doctype, filters=None):
	if not _can_read(doctype):
		return 0
	rows = frappe.get_list(
		doctype,
		filters=filters or {},
		fields=["name"],
		limit_page_length=0,
	)
	return len(rows)


def _list(doctype, fields, filters=None, order_by=None, limit=8):
	if not _can_read(doctype):
		return []
	return frappe.get_list(
		doctype,
		filters=filters or {},
		fields=fields,
		order_by=order_by,
		limit_page_length=limit,
	)


def _task_actions():
	rows = _list(
		"Saudi Regulatory Task",
		["name", "task_title", "status", "priority", "due_date", "assigned_to", "article_reference"],
		{"status": ["not in", ["Completed / مكتمل", "Cancelled / ملغى"]]},
		"due_date asc, priority desc, modified desc",
		10,
	)
	actions = []
	for row in rows:
		due = getdate(row.due_date) if row.due_date else None
		is_overdue = bool(due and due < getdate(today()))
		actions.append(
			{
				"kind": "Regulatory Task",
				"name": row.name,
				"title": row.task_title,
				"meta": row.article_reference or _("Regulatory follow-up / متابعة تنظيمية"),
				"owner": row.assigned_to,
				"due_date": row.due_date,
				"status": _("Overdue / متأخر") if is_overdue else row.status,
				"severity": "critical" if is_overdue or row.priority == "Urgent / عاجل" else "warning",
				"route": f"/app/saudi-regulatory-task/{row.name}",
				"action_label": _("Review task / راجع المهمة"),
			}
		)
	return actions


def _settlement_actions():
	rows = _list(
		"Final Settlement SLA",
		["name", "employee_name", "settlement_due_date", "termination_initiated_by", "status"],
		{"status": "Overdue / متأخر"},
		"settlement_due_date asc",
		5,
	)
	return [
		{
			"kind": "Final Settlement",
			"name": row.name,
			"title": _("Complete settlement for {0} / أكمل تسوية {0}").format(row.employee_name or row.name),
			"meta": row.termination_initiated_by,
			"due_date": row.settlement_due_date,
			"status": row.status,
			"severity": "critical",
			"route": f"/app/final-settlement-sla/{row.name}",
			"action_label": _("Complete settlement / أكمل التسوية"),
		}
		for row in rows
	]


def _journeys(metrics):
	return [
		{
			"id": "onboarding",
			"title": _("Onboard an employee / هيّئ موظفاً جديداً"),
			"description": _("Create the employee file, contract, documents, policy acknowledgements, and first-day tasks. / أنشئ الملف والعقد والمستندات والإقرارات ومهام أول يوم."),
			"route": "/app/employee-onboarding/new",
			"tone": "primary",
		},
		{
			"id": "overtime",
			"title": _("Review overtime / راجع العمل الإضافي"),
			"description": _("Verify cash pay or 1.5x compensatory leave, consent, annual limit, and evidence. / تحقق من البدل أو التعويض بمعامل 1.5 والموافقة والحد السنوي والإثبات."),
			"route": "/app/overtime-request",
			"count": metrics["open_overtime"],
			"tone": "warning",
		},
		{
			"id": "maternity",
			"title": _("Manage maternity journey / أدر رحلة الأمومة"),
			"description": _("Plan the 12-week leave, nursing period, and child-care extensions. / خطط لإجازة 12 أسبوعاً وفترة الرضاعة وتمديدات رعاية الطفل."),
			"route": "/app/maternity-paternity-leave",
			"tone": "information",
		},
		{
			"id": "offboarding",
			"title": _("Close an employee file / أغلق ملف مغادرة"),
			"description": _("Track the 7/14-day settlement, document return, EOSB review, and closure evidence. / تابع مهلة 7 أو 14 يوماً ورد المستندات ومراجعة المكافأة وأدلة الإغلاق."),
			"route": "/app/final-settlement-sla",
			"count": metrics["overdue_settlements"],
			"tone": "critical" if metrics["overdue_settlements"] else "success",
		},
	]


@frappe.whitelist()
def get_compliance_command_center():
	if not ({"HR Manager", "HR User", "System Manager"} & set(frappe.get_roles())):
		frappe.throw(_("You do not have access to the Saudi HR command center. / لا تملك صلاحية الوصول إلى مركز قيادة الموارد البشرية السعودية."), frappe.PermissionError)

	current_day = today()
	metrics = {
		"legal_rules": len(LEGAL_RULES),
		"automated_rules": sum(1 for rule in LEGAL_RULES if rule["automation_level"] == "Automated / آلي"),
		"open_tasks": _count("Saudi Regulatory Task", {"status": ["not in", ["Completed / مكتمل", "Cancelled / ملغى"]]}),
		"overdue_tasks": _count("Saudi Regulatory Task", {"status": ["not in", ["Completed / مكتمل", "Cancelled / ملغى"]], "due_date": ["<", current_day]}),
		"urgent_tasks": _count("Saudi Regulatory Task", {"status": ["not in", ["Completed / مكتمل", "Cancelled / ملغى"]], "priority": "Urgent / عاجل"}),
		"overdue_settlements": _count("Final Settlement SLA", {"status": "Overdue / متأخر"}),
		"review_arrangements": _count("Work Arrangement Control", {"status": ["in", ["Needs Review / يحتاج مراجعة", "Needs Conversion / يحتاج تحويل"]]}),
		"open_overtime": _count("Overtime Request", {"approval_status": "Pending / معلق", "docstatus": 0}),
		"open_inspections": _count("Labor Inspection", {"status": ["not in", ["Closed / مغلق", "Cancelled / ملغى"]]}),
	}
	metrics["health_score"] = calculate_compliance_health(
		metrics["overdue_tasks"],
		metrics["urgent_tasks"],
		metrics["overdue_settlements"],
		metrics["review_arrangements"],
	)
	metrics["automation_percentage"] = round(metrics["automated_rules"] / metrics["legal_rules"] * 100) if metrics["legal_rules"] else 0

	actions = sorted(
		_task_actions() + _settlement_actions(),
		key=lambda item: (0 if item["severity"] == "critical" else 1, item.get("due_date") or "9999-12-31"),
	)[:12]

	return {
		"generated_on": frappe.utils.now_datetime(),
		"catalog_version": CATALOG_VERSION,
		"source_document": "اللائحة التنفيذية لنظام العمل وملحقاتها.pdf",
		"metrics": metrics,
		"actions": actions,
		"journeys": _journeys(metrics),
		"quick_actions": [
			{"label": _("Create regulatory task / أنشئ مهمة تنظيمية"), "route": "/app/saudi-regulatory-task/new"},
			{"label": _("Review legal matrix / راجع المصفوفة القانونية"), "route": "/app/legal-reference-matrix"},
			{"label": _("Open coverage report / افتح تقرير التغطية"), "route": "/app/query-report/Saudi Labor Coverage Matrix"},
			{"label": _("Open HR hub / افتح مركز الموارد البشرية"), "route": "/app/professional-hr-hub"},
		],
		"disclaimer": _("Operational compliance guidance based on the attached regulation; fact-specific cases require qualified legal review. / إرشاد امتثال تشغيلي مستند إلى اللائحة المرفقة؛ الحالات الواقعية الخاصة تتطلب مراجعة قانونية مؤهلة."),
	}
