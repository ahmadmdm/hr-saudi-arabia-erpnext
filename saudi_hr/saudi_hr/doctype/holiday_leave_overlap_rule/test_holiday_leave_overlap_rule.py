# Copyright (c) 2026, IdeaOrbit and Contributors
# See license.txt

from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr.compliance_controls import get_holiday_overlap_action


class TestHolidayLeaveOverlapRule(FrappeTestCase):
	def test_annual_leave_is_extended(self):
		self.assertEqual(
			get_holiday_overlap_action("Annual Leave / إجازة سنوية"),
			"Extend Leave / تمديد الإجازة",
		)

	def test_weekly_rest_day_is_compensated(self):
		self.assertEqual(
			get_holiday_overlap_action("Weekly Rest / راحة أسبوعية"),
			"Compensate Rest Day / تعويض يوم راحة",
		)
