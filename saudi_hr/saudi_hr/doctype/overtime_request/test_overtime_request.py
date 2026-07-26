from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr.doctype.overtime_request.overtime_request import (
	calculate_annual_overtime_status,
	calculate_compensatory_leave_entitlement,
	calculate_overtime_breakdown,
)


test_ignore = ["Journal Entry"]


class TestOvertimeRequest(FrappeTestCase):
	def test_article_107_uses_actual_hourly_plus_half_basic_hourly(self):
		result = calculate_overtime_breakdown(6000, 4000, 2)

		self.assertAlmostEqual(result["actual_hourly_rate"], 25, places=4)
		self.assertAlmostEqual(result["basic_hourly_rate"], 16.6667, places=4)
		self.assertAlmostEqual(result["overtime_premium_hourly"], 8.3333, places=4)
		self.assertAlmostEqual(result["payable_hourly_rate"], 33.3333, places=4)
		self.assertEqual(result["overtime_amount"], 66.67)

	def test_equivalent_rate_is_one_and_half_when_actual_equals_basic(self):
		result = calculate_overtime_breakdown(4800, 4800, 1)
		self.assertEqual(result["equivalent_basic_rate"], 1.5)
		self.assertEqual(result["overtime_amount"], 30)

	def test_compensatory_leave_uses_one_and_half_factor_and_sixty_day_deadline(self):
		result = calculate_compensatory_leave_entitlement(4, "2026-07-01", 8)

		self.assertEqual(result["leave_hours"], 6)
		self.assertEqual(result["leave_days"], 0.75)
		self.assertEqual(str(result["use_by"]), "2026-08-30")
		self.assertEqual(result["annual_cap_days"], 30)

	def test_annual_overtime_requires_consent_only_above_seven_hundred_twenty(self):
		self.assertFalse(calculate_annual_overtime_status(718, 2)["consent_required"])
		self.assertTrue(calculate_annual_overtime_status(720, 0.25)["consent_required"])
