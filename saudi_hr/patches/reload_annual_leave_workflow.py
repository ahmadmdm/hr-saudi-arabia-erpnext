import frappe


def execute():
	frappe.reload_doc("saudi_hr", "workflow", "annual_leave_approval_workflow")
