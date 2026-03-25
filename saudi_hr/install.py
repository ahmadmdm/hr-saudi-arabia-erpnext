"""
install.py — تُنفَّذ عند تثبيت التطبيق لأوّل مرة.
تُنشئ: أنواع الإجازات السعودية، قواعد EOSB، إعدادات GOSI الافتراضية.
"""

import frappe


def after_install():
	create_workflow_states()
	sync_dashboard_chart_configs()
	sync_notification_configs()
	create_saudi_leave_types()
	create_eosb_gratuity_rule()
	create_default_settings()
	frappe.db.commit()


def after_migrate():
	"""Called after every bench migrate — ensures workflow states always exist."""
	create_workflow_states()
	sync_dashboard_chart_configs()
	sync_notification_configs()


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

def create_saudi_leave_types():
	"""إنشاء أنواع الإجازات السعودية الإلزامية إن لم تكن موجودة."""
	leave_types = [
		{
			"leave_type_name": "Saudi Annual Leave / إجازة سنوية",
			"max_leaves_allowed": 30,
			"is_carry_forward": 1,
			"allow_encashment": 1,
			"description": "Annual leave per Saudi Labor Law Art. 109 — 21 days (<5 yrs) / 30 days (≥5 yrs)",
		},
		{
			"leave_type_name": "Saudi Sick Leave / إجازة مرضية",
			"max_leaves_allowed": 120,
			"is_lwp": 0,
			"description": "Sick leave per Saudi Labor Law Art. 117 — 30 days full pay / 60 days 75% / 30 days unpaid",
		},
		{
			"leave_type_name": "Saudi Maternity Leave / إجازة أمومة",
			"max_leaves_allowed": 70,
			"is_carry_forward": 0,
			"description": "Maternity leave per Saudi Labor Law Art. 151 — 70 days full pay",
		},
		{
			"leave_type_name": "Saudi Paternity Leave / إجازة أبوة",
			"max_leaves_allowed": 3,
			"is_carry_forward": 0,
			"description": "Paternity leave per Saudi Labor Law Art. 151 — 3 days full pay",
		},
		{
			"leave_type_name": "Hajj Leave / إجازة الحج",
			"max_leaves_allowed": 15,
			"is_carry_forward": 0,
			"applicable_after": 730,  # 2 years of service
			"description": "Hajj leave — once per service after 2 years, maximum 15 days",
		},
		{
			"leave_type_name": "Bereavement Leave / إجازة وفاة",
			"max_leaves_allowed": 5,
			"is_carry_forward": 0,
			"description": "Bereavement leave — 5 days for immediate family",
		},
		{
			"leave_type_name": "Marriage Leave / إجازة زواج",
			"max_leaves_allowed": 5,
			"is_carry_forward": 0,
			"description": "Marriage leave — 5 days with full pay",
		},
	]

	for lt in leave_types:
		if not frappe.db.exists("Leave Type", lt["leave_type_name"]):
			doc = frappe.get_doc({"doctype": "Leave Type", **lt})
			doc.insert(ignore_permissions=True)
			frappe.msgprint(f"Created Leave Type: {lt['leave_type_name']}", alert=True)


# ─── EOSB Gratuity Rule ─────────────────────────────────────────────────────────

def create_eosb_gratuity_rule():
	"""إنشاء قاعدة مكافأة نهاية الخدمة السعودية (م.84)."""
	if frappe.db.exists("Gratuity Rule", "Saudi EOSB Rule / قاعدة مكافأة نهاية الخدمة"):
		return

	rule = frappe.get_doc({
		"doctype": "Gratuity Rule",
		"name": "Saudi EOSB Rule / قاعدة مكافأة نهاية الخدمة",
		"calculate_gratuity_amount_based_on": "Sum of all previous slabs",
		"work_experience_calculation_function": "Manual",
		"total_working_days_per_year": 365,
		"minimum_year_for_gratuity": 1,
		"gratuity_rule_slabs": [
			# سنة 1 إلى 5: نصف شهر عن كل سنة
			{
				"from_year": 0,
				"to_year": 5,
				"fraction_of_applicable_earnings": 0.5,
			},
			# أكثر من 5 سنوات: شهر كامل عن كل سنة
			{
				"from_year": 5,
				"to_year": 0,  # 0 = no upper limit
				"fraction_of_applicable_earnings": 1.0,
			},
		],
	})
	try:
		rule.insert(ignore_permissions=True)
		frappe.msgprint("Created Saudi EOSB Gratuity Rule", alert=True)
	except Exception:
		pass  # Gratuity module may not be installed yet


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
