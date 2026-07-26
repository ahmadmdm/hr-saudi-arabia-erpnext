# Copyright (c) 2026, IdeaOrbit and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr.compliance_controls import (
	SAUDI_ONLY_PROFESSION_DEFAULTS,
	is_saudi_only_profession,
	match_saudi_only_profession,
)


class TestSaudiOnlyProfession(FrappeTestCase):
	"""المادة (11) من اللائحة التنفيذية: المهن المقصورة على السعوديين."""

	def test_all_eighteen_regulated_professions_are_seeded(self):
		self.assertEqual(len(SAUDI_ONLY_PROFESSION_DEFAULTS), 18)
		for code, name_ar, _name_en, _group in SAUDI_ONLY_PROFESSION_DEFAULTS:
			self.assertTrue(
				frappe.db.exists("Saudi Only Profession", {"profession_code": code}),
				msg=f"{code} ({name_ar}) is not seeded",
			)

	def test_restricted_profession_is_detected_in_arabic_and_english(self):
		self.assertTrue(is_saudi_only_profession("أمين صندوق"))
		self.assertTrue(is_saudi_only_profession("Cashier"))
		self.assertEqual(match_saudi_only_profession("Cashier"), "أمين صندوق")

	def test_restriction_covers_disguised_job_titles(self):
		"""لا يجوز إسناد مهام المهنة المقصورة تحت أي مسمى وظيفي آخر."""
		self.assertTrue(is_saudi_only_profession("كاتب دوام أول"))
		self.assertTrue(is_saudi_only_profession("Senior Recruitment Clerk"))

	def test_unrestricted_profession_is_allowed(self):
		self.assertFalse(is_saudi_only_profession("مهندس مدني"))
		self.assertFalse(is_saudi_only_profession("Software Engineer"))
		self.assertFalse(is_saudi_only_profession(""))
		self.assertFalse(is_saudi_only_profession(None))
