from __future__ import annotations

import frappe


DASHBOARD_GROUPS = (
	(
		"Onboarding & Employment",
		(
			"Candidate Profile",
			"Employee Onboarding",
			"Saudi Employment Contract",
			"Work Permit Iqama",
			"Expat Work Authorization Control",
			"Medical Examination",
			"Policy Acknowledgement",
			"Special Employment Category Control",
			"Work Arrangement Control",
			"Saudi Employee Voice Profile",
		),
	),
	(
		"Time, Leave & Payroll",
		(
			"Saudi Employee Checkin",
			"Saudi Daily Attendance",
			"Monthly Attendance Record",
			"Saudi Shift Assignment",
			"Saudi Annual Leave",
			"Saudi Sick Leave",
			"Maternity Paternity Leave",
			"Special Leave",
			"Overtime Request",
			"Saudi Leave Policy Assignment",
			"Holiday Leave Overlap Rule",
			"Working Time Compliance Check",
		),
	),
	(
		"Payroll & Benefits",
		(
			"GOSI Contribution",
			"Employee Loan",
			"Salary Adjustment",
			"Annual Leave Disbursement",
		),
	),
	(
		"Performance & Development",
		(
			"Performance Review",
			"Training Record",
			"Training Agreement",
			"Promotion Transfer",
		),
	),
	(
		"Employee Relations & Legal",
		(
			"Employee Warning Notice",
			"Employee Grievance",
			"Absence Case",
			"Investigation Record",
			"Disciplinary Procedure",
			"Disciplinary Decision Log",
			"Disciplinary Appeal",
			"Labor Dispute",
			"Work Injury",
			"HR Compliance Action Log",
		),
	),
	(
		"Documents",
		(
			"Employee Document Custody Log",
			"Contract Portal Evidence",
		),
	),
	(
		"Separation & Offboarding",
		(
			"Termination Notice",
			"Exit Clearance",
			"Exit Interview",
			"Final Settlement SLA",
			"End of Service Benefit",
		),
	),
)

NON_STANDARD_FIELDNAMES = {
	"Candidate Profile": "linked_employee",
	"Investigation Record": "subject_employee",
}


def get_data(data=None):
	"""Extend Employee connections without exposing unavailable or unreadable DocTypes."""
	dashboard = frappe._dict(data or {})
	dashboard.fieldname = dashboard.get("fieldname") or "employee"
	dashboard.non_standard_fieldnames = dict(dashboard.get("non_standard_fieldnames") or {})

	transactions = []
	existing_items = set()
	for source_group in dashboard.get("transactions") or []:
		group = dict(source_group)
		group["items"] = list(group.get("items") or [])
		transactions.append(group)
		existing_items.update(group["items"])

	visibility = {}

	def can_show(doctype):
		if doctype not in visibility:
			visibility[doctype] = _can_read_doctype(doctype)
		return visibility[doctype]

	groups_by_label = {group.get("label"): group for group in transactions}
	for label, doctypes in DASHBOARD_GROUPS:
		items = [doctype for doctype in doctypes if doctype not in existing_items and can_show(doctype)]
		if not items:
			continue

		if label in groups_by_label:
			groups_by_label[label]["items"].extend(items)
		else:
			group = {"label": label, "items": items}
			transactions.append(group)
			groups_by_label[label] = group
		existing_items.update(items)

	for doctype, fieldname in NON_STANDARD_FIELDNAMES.items():
		if doctype in existing_items and can_show(doctype):
			dashboard.non_standard_fieldnames[doctype] = fieldname

	dashboard.transactions = transactions
	return dashboard


def _can_read_doctype(doctype):
	try:
		meta = frappe.get_meta(doctype)
	except frappe.DoesNotExistError:
		return False

	return not meta.istable and bool(frappe.has_permission(doctype, "read"))
