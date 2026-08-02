import frappe
from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr.test_support import make_qa_employee
from saudi_hr.saudi_hr.utils import get_annual_leave_entitlement_details, resolve_leave_policy


class TestSaudiLeavePolicyAssignment(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.company = frappe.get_all("Company", pluck="name", limit_page_length=1)[0]
		self.employee = make_qa_employee(self.company, f"leave-policy-{frappe.generate_hash(length=6)}")
		self.department = frappe.get_doc(
			{
				"doctype": "Department",
				"department_name": f"سياسات الإجازات QA {frappe.generate_hash(length=8)}",
				"company": self.company,
				"is_group": 0,
			}
		).insert(ignore_permissions=True).name
		frappe.db.set_value(
			"Employee",
			self.employee,
			{"company": self.company, "department": self.department, "date_of_joining": "2024-01-01"},
		)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		super().tearDown()

	def _policy(self, label, before_days, after_days, **overrides):
		values = {
			"doctype": "Saudi Leave Policy",
			"policy_name": f"{label} {frappe.generate_hash(length=8)}",
			"company": self.company,
			"enabled": 1,
			"annual_leave_years_threshold": 5,
			"annual_leave_before_threshold": before_days,
			"annual_leave_after_threshold": after_days,
			"sick_leave_full_pay_days": 30,
			"sick_leave_partial_pay_days": 60,
			"sick_leave_partial_pay_percentage": 75,
		}
		values.update(overrides)
		return frappe.get_doc(values).insert(ignore_permissions=True)

	def _assignment(self, policy, applies_to, **overrides):
		values = {
			"doctype": "Saudi Leave Policy Assignment",
			"policy": policy.name,
			"company": self.company,
			"applies_to": applies_to,
			"effective_from": "2026-01-01",
			"effective_to": "2026-12-31",
			"enabled": 1,
		}
		if applies_to == "Employee / موظف":
			values["employee"] = self.employee
		else:
			values["department"] = self.department
		values.update(overrides)
		return frappe.get_doc(values).insert(ignore_permissions=True)

	@staticmethod
	def _value(result, *keys):
		if result is None:
			return None
		if isinstance(result, str):
			return result if any(key in {"name", "policy", "policy_name"} for key in keys) else None
		for key in keys:
			if hasattr(result, "get"):
				value = result.get(key)
			else:
				value = getattr(result, key, None)
			if value is not None:
				return value
		return None

	def _resolved_policy_name(self, result):
		if result is None:
			return None
		if hasattr(result, "get") and "policy" in result:
			return result.get("policy")
		return self._value(result, "name", "policy")

	def test_settings_are_used_when_no_assignment_exists(self):
		settings = frappe.get_single("Saudi HR Settings")
		details = get_annual_leave_entitlement_details(self.employee, "2026-06-01")

		self.assertEqual(
			details["entitled"],
			int(settings.annual_leave_before_threshold or 21),
		)
		self.assertFalse(details["policy"])
		self.assertIn("Settings", details["policy_name"])
		self.assertIn("Settings", details["source_type"])
		self.assertEqual(details["statutory_minimum"], 21)

	def test_department_assignment_is_resolved_within_effective_period(self):
		department_policy = self._policy("سياسة القسم", 24, 34)
		self._assignment(department_policy, "Department / قسم")

		resolved = resolve_leave_policy(self.employee, "2026-06-01")
		details = get_annual_leave_entitlement_details(self.employee, "2026-06-01")

		self.assertEqual(self._resolved_policy_name(resolved), department_policy.name)
		self.assertEqual(self._resolved_policy_name(details), department_policy.name)
		self.assertEqual(details["entitled"], 24)
		self.assertIn("Department", details["source_type"])

	def test_employee_assignment_takes_precedence_over_department(self):
		department_policy = self._policy("سياسة القسم", 24, 34)
		employee_policy = self._policy("سياسة الموظف", 27, 37)
		self._assignment(department_policy, "Department / قسم")
		self._assignment(employee_policy, "Employee / موظف")

		resolved = resolve_leave_policy(self.employee, "2026-06-01")
		details = get_annual_leave_entitlement_details(self.employee, "2026-06-01")

		self.assertEqual(self._resolved_policy_name(resolved), employee_policy.name)
		self.assertEqual(details["entitled"], 27)
		self.assertIn("Employee", details["source_type"])

	def test_resolution_obeys_effective_dates_and_enabled_flag(self):
		department_policy = self._policy("سياسة القسم", 24, 34)
		employee_policy = self._policy("سياسة الموظف المستقبلية", 28, 38)
		self._assignment(department_policy, "Department / قسم")
		employee_assignment = self._assignment(
			employee_policy,
			"Employee / موظف",
			effective_from="2027-01-01",
			effective_to="2027-12-31",
		)

		self.assertEqual(
			self._resolved_policy_name(resolve_leave_policy(self.employee, "2026-06-01")),
			department_policy.name,
		)
		self.assertEqual(
			self._resolved_policy_name(resolve_leave_policy(self.employee, "2027-06-01")),
			employee_policy.name,
		)

		frappe.db.set_value("Saudi Leave Policy Assignment", employee_assignment.name, "enabled", 0)
		self.assertFalse(resolve_leave_policy(self.employee, "2027-06-01")["policy"])

	def test_overlapping_assignment_for_same_target_is_rejected(self):
		policy = self._policy("سياسة منع التداخل", 24, 34)
		self._assignment(
			policy,
			"Department / قسم",
			effective_from="2026-01-01",
			effective_to="2026-06-30",
		)

		with self.assertRaises(frappe.ValidationError):
			self._assignment(
				policy,
				"Department / قسم",
				effective_from="2026-06-30",
				effective_to="2026-12-31",
			)

	def test_policy_resolution_is_isolated_by_employee_company(self):
		department_policy = self._policy("سياسة شركة الموظف", 24, 34)
		self._assignment(department_policy, "Department / قسم")

		frappe.db.set_value("Employee", self.employee, "company", f"Other Company {frappe.generate_hash(length=8)}")
		resolved = resolve_leave_policy(self.employee, "2026-06-01")

		self.assertFalse(resolved["policy"])

	def test_entitlement_details_are_a_detached_policy_snapshot(self):
		policy = self._policy(
			"سياسة اللقطة",
			26,
			36,
			sick_leave_full_pay_days=40,
			sick_leave_partial_pay_days=65,
			sick_leave_partial_pay_percentage=80,
		)
		assignment = self._assignment(policy, "Employee / موظف")

		snapshot = get_annual_leave_entitlement_details(self.employee, "2026-06-01")

		self.assertEqual(self._resolved_policy_name(snapshot), policy.name)
		self.assertEqual(self._value(snapshot, "assignment", "policy_assignment"), assignment.name)
		self.assertEqual(self._value(snapshot, "annual_leave_before_threshold"), 26)
		self.assertEqual(self._value(snapshot, "annual_leave_after_threshold"), 36)
		self.assertEqual(self._value(snapshot, "sick_leave_full_pay_days"), 40)
		self.assertEqual(self._value(snapshot, "sick_leave_partial_pay_days"), 65)
		self.assertEqual(self._value(snapshot, "sick_leave_partial_pay_percentage"), 80)

		frappe.db.set_value("Saudi Leave Policy", policy.name, "annual_leave_before_threshold", 29)
		fresh = get_annual_leave_entitlement_details(self.employee, "2026-06-01")

		self.assertEqual(self._value(snapshot, "annual_leave_before_threshold"), 26)
		self.assertEqual(self._value(fresh, "annual_leave_before_threshold"), 29)
