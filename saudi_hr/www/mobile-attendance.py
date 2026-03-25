no_cache = 1
login_required = True


def get_context(context):
	import frappe
	from frappe import _

	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/mobile-attendance"
		raise frappe.Redirect

	# Basic context — the heavy data loading happens via API calls in the browser
	user_lang = frappe.db.get_value("User", frappe.session.user, "language")
	lang_code = (user_lang or frappe.local.lang or "ar").lower()
	is_english = lang_code.startswith("en")
	context.title = "Mobile Attendance | Saudi HR" if is_english else "حضور الموظفين | Saudi HR"
	context.full_name = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
	context.no_breadcrumbs = True
	context.show_sidebar = False
	context.lang_code = lang_code
	context.text_direction = "ltr" if is_english else "rtl"
