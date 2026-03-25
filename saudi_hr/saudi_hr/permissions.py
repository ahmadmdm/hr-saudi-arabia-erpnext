import frappe


ELEVATED_ROLES = {"HR Manager", "HR User", "System Manager", "Leave Approver"}


def _has_elevated_access(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return bool(ELEVATED_ROLES.intersection(set(frappe.get_roles(user))))


def _get_employee_for_user(user=None):
	user = user or frappe.session.user
	return frappe.db.get_value("Employee", {"user_id": user}, "name")


def _get_branch_for_user(user=None):
	user = user or frappe.session.user
	return frappe.db.get_value("Employee", {"user_id": user}, "branch")


def _employee_query(doctype, user=None):
	if _has_elevated_access(user):
		return ""

	employee = _get_employee_for_user(user)
	if not employee:
		return "1=0"

	return f"`tab{doctype}`.`employee` = {frappe.db.escape(employee)}"


def _branch_query(doctype, user=None):
	if _has_elevated_access(user):
		return ""

	branch = _get_branch_for_user(user)
	if not branch:
		return "1=0"

	return f"`tab{doctype}`.`branch` = {frappe.db.escape(branch)}"


def _employee_permission(doc, user=None):
	if _has_elevated_access(user):
		return True

	employee = _get_employee_for_user(user)
	return bool(employee and getattr(doc, "employee", None) == employee)


def _branch_permission(doc, user=None):
	if _has_elevated_access(user):
		return True

	branch = _get_branch_for_user(user)
	return bool(branch and getattr(doc, "branch", None) == branch)


def get_saudi_employee_checkin_query(user=None):
	return _employee_query("Saudi Employee Checkin", user)


def has_saudi_employee_checkin_permission(doc, user=None, permission_type=None):
	return _employee_permission(doc, user)


def get_saudi_daily_attendance_query(user=None):
	return _employee_query("Saudi Daily Attendance", user)


def has_saudi_daily_attendance_permission(doc, user=None, permission_type=None):
	return _employee_permission(doc, user)


def get_monthly_attendance_record_query(user=None):
	return _employee_query("Monthly Attendance Record", user)


def has_monthly_attendance_record_permission(doc, user=None, permission_type=None):
	return _employee_permission(doc, user)


def get_saudi_sick_leave_query(user=None):
	return _employee_query("Saudi Sick Leave", user)


def has_saudi_sick_leave_permission(doc, user=None, permission_type=None):
	return _employee_permission(doc, user)


def get_maternity_paternity_leave_query(user=None):
	return _employee_query("Maternity Paternity Leave", user)


def has_maternity_paternity_leave_permission(doc, user=None, permission_type=None):
	return _employee_permission(doc, user)


def get_special_leave_query(user=None):
	return _employee_query("Special Leave", user)


def has_special_leave_permission(doc, user=None, permission_type=None):
	return _employee_permission(doc, user)


def get_leave_application_query(user=None):
	return _employee_query("Leave Application", user)


def has_leave_application_permission(doc, user=None, permission_type=None):
	return _employee_permission(doc, user)


def get_attendance_location_query(user=None):
	return _branch_query("Attendance Location", user)


def has_attendance_location_permission(doc, user=None, permission_type=None):
	return _branch_permission(doc, user)