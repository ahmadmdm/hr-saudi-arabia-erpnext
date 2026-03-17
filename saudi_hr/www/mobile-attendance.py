no_cache = 1
login_required = True


def get_context(context):
	import frappe
	from frappe import _

	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/mobile-attendance"
		raise frappe.Redirect

	# Basic context — the heavy data loading happens via API calls in the browser
	context.title = "حضور الموظفين | Saudi HR"
	context.full_name = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
