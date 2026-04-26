import frappe
from frappe import _
from frappe.utils import getdate, nowdate


OVERDUE_STATUSES = {"Rejected / مرفوض", "Corrective Action Required / يحتاج تصحيح"}


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"fieldname": "wps_submission", "label": _("WPS Submission / متابعة حماية الأجور"), "fieldtype": "Link", "options": "WPS Submission", "width": 180},
		{"fieldname": "payroll_document", "label": _("Saudi Monthly Payroll / المسير الشهري"), "fieldtype": "Link", "options": "Saudi Monthly Payroll", "width": 170},
		{"fieldname": "company", "label": _("Company / الشركة"), "fieldtype": "Link", "options": "Company", "width": 160},
		{"fieldname": "status", "label": _("Status / الحالة"), "fieldtype": "Data", "width": 180},
		{"fieldname": "submission_date", "label": _("Submission Date / تاريخ الإرسال"), "fieldtype": "Date", "width": 120},
		{"fieldname": "correction_due_date", "label": _("Correction Due Date / موعد التصحيح"), "fieldtype": "Date", "width": 130},
		{"fieldname": "responsible_user", "label": _("Responsible User / المسؤول"), "fieldtype": "Link", "options": "User", "width": 150},
		{"fieldname": "accepted_on", "label": _("Accepted On / تاريخ القبول"), "fieldtype": "Date", "width": 120},
		{"fieldname": "corrective_action_log", "label": _("Compliance Action / إجراء الامتثال"), "fieldtype": "Link", "options": "HR Compliance Action Log", "width": 170},
		{"fieldname": "overdue_status", "label": _("Correction Status / حالة التصحيح"), "fieldtype": "Data", "width": 160},
	]


def get_data(filters):
	conditions = []
	values = {}

	if filters.get("company"):
		conditions.append("company = %(company)s")
		values["company"] = filters["company"]
	if filters.get("status"):
		conditions.append("status = %(status)s")
		values["status"] = filters["status"]
	if filters.get("responsible_user"):
		conditions.append("responsible_user = %(responsible_user)s")
		values["responsible_user"] = filters["responsible_user"]

	where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
	rows = frappe.db.sql(
		f"""
		SELECT
			name AS wps_submission,
			payroll_document,
			company,
			status,
			submission_date,
			correction_due_date,
			responsible_user,
			accepted_on,
			corrective_action_log
		FROM `tabWPS Submission`
		{where_clause}
		ORDER BY modified DESC
		""",
		values,
		as_dict=True,
	)

	today = getdate(nowdate())
	for row in rows:
		overdue = row.get("correction_due_date") and getdate(row["correction_due_date"]) < today and row.get("status") in OVERDUE_STATUSES
		if overdue:
			row["overdue_status"] = _("Overdue / متأخر")
		elif row.get("status") in OVERDUE_STATUSES:
			row["overdue_status"] = _("Open Correction / تصحيح مفتوح")
		else:
			row["overdue_status"] = _("Normal / طبيعي")

	return rows