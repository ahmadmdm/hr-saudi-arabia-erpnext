"""
Saudi Leave Balance Report — تقرير رصيد الإجازات السنوية
"""
import frappe
from frappe import _
from frappe.utils import getdate, today

from saudi_hr.saudi_hr.utils import get_annual_leave_balance


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
		{"fieldname": "leave_policy", "label": _("Leave Policy / سياسة الإجازة"), "fieldtype": "Link", "options": "Saudi Leave Policy", "width": 170},
		{"fieldname": "policy_name", "label": _("Policy Name / اسم السياسة"), "fieldtype": "Data", "width": 190},
		{"fieldname": "policy_source", "label": _("Policy Source / مصدر السياسة"), "fieldtype": "Data", "width": 170},
		{"fieldname": "policy_assignment", "label": _("Policy Assignment / تعيين السياسة"), "fieldtype": "Link", "options": "Saudi Leave Policy Assignment", "width": 180},
	]


def get_data(filters):
	conditions = ["e.status = 'Active'"]
	as_of_date = getdate(filters.get("as_of_date") or today())
	values = {"as_of_date": as_of_date}
	conditions.append("e.date_of_joining <= %(as_of_date)s")

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
			e.date_of_joining, e.company
		FROM `tabEmployee` e
		{where}
		ORDER BY e.employee_name
		""",
		values,
		as_dict=True,
	)

	result = []

	for emp in employees:
		leave_balance = get_annual_leave_balance(emp.employee, as_of_date)
		entitlement = leave_balance["entitled"]
		allocated = float(entitlement)
		taken = float(leave_balance["taken"])
		balance = float(leave_balance["balance"])

		result.append({
			"employee": emp.employee,
			"employee_name": emp.employee_name,
			"department": emp.department,
			"date_of_joining": emp.date_of_joining,
			"years_of_service": leave_balance["years_of_service"],
			"entitlement": entitlement,
			"leave_allocated": allocated,
			"leave_taken": taken,
			"leave_balance": balance,
			"leave_policy": leave_balance.get("policy"),
			"policy_name": leave_balance.get("policy_name"),
			"policy_source": leave_balance.get("source_type"),
			"policy_assignment": leave_balance.get("assignment"),
		})

	return result
