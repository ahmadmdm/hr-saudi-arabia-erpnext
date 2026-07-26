# Copyright (c) 2026, IdeaOrbit and Contributors
# See license.txt

from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr.compliance_controls import calculate_flexible_work_limits


class TestWorkArrangementControl(FrappeTestCase):
	def test_flexible_overtime_starts_after_ninety_five_hours(self):
		self.assertEqual(calculate_flexible_work_limits(120)["overtime_hours"], 25)

	def test_flexible_monthly_maximum_is_detected(self):
		self.assertTrue(calculate_flexible_work_limits(161)["maximum_exceeded"])

	def test_flexible_nitaqat_credit_requires_one_hundred_sixty_hours(self):
		self.assertEqual(calculate_flexible_work_limits(159.99)["nitaqat_credit"], 0)
		self.assertEqual(calculate_flexible_work_limits(160)["nitaqat_credit"], 1)

	def test_flexible_work_excludes_paid_leave_eosb_and_probation(self):
		result = calculate_flexible_work_limits(95)
		self.assertFalse(result["paid_leave_entitled"])
		self.assertFalse(result["eosb_entitled"])
		self.assertFalse(result["probation_applicable"])
		self.assertTrue(result["overtime_at_base_hourly_rate"])
