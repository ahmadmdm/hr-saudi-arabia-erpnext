# Copyright (c) 2026, IdeaOrbit and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from saudi_hr.saudi_hr.compliance_controls import (
	evaluate_working_time_status,
	get_special_working_hours_limits,
)


class TestWorkingTimeComplianceCheck(FrappeTestCase):
	def test_normal_hours_are_compliant(self):
		self.assertEqual(evaluate_working_time_status(8, 48), "Compliant / ممتثل")

	def test_overtime_without_approval_requires_review(self):
		self.assertEqual(evaluate_working_time_status(9, 50), "Needs Review / يحتاج مراجعة")

	def test_exception_with_approval_is_classified(self):
		self.assertEqual(evaluate_working_time_status(9, 50, approval_reference="SAU-OT-0001"), "Exception Approved / استثناء معتمد")

	def test_absolute_daily_limit_is_blocking_status(self):
		self.assertEqual(evaluate_working_time_status(10.5, 50), "Daily Limit Exceeded / تجاوز الحد اليومي")


class TestSpecialWorkingHoursLimits(FrappeTestCase):
	"""المادة (23) من اللائحة التنفيذية: ساعات العمل لفئات المادة (108) من النظام."""

	def test_senior_management_is_exempt(self):
		self.assertIsNone(get_special_working_hours_limits("Senior Management / مناصب عالية ذات مسؤولية"))

	def test_intermittent_work_is_ten_hours_and_eight_in_ramadan(self):
		category = "Intermittent by Necessity / عمل متقطع بالضرورة"
		self.assertEqual(get_special_working_hours_limits(category), {"daily": 10, "weekly": 48})
		self.assertEqual(
			get_special_working_hours_limits(category, is_ramadan=1, worker_is_muslim=1),
			{"daily": 8, "weekly": 36},
		)

	def test_guards_and_cleaners_are_twelve_hours_and_ten_in_ramadan(self):
		for category in ("Guarding / عمال الحراسة", "Cleaning / عمال النظافة"):
			self.assertEqual(get_special_working_hours_limits(category), {"daily": 12, "weekly": 48})
			self.assertEqual(
				get_special_working_hours_limits(category, is_ramadan=1, worker_is_muslim=1),
				{"daily": 10, "weekly": 36},
			)

	def test_ramadan_reduction_applies_to_muslim_workers_only(self):
		category = "Guarding / عمال الحراسة"
		self.assertEqual(
			get_special_working_hours_limits(category, is_ramadan=1, worker_is_muslim=0),
			{"daily": 12, "weekly": 48},
		)


class TestSpecialWorkingHoursDocument(FrappeTestCase):
	def _make_check(self, **kwargs):
		values = {
			"doctype": "Working Time Compliance Check",
			"employee": frappe.db.get_value("Employee", {"status": "Active"}, "name"),
			"check_date": today(),
			"work_category": "Standard / عمل اعتيادي",
		}
		values.update(kwargs)
		return frappe.get_doc(values).insert(ignore_permissions=True)

	def test_guard_working_twelve_hours_is_compliant(self):
		doc = self._make_check(
			work_category="Guarding / عمال الحراسة",
			actual_daily_hours=12,
			actual_weekly_hours=48,
		)
		self.assertEqual(doc.standard_daily_hours, 12)
		self.assertEqual(doc.overtime_hours, 0)
		self.assertEqual(doc.status, "Compliant / ممتثل")

	def test_hours_above_category_limit_become_overtime(self):
		doc = self._make_check(
			work_category="Guarding / عمال الحراسة",
			actual_daily_hours=13.5,
			actual_weekly_hours=48,
		)
		self.assertEqual(doc.overtime_hours, 1.5)
		self.assertEqual(doc.status, "Daily Limit Exceeded / تجاوز الحد اليومي")

	def test_civil_security_guard_is_outside_the_category(self):
		doc = self._make_check(
			work_category="Guarding / عمال الحراسة",
			is_civil_or_industrial_security=1,
			actual_daily_hours=12,
		)
		self.assertEqual(doc.status, "Category Control Breach / مخالفة ضوابط الفئة")
		self.assertIn("الحراسات الأمنية المدنية", doc.breach_summary)

	def test_preparatory_and_complementary_minutes_are_capped(self):
		doc = self._make_check(
			work_category="Preparatory or Complementary / أعمال تجهيزية أو تكميلية",
			actual_daily_hours=8,
			preparatory_minutes=20,
			complementary_minutes=15,
		)
		self.assertEqual(doc.total_added_minutes, 35)
		self.assertEqual(doc.status, "Category Control Breach / مخالفة ضوابط الفئة")
		self.assertIn("15", doc.breach_summary)
		self.assertIn("30", doc.breach_summary)

	def test_preparatory_within_caps_is_compliant(self):
		doc = self._make_check(
			work_category="Preparatory or Complementary / أعمال تجهيزية أو تكميلية",
			actual_daily_hours=8,
			preparatory_minutes=15,
			complementary_minutes=15,
		)
		self.assertEqual(doc.total_added_minutes, 30)
		self.assertEqual(doc.status, "Compliant / ممتثل")

	def test_intermittent_work_requires_ten_continuous_rest_hours(self):
		doc = self._make_check(
			work_category="Intermittent by Necessity / عمل متقطع بالضرورة",
			actual_daily_hours=10,
			continuous_rest_hours=8,
		)
		self.assertEqual(doc.status, "Category Control Breach / مخالفة ضوابط الفئة")
		self.assertIn("الراحة المتواصلة", doc.breach_summary)

	def test_cleaner_exceeding_six_consecutive_hours_is_flagged(self):
		doc = self._make_check(
			work_category="Cleaning / عمال النظافة",
			actual_daily_hours=12,
			max_consecutive_hours=7,
		)
		self.assertEqual(doc.status, "Category Control Breach / مخالفة ضوابط الفئة")
		self.assertIn("النظافة المتوالي", doc.breach_summary)

	def test_prayer_time_must_be_enabled_for_special_categories(self):
		doc = self._make_check(
			work_category="Intermittent by Necessity / عمل متقطع بالضرورة",
			actual_daily_hours=10,
			continuous_rest_hours=12,
			prayer_time_enabled=0,
		)
		self.assertEqual(doc.status, "Category Control Breach / مخالفة ضوابط الفئة")
		self.assertIn("الصلوات", doc.breach_summary)

	def test_senior_management_document_is_marked_exempt(self):
		doc = self._make_check(
			work_category="Senior Management / مناصب عالية ذات مسؤولية",
			actual_daily_hours=11,
			actual_weekly_hours=55,
		)
		self.assertEqual(doc.status, "Exempt Category / فئة مستثناة")
		self.assertEqual(doc.overtime_hours, 0)
