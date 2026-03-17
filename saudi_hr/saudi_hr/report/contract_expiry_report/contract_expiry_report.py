"""
Contract Expiry Report — تقرير انتهاء عقود العمل
"""
import frappe
from frappe import _
from frappe.utils import today, add_days


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"fieldname": "name", "label": _("Contract / العقد"), "fieldtype": "Link", "options": "Saudi Employment Contract", "width": 180},
		{"fieldname": "employee", "label": _("Employee / الموظف"), "fieldtype": "Link", "options": "Employee", "width": 130},
		{"fieldname": "employee_name", "label": _("Name / الاسم"), "fieldtype": "Data", "width": 180},
		{"fieldname": "contract_type", "label": _("Type / النوع"), "fieldtype": "Data", "width": 160},
		{"fieldname": "start_date", "label": _("Start / البدء"), "fieldtype": "Date", "width": 110},
		{"fieldname": "end_date", "label": _("End / الانتهاء"), "fieldtype": "Date", "width": 110},
		{"fieldname": "days_to_expiry", "label": _("Days Left / أيام متبقية"), "fieldtype": "Int", "width": 120},
		{"fieldname": "contract_status", "label": _("Status / الحالة"), "fieldtype": "Data", "width": 130},
		{"fieldname": "basic_salary", "label": _("Basic Salary / الراتب"), "fieldtype": "Currency", "width": 130},
	]


def get_data(filters):
	days = int(filters.get("alert_days") or 60)
	cutoff = add_days(today(), days)

	conditions = [
		"contract_type = 'محدد المدة / Fixed Term'",
		"end_date <= %(cutoff)s",
		"contract_status = 'Active / نشط'",
	]
	values = {"cutoff": cutoff, "today": today()}

	if filters.get("company"):
		conditions.append("company = %(company)s")
		values["company"] = filters["company"]

	where = "WHERE " + " AND ".join(conditions)

	rows = frappe.db.sql(
		f"""
		SELECT
			name, employee, employee_name, contract_type,
			start_date, end_date, contract_status, basic_salary
		FROM `tabSaudi Employment Contract`
		{where}
		ORDER BY end_date ASC
		""",
		values,
		as_dict=True,
	)

	from frappe.utils import date_diff, getdate
	for row in rows:
		row["days_to_expiry"] = date_diff(row["end_date"], today())

	return rows
