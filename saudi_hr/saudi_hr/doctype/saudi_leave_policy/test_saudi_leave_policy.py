import frappe
from frappe.tests.utils import FrappeTestCase


STATUTORY_DEFAULTS = {
	"annual_leave_years_threshold": 5,
	"annual_leave_before_threshold": 21,
	"annual_leave_after_threshold": 30,
	"sick_leave_full_pay_days": 30,
	"sick_leave_partial_pay_days": 60,
	"sick_leave_partial_pay_percentage": 75,
}


class TestSaudiLeavePolicy(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.company = frappe.get_all("Company", pluck="name", limit_page_length=1)[0]

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		super().tearDown()

	def _policy(self, **overrides):
		values = {
			"doctype": "Saudi Leave Policy",
			"policy_name": f"سياسة إجازات QA {frappe.generate_hash(length=8)}",
			"company": self.company,
			"enabled": 1,
			**STATUTORY_DEFAULTS,
		}
		values.update(overrides)
		return frappe.get_doc(values)

	def test_policy_accepts_statutory_floors_and_better_benefits(self):
		policy = self._policy(
			annual_leave_years_threshold=4,
			annual_leave_before_threshold=24,
			annual_leave_after_threshold=35,
			sick_leave_full_pay_days=40,
			sick_leave_partial_pay_days=60,
			sick_leave_partial_pay_percentage=80,
		).insert(ignore_permissions=True)

		self.assertEqual(policy.annual_leave_years_threshold, 4)
		self.assertEqual(policy.annual_leave_before_threshold, 24)
		self.assertEqual(policy.annual_leave_after_threshold, 35)
		self.assertEqual(policy.sick_leave_full_pay_days, 40)
		self.assertEqual(policy.sick_leave_partial_pay_percentage, 80)

	def test_policy_rejects_values_below_statutory_floors(self):
		invalid_values = (
			{"annual_leave_years_threshold": 6},
			{"annual_leave_before_threshold": 20},
			{"annual_leave_after_threshold": 29},
			{"sick_leave_full_pay_days": 29},
			{"sick_leave_partial_pay_days": 59},
			{"sick_leave_partial_pay_percentage": 74},
		)

		for values in invalid_values:
			with self.subTest(values=values), self.assertRaises(frappe.ValidationError):
				self._policy(**values).insert(ignore_permissions=True)

	def test_policy_rejects_non_positive_service_threshold(self):
		with self.assertRaises(frappe.ValidationError):
			self._policy(annual_leave_years_threshold=0).insert(ignore_permissions=True)
