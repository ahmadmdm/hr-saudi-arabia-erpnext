"""
Saudi Leave Balance Report — تقرير رصيد الإجازات السنوية
"""
import frappe
from frappe import _
from frappe.utils import date_diff, getdate, today

from saudi_hr.saudi_hr.utils import get_annual_leave_days_taken, get_annual_leave_entitlement


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"fieldname": "employee", "label": _("Employee / الموظف"), "fieldtype": "Link", "options": "Employee", "width": 130},
		{"fieldname": "employee_name", "label": _("Name / الاسم"), "fieldtype": "Data", "width": 180},
		{"fieldname": "department", "label": _("Department / القسم"), "fieldtype": "Link", "options": "Department", "width": 140},
		{"fieldname": "date_of_joining", "label": _("Joining Date / تاريخ الانضمام"), "fieldtype": "Date", "width": 130},
		{"fieldname": "years_of_service", "label": _("Years / السنوات"), "fieldtype": "Float", "precision": 2, "width": 100},
		{"fieldname": "entitlement", "label": _("Entitlement / الاستحقاق"), "fieldtype": "Int", "width": 120},
		{"fieldname": "leave_allocated", "label": _("Allocated / المُخصص"), "fieldtype": "Float", "precision": 1, "width": 120},
		{"fieldname": "leave_taken", "label": _("Taken / المأخوذ"), "fieldtype": "Float", "precision": 1, "width": 110},
		{"fieldname": "leave_balance", "label": _("Balance / الرصيد"), "fieldtype": "Float", "precision": 1, "width": 110},
	]


def get_data(filters):
	conditions = ["e.status = 'Active'"]
	values = {}

	if filters.get("company"):
		conditions.append("e.company = %(company)s")
		values["company"] = filters["company"]
	if filters.get("department"):
		conditions.append("e.department = %(department)s")
		values["department"] = filters["department"]
	if filters.get("employee"):
		conditions.append("e.name = %(employee)s")
		values["employee"] = filters["employee"]

	where = "WHERE " + " AND ".join(conditions)

	employees = frappe.db.sql(
		f"""
		SELECT e.name AS employee, e.employee_name, e.department,
			e.date_of_joining, e.company, e.nationality
		FROM `tabEmployee` e
		{where}
		ORDER BY e.employee_name
		""",
		values,
		as_dict=True,
	)

	result = []

	for emp in employees:
		years = date_diff(today(), emp.date_of_joining) / 365.0
		entitlement = get_annual_leave_entitlement(emp.employee)
		allocated = float(entitlement)
		taken = float(get_annual_leave_days_taken(emp.employee, getdate(today()).year))
		balance = allocated - taken

		result.append({
			"employee": emp.employee,
			"employee_name": emp.employee_name,
			"department": emp.department,
			"date_of_joining": emp.date_of_joining,
			"years_of_service": round(years, 2),
			"entitlement": entitlement,
			"leave_allocated": allocated,
			"leave_taken": taken,
			"leave_balance": balance,
		})

	return result
