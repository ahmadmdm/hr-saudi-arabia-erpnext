app_name = "saudi_hr"
app_title = "Saudi HR / نظام الموارد البشرية السعودي"
app_publisher = "IdeaOrbit"
app_description = "Saudi HR Management System per Saudi Labor Law (Royal Decree M/51)"
app_email = "info@ideaorbit.net"
app_license = "MIT"
app_version = "1.3.0"
required_apps = ["frappe/erpnext", "frappe/hrms"]

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
