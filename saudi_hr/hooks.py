from . import __version__ as app_version


app_name = "saudi_hr"
app_title = "Saudi HR / نظام الموارد البشرية السعودي"
app_publisher = "IdeaOrbit"
app_description = "Saudi HR Management System per Saudi Labor Law (Royal Decree M/51)"
app_email = "info@ideaorbit.net"
app_license = "MIT"
required_apps = ["frappe/erpnext"]

# Apps Screen
add_to_apps_screen = [
	{
		"name": "saudi_hr",
		"logo": "/assets/saudi_hr/images/logo.svg",
		"title": "Saudi HR / الموارد البشرية",
		"route": "/app/saudi-hr",
	},
	{
		"name": "saudi_hr_mobile",
		"logo": "/assets/saudi_hr/images/logo.svg",
		"title": "حضور الموظفين / Attendance",
		"route": "/mobile-attendance",
	},
]

# ─── Web Routes ──────────────────────────────────────────────────────────────────
website_route_rules = [
	{"from_route": "/mobile-attendance", "to_route": "mobile-attendance"},
]

# ─── Scheduled Tasks ───────────────────────────────────────────────────────────
# Runs every day at midnight to send expiry alerts
scheduler_events = {
	"daily": [
		"saudi_hr.saudi_hr.tasks.send_iqama_expiry_alerts",
		"saudi_hr.saudi_hr.tasks.send_contract_expiry_alerts",
		"saudi_hr.saudi_hr.tasks.send_work_permit_expiry_alerts",
		"saudi_hr.saudi_hr.tasks.send_sick_leave_threshold_alerts",
		"saudi_hr.saudi_hr.tasks.send_probation_end_alerts",
	],
	"monthly": [
		"saudi_hr.saudi_hr.tasks.send_gosi_due_alerts",
	],
	"weekly": [
		"saudi_hr.saudi_hr.tasks.send_iqama_expiry_alerts",
	],
}

# ─── Document Events ────────────────────────────────────────────────────────────
doc_events = {
	"Overtime Request": {
		"on_submit": "saudi_hr.saudi_hr.doctype.overtime_request.overtime_request.create_overtime_journal_entry",
	},
	"GOSI Contribution": {
		"on_submit": "saudi_hr.saudi_hr.doctype.gosi_contribution.gosi_contribution.create_payroll_entries",
	},
	"Policy Acknowledgement": {
		"after_insert": "saudi_hr.saudi_hr.doctype.policy_acknowledgement.policy_acknowledgement.update_policy_acknowledgement_summary",
		"on_update": "saudi_hr.saudi_hr.doctype.policy_acknowledgement.policy_acknowledgement.update_policy_acknowledgement_summary",
		"on_trash": "saudi_hr.saudi_hr.doctype.policy_acknowledgement.policy_acknowledgement.update_policy_acknowledgement_summary",
	},
}

doctype_js = {
	"Employee": "public/js/employee.js",
}

# ─── Custom Fields on Employee ──────────────────────────────────────────────────
# Added via install.py to avoid modifying ERPNext/HRMS directly
# custom_fields = {}

# ─── Jinja ──────────────────────────────────────────────────────────────────────
jinja = {
	"methods": [
		"saudi_hr.saudi_hr.utils.get_eosb_amount",
		"saudi_hr.saudi_hr.utils.get_annual_leave_entitlement",
		"saudi_hr.saudi_hr.utils.get_gosi_rates",
	]
}

# ─── Override Whitelisted Methods ───────────────────────────────────────────────
override_whitelisted_methods = {}

permission_query_conditions = {
	"Saudi Employee Checkin": "saudi_hr.saudi_hr.permissions.get_saudi_employee_checkin_query",
	"Saudi Daily Attendance": "saudi_hr.saudi_hr.permissions.get_saudi_daily_attendance_query",
	"Monthly Attendance Record": "saudi_hr.saudi_hr.permissions.get_monthly_attendance_record_query",
	"Saudi Annual Leave": "saudi_hr.saudi_hr.permissions.get_saudi_annual_leave_query",
	"Saudi Sick Leave": "saudi_hr.saudi_hr.permissions.get_saudi_sick_leave_query",
	"Overtime Request": "saudi_hr.saudi_hr.permissions.get_overtime_request_query",
	"Salary Adjustment": "saudi_hr.saudi_hr.permissions.get_salary_adjustment_query",
	"Maternity Paternity Leave": "saudi_hr.saudi_hr.permissions.get_maternity_paternity_leave_query",
	"Special Leave": "saudi_hr.saudi_hr.permissions.get_special_leave_query",
	"Attendance Location": "saudi_hr.saudi_hr.permissions.get_attendance_location_query",
}

has_permission = {
	"Saudi Employee Checkin": "saudi_hr.saudi_hr.permissions.has_saudi_employee_checkin_permission",
	"Saudi Daily Attendance": "saudi_hr.saudi_hr.permissions.has_saudi_daily_attendance_permission",
	"Monthly Attendance Record": "saudi_hr.saudi_hr.permissions.has_monthly_attendance_record_permission",
	"Saudi Annual Leave": "saudi_hr.saudi_hr.permissions.has_saudi_annual_leave_permission",
	"Saudi Sick Leave": "saudi_hr.saudi_hr.permissions.has_saudi_sick_leave_permission",
	"Overtime Request": "saudi_hr.saudi_hr.permissions.has_overtime_request_permission",
	"Salary Adjustment": "saudi_hr.saudi_hr.permissions.has_salary_adjustment_permission",
	"Maternity Paternity Leave": "saudi_hr.saudi_hr.permissions.has_maternity_paternity_leave_permission",
	"Special Leave": "saudi_hr.saudi_hr.permissions.has_special_leave_permission",
	"Attendance Location": "saudi_hr.saudi_hr.permissions.has_attendance_location_permission",
}

after_install = "saudi_hr.install.after_install"

# ─── Fixtures ───────────────────────────────────────────────────────────────────
fixtures = [
	{
		"doctype": "Custom Field",
		"filters": [["module", "=", "Saudi HR"]],
	},
	{
		"doctype": "Property Setter",
		"filters": [["module", "=", "Saudi HR"]],
	},
	{
		"doctype": "Workflow",
		"filters": [["module", "=", "Saudi HR"]],
	},
	"Attendance Location",
]

# ─── Migration Hooks ───────────────────────────────────────────────────────
after_migrate = ["saudi_hr.install.after_migrate"]
