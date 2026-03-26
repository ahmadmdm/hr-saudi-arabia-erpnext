"""
install.py — تُنفَّذ عند تثبيت التطبيق لأوّل مرة.
تُنشئ: أنواع الإجازات السعودية، قواعد EOSB، إعدادات GOSI الافتراضية.
"""

import frappe


def after_install():
	create_workflow_states()
	sync_dashboard_chart_configs()
	sync_notification_configs()
	create_default_settings()
	frappe.db.commit()


def after_migrate():
	"""Called after every bench migrate — ensures workflow states always exist."""
	create_workflow_states()
	sync_dashboard_chart_configs()
	sync_notification_configs()
	migrate_legacy_annual_leave()
	migrate_legacy_employee_loans()


def sync_dashboard_chart_configs():
	"""Keep standard Saudi HR dashboard charts on the correct Frappe code path."""
	chart_updates = {
		"Nationality Distribution": {"chart_type": "Group By"},
		"Active Contracts by Type": {"chart_type": "Group By"},
	}

	for chart_name, values in chart_updates.items():
		if not frappe.db.exists("Dashboard Chart", chart_name):
			continue

		for fieldname, value in values.items():
			if frappe.db.get_value("Dashboard Chart", chart_name, fieldname) == value:
				continue

			frappe.db.set_value("Dashboard Chart", chart_name, fieldname, value, update_modified=False)


def sync_notification_configs():
	"""Keep GOSI notifications aligned with the scheduler-driven compliance flow."""
	old_name = "GOSI Due Alert"
	new_name = "GOSI Status Update Alert"

	if frappe.db.exists("Notification", old_name):
		event = frappe.db.get_value("Notification", old_name, "event")
		value_changed = frappe.db.get_value("Notification", old_name, "value_changed")

		if event == "Change" and value_changed == "payment_status":
			if frappe.db.exists("Notification", new_name):
				frappe.delete_doc("Notification", old_name, force=1, ignore_permissions=True)
			else:
				frappe.rename_doc("Notification", old_name, new_name, force=True, merge=False)


# ─── Workflow States ──────────────────────────────────────────────────────────

def create_workflow_states():
        """إنشاء حالات سير العمل العربية المطلوبة لجميع workflows في saudi_hr."""
        states = [
                ("مسودة / Draft",                              "Warning"),
                ("مفتوح / Open",                               "Warning"),
                ("قيد المراجعة / Under Review",                "Primary"),
                ("قيد التحقيق / In Progress",                  "Primary"),
                ("قيد التنفيذ / In Progress",                  "Primary"),
                ("بانتظار HR / Pending HR",                    "Primary"),
                ("بانتظار موافقة المدير / Pending Manager",   "Primary"),
                ("مراجعة HR / HR Review",                      "Primary"),
                ("موافقة الإدارة / Management Approval",       "Primary"),
                ("تم الإشعار / Notice Sent",                   "Primary"),
                ("معتمد / Approved",                           "Success"),
                ("تم البت / Decided",                          "Success"),
                ("محلول / Resolved",                           "Success"),
                ("مكتمل / Completed",                          "Success"),
                ("مغلق / Closed",                              "Success"),
                ("مرفوض / Rejected",                           "Danger"),
                ("ملغى / Cancelled",                           "Danger"),
        ]
        for state_name, style in states:
                if not frappe.db.exists("Workflow State", state_name):
                        frappe.get_doc({
                                "doctype": "Workflow State",
                                "workflow_state_name": state_name,
                                "style": style,
                        }).insert(ignore_permissions=True)


# ─── Leave Types ───────────────────────────────────────────────────────────────

def migrate_legacy_annual_leave():
	"""Copy legacy annual leave requests into Saudi Annual Leave before HRMS removal."""
	if not frappe.db.exists("DocType", "Saudi Annual Leave"):
		return
	if not frappe.db.exists("DocType", "Leave Application"):
		return

	annual_types = (
		"Saudi Annual Leave / إجازة سنوية",
		"Annual Leave",
	)
	rows = frappe.get_all(
		"Leave Application",
		filters={"leave_type": ["in", list(annual_types)]},
		fields=[
			"name",
			"employee",
			"employee_name",
			"company",
			"department",
			"from_date",
			"to_date",
			"half_day",
			"description",
			"status",
			"docstatus",
			"creation",
		],
	)

	for row in rows:
		if frappe.db.exists("Saudi Annual Leave", {"legacy_reference": row.name}):
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Saudi Annual Leave",
				"employee": row.employee,
				"employee_name": row.employee_name,
				"company": row.company,
				"department": row.department,
				"leave_start_date": row.from_date,
				"leave_end_date": row.to_date,
				"half_day": row.half_day,
				"description": row.description,
				"legacy_reference": row.name,
			}
		)
		doc.insert(ignore_permissions=True)
		if row.docstatus == 1:
			doc.submit()
		elif row.docstatus == 2:
			doc.submit()
			doc.cancel()
		elif row.status:
			doc.db_set("status", row.status)


def migrate_legacy_employee_loans():
	"""Backfill approval states for loans created before the approval workflow existed."""
	if not frappe.db.exists("DocType", "Employee Loan"):
		return

	from saudi_hr.saudi_hr.doctype.employee_loan.employee_loan import reconcile_legacy_employee_loans

	reconcile_legacy_employee_loans()


# ─── Saudi HR Settings ──────────────────────────────────────────────────────────

def create_default_settings():
	"""إنشاء إعدادات Saudi HR الافتراضية."""
	if frappe.db.exists("Saudi HR Settings", "Saudi HR Settings"):
		return

	settings = frappe.get_doc({
		"doctype": "Saudi HR Settings",
		"gosi_saudi_employee_rate": 10.0,
		"gosi_saudi_employer_rate": 12.0,
		"gosi_non_saudi_employee_rate": 0.0,
		"gosi_non_saudi_employer_rate": 2.0,
		"annual_leave_years_threshold": 5,
		"annual_leave_before_threshold": 21,
		"annual_leave_after_threshold": 30,
		"probation_period_days": 90,
		"max_probation_period_days": 180,
		"notice_period_monthly_days": 60,
		"notice_period_non_monthly_days": 30,
		"sick_leave_full_pay_days": 30,
		"sick_leave_partial_pay_days": 60,
		"sick_leave_partial_pay_percentage": 75,
		"iqama_expiry_alert_days": 90,
	})
	try:
		settings.insert(ignore_permissions=True)
		frappe.msgprint("Created Saudi HR default settings", alert=True)
	except Exception:
		pass
