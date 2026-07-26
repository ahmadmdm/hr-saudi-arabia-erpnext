"""Shared factories for isolated Saudi HR product tests."""

from __future__ import annotations

import frappe
from erpnext.setup.doctype.employee.test_employee import make_employee
from frappe.utils.password import update_password


STRONG_TEST_PASSWORD = "N7!xP4@qR9#vT2$k"


def select_option(doctype: str, fieldname: str, contains: str | None = None) -> str:
	field = frappe.get_meta(doctype).get_field(fieldname)
	options = [line.strip() for line in (field.options or "").splitlines() if line.strip()]
	if contains:
		for option in options:
			if contains.lower() in option.lower():
				return option
		raise AssertionError(f"No {doctype}.{fieldname} option contains {contains!r}")
	if not options:
		raise AssertionError(f"No options configured for {doctype}.{fieldname}")
	return options[0]


def ensure_test_user(email: str, *roles: str):
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@", 1)[0],
				"new_password": STRONG_TEST_PASSWORD,
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	if roles:
		user.add_roles(*roles)
	return user


def ensure_visual_test_user():
	"""Create the deterministic local-only user used by browser QA."""
	user = ensure_test_user(
		"visual.qa.v16@example.com",
		"System Manager",
		"HR Manager",
		"HR User",
	)
	user.language = "ar"
	user.enabled = 1
	user.save(ignore_permissions=True)
	update_password(user=user.name, pwd=STRONG_TEST_PASSWORD, logout_all_sessions=True)
	frappe.db.commit()
	return user.name


def disable_visual_test_user():
	"""Disable the deterministic browser QA user after visual verification."""
	from frappe.sessions import clear_sessions

	email = "visual.qa.v16@example.com"
	if frappe.db.exists("User", email):
		frappe.db.set_value("User", email, "enabled", 0)
		frappe.db.commit()
		clear_sessions(user=email, keep_current=False, force=True)
	return email


def configure_administrator_arabic():
	"""Use the professional Arabic Desk experience for the local administrator."""
	frappe.db.set_value("User", "Administrator", "language", "ar")
	frappe.clear_cache(user="Administrator")
	frappe.db.commit()
	return "ar"


def make_qa_employee(company: str, prefix: str = "employee") -> str:
	email = f"saudi.qa.{prefix}.{frappe.generate_hash(length=10).lower()}@example.com"
	ensure_test_user(email, "Employee")
	employee = make_employee(email, company=company)
	if frappe.get_meta("Employee").has_field("ctc"):
		frappe.db.set_value("Employee", employee, "ctc", 12000)
	return employee


def get_or_create_department(company: str, label: str = "Saudi QA") -> str:
	existing = frappe.get_all(
		"Department",
		filters={"company": company, "is_group": 0},
		pluck="name",
		limit_page_length=1,
	)
	if existing:
		return existing[0]
	return frappe.get_doc(
		{"doctype": "Department", "department_name": label, "company": company, "is_group": 0}
	).insert(ignore_permissions=True).name


def get_or_create_designation(label: str) -> str:
	if frappe.db.exists("Designation", label):
		return label
	return frappe.get_doc({"doctype": "Designation", "designation_name": label}).insert(ignore_permissions=True).name
