# Copyright (c) 2026, IdeaOrbit and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from saudi_hr.saudi_hr.compliance_controls import (
	EDUCATION_EXCEPTION_CONDITIONS,
	JUVENILE_PROHIBITED_WORK_DEFAULTS,
	calculate_juvenile_age,
	match_juvenile_prohibited_work,
)

ALL_EDUCATION_CONDITIONS = {fieldname: 1 for fieldname, _label in EDUCATION_EXCEPTION_CONDITIONS}


def _birth_date_for_age(age_years):
	return add_days(today(), -int(age_years * 365.25))


class TestJuvenileProhibitedWork(FrappeTestCase):
	"""المادة (32) من اللائحة التنفيذية: الأعمال المحظورة على الأحداث."""

	def test_all_five_prohibited_categories_are_seeded(self):
		self.assertEqual(len(JUVENILE_PROHIBITED_WORK_DEFAULTS), 5)
		for code, *_rest in JUVENILE_PROHIBITED_WORK_DEFAULTS:
			self.assertTrue(
				frappe.db.exists("Juvenile Prohibited Work", {"work_code": code}),
				msg=f"{code} is not seeded",
			)

	def test_mining_work_is_detected(self):
		self.assertIsNotNone(match_juvenile_prohibited_work("العمل في منجم للذهب"))
		self.assertIsNotNone(match_juvenile_prohibited_work("Underground mining assistant"))

	def test_sharp_cutting_machinery_is_detected(self):
		self.assertIsNotNone(match_juvenile_prohibited_work("تشغيل آلات القطع في الورشة"))

	def test_arduous_work_is_detected(self):
		self.assertIsNotNone(match_juvenile_prohibited_work("أعمال شاقة في المستودع"))

	def test_safe_office_work_is_not_flagged(self):
		self.assertIsNone(match_juvenile_prohibited_work("إدخال بيانات في المكتب"))
		self.assertIsNone(match_juvenile_prohibited_work("Filing documents"))
		self.assertIsNone(match_juvenile_prohibited_work(""))

	def test_age_calculation(self):
		self.assertAlmostEqual(calculate_juvenile_age(_birth_date_for_age(16)), 16, delta=0.05)
		self.assertIsNone(calculate_juvenile_age(None))


class TestJuvenileEmploymentControls(FrappeTestCase):
	"""المواد (32) و(33) و(34): ضوابط تشغيل الأحداث."""

	def _make_control(self, age, **kwargs):
		employee = frappe.db.get_value("Employee", {"status": "Active"}, "name")
		frappe.db.set_value("Employee", employee, "date_of_birth", _birth_date_for_age(age))
		values = {
			"doctype": "Special Employment Category Control",
			"employee": employee,
			"category": "Young Worker / عامل حدث",
			"date_of_birth": _birth_date_for_age(age),
		}
		values.update(kwargs)
		return frappe.get_doc(values).insert(ignore_permissions=True)

	def test_worker_below_fifteen_is_a_breach(self):
		doc = self._make_control(13, assigned_work_description="إدخال بيانات")
		self.assertEqual(doc.minimum_age_breach, 1)
		self.assertEqual(doc.status, "Restriction Breach / مخالفة قيد")
		self.assertIn("الخامسة عشرة", doc.juvenile_breach_summary)

	def test_education_exception_allows_fourteen_year_old_when_all_conditions_met(self):
		doc = self._make_control(
			14,
			assigned_work_description="تدريب مكتبي",
			education_exception_applies=1,
			**ALL_EDUCATION_CONDITIONS,
		)
		self.assertEqual(doc.education_exception_valid, 1)
		self.assertEqual(doc.minimum_age_breach, 0)

	def test_education_exception_does_not_cover_under_fourteen(self):
		doc = self._make_control(
			12,
			assigned_work_description="تدريب مكتبي",
			education_exception_applies=1,
			**ALL_EDUCATION_CONDITIONS,
		)
		self.assertEqual(doc.education_exception_valid, 0)
		self.assertEqual(doc.minimum_age_breach, 1)

	def test_education_exception_requires_all_five_conditions(self):
		"""المادة (35): مربع اختيار واحد لا يكفي لإسقاط شرط السن."""
		doc = self._make_control(
			14,
			assigned_work_description="تدريب مكتبي",
			education_exception_applies=1,
		)
		self.assertEqual(doc.education_exception_valid, 0)
		self.assertEqual(doc.minimum_age_breach, 1)
		self.assertIn("المادة (35)", doc.juvenile_breach_summary)

	def test_each_missing_condition_blocks_the_exception(self):
		for fieldname, _label in EDUCATION_EXCEPTION_CONDITIONS:
			conditions = dict(ALL_EDUCATION_CONDITIONS)
			conditions[fieldname] = 0
			doc = self._make_control(
				14,
				assigned_work_description="تدريب مكتبي",
				education_exception_applies=1,
				**conditions,
			)
			self.assertEqual(
				doc.education_exception_valid,
				0,
				msg=f"exception should fail when {fieldname} is unmet",
			)

	def test_hazardous_work_cannot_satisfy_the_not_hazardous_condition(self):
		"""لا يصح إقرار «ليست خطرة» وقد طابق العمل دليل الأعمال المحظورة."""
		doc = self._make_control(
			14,
			assigned_work_description="مساعد في منجم",
			education_exception_applies=1,
			**ALL_EDUCATION_CONDITIONS,
		)
		self.assertEqual(doc.edu_not_hazardous, 0)
		self.assertEqual(doc.education_exception_valid, 0)
		self.assertEqual(doc.prohibited_work_breach, 1)

	def test_juvenile_assigned_prohibited_work_is_flagged(self):
		doc = self._make_control(16, assigned_work_description="مساعد في منجم")
		self.assertEqual(doc.prohibited_work_breach, 1)
		self.assertTrue(doc.matched_prohibited_work)
		self.assertEqual(doc.status, "Restriction Breach / مخالفة قيد")

	def test_juvenile_on_safe_work_is_compliant(self):
		doc = self._make_control(16, assigned_work_description="ترتيب ملفات في المكتب")
		self.assertEqual(doc.prohibited_work_breach, 0)
		self.assertEqual(doc.night_work_restriction, 1)
		self.assertEqual(doc.status, "Compliant / ممتثل")

	def test_night_shift_without_exception_is_a_breach(self):
		doc = self._make_control(
			16,
			assigned_work_description="ترتيب ملفات",
			night_shift_assigned=1,
		)
		self.assertEqual(doc.night_work_breach, 1)
		self.assertIn("اثنتي عشرة ساعة", doc.juvenile_breach_summary)

	def test_night_shift_with_regulated_exception_is_allowed(self):
		doc = self._make_control(
			16,
			assigned_work_description="ترتيب ملفات",
			night_shift_assigned=1,
			night_work_exception="Bakery outside 9pm-4am / مخابز خارج الفترة 9 مساءً - 4 صباحاً",
		)
		self.assertEqual(doc.night_work_breach, 0)
		self.assertEqual(doc.status, "Compliant / ممتثل")

	def test_adult_worker_skips_juvenile_controls(self):
		employee = frappe.db.get_value("Employee", {"status": "Active"}, "name")
		doc = frappe.get_doc(
			{
				"doctype": "Special Employment Category Control",
				"employee": employee,
				"category": "Woman Worker / عاملة",
				"assigned_work_description": "مساعد في منجم",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(doc.prohibited_work_breach, 0)
		self.assertIsNone(doc.juvenile_breach_summary)
