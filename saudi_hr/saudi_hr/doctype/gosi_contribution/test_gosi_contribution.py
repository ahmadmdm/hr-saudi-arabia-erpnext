import frappe
from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr.utils import (
	GOSI_NEW_SYSTEM_START_DATE,
	GOSI_SOURCE_ASSUMED,
	backfill_gosi_first_contribution_dates,
	get_gosi_pension_rate,
	get_gosi_rates,
	is_gosi_new_system_subscriber,
)

test_ignore = ["Journal Entry"]


class TestGOSIPensionSchedule(FrappeTestCase):
	"""جدول نسب المعاشات — النظام السابق ونظام التأمينات الجديد (م/273)."""

	def test_previous_system_pension_is_flat_nine_percent(self):
		self.assertEqual(get_gosi_pension_rate(False), 9.0)
		self.assertEqual(get_gosi_pension_rate(False, "2030-01-01"), 9.0)

	def test_new_system_pension_schedule_steps_half_a_point_each_july(self):
		expected = {
			"2024-08-01": 9.0,
			"2025-06-30": 9.0,
			"2025-07-01": 9.5,
			"2026-06-30": 9.5,
			"2026-07-01": 10.0,
			"2027-07-01": 10.5,
			"2028-07-01": 11.0,
			"2031-01-01": 11.0,
		}
		for as_on_date, rate in expected.items():
			self.assertEqual(
				get_gosi_pension_rate(True, as_on_date),
				rate,
				msg=f"pension rate on {as_on_date}",
			)


class TestGOSIRates(FrappeTestCase):
	def setUp(self):
		self.employee = frappe.db.get_value("Employee", {"status": "Active"}, "name")

	def _set_first_contribution(self, date_value):
		frappe.db.set_value("Employee", self.employee, "gosi_first_contribution_date", date_value)

	def test_non_saudi_pays_occupational_hazards_only(self):
		rates = get_gosi_rates("Indian")
		self.assertEqual(rates["employee_rate"], 0.0)
		self.assertEqual(rates["employer_rate"], 2.0)

	def test_previous_system_saudi_rates(self):
		"""9% معاشات + 0.75% ساند للعامل، ويضاف 2% أخطار مهنية على صاحب العمل."""
		self._set_first_contribution("2020-01-01")
		rates = get_gosi_rates("Saudi", employee=self.employee, as_on_date="2026-07-25")
		self.assertEqual(rates["employee_rate"], 9.75)
		self.assertEqual(rates["employer_rate"], 11.75)
		self.assertIn("Previous System", rates["system"])

	def test_new_system_saudi_rates_in_july_2026(self):
		"""المعاشات 10% في يوليو 2026 => العامل 10.75% وصاحب العمل 12.75%."""
		self._set_first_contribution("2024-09-01")
		rates = get_gosi_rates("Saudi", employee=self.employee, as_on_date="2026-07-25")
		self.assertEqual(rates["employee_rate"], 10.75)
		self.assertEqual(rates["employer_rate"], 12.75)
		self.assertIn("New System", rates["system"])

	def test_new_system_saudi_rates_in_first_half_of_2026(self):
		self._set_first_contribution("2024-09-01")
		rates = get_gosi_rates("Saudi", employee=self.employee, as_on_date="2026-03-01")
		self.assertEqual(rates["employee_rate"], 10.25)
		self.assertEqual(rates["employer_rate"], 12.25)

	def test_new_system_reaches_eleven_percent_pension_in_2028(self):
		self._set_first_contribution("2024-09-01")
		rates = get_gosi_rates("Saudi", employee=self.employee, as_on_date="2028-08-01")
		self.assertEqual(rates["employee_rate"], 11.75)
		self.assertEqual(rates["employer_rate"], 13.75)

	def test_subscriber_on_the_cutover_date_is_new_system(self):
		self._set_first_contribution(GOSI_NEW_SYSTEM_START_DATE)
		self.assertTrue(is_gosi_new_system_subscriber(self.employee))

	def test_subscriber_one_day_before_cutover_is_previous_system(self):
		self._set_first_contribution("2024-07-02")
		self.assertFalse(is_gosi_new_system_subscriber(self.employee))

	def test_missing_first_contribution_date_falls_back_to_joining_date(self):
		self._set_first_contribution(None)
		frappe.db.set_value("Employee", self.employee, "date_of_joining", "2019-01-01")
		self.assertFalse(is_gosi_new_system_subscriber(self.employee))
		frappe.db.set_value("Employee", self.employee, "date_of_joining", "2025-01-01")
		self.assertTrue(is_gosi_new_system_subscriber(self.employee))


class TestGOSIContributionDocument(FrappeTestCase):
	def _make_contribution(self, first_contribution_date, month, year, base=10000):
		employee = frappe.db.get_value("Employee", {"status": "Active"}, "name")
		frappe.db.set_value("Employee", employee, "gosi_first_contribution_date", first_contribution_date)
		return frappe.get_doc(
			{
				"doctype": "GOSI Contribution",
				"employee": employee,
				"nationality": "Saudi",
				"month": month,
				"year": year,
				"contribution_base": base,
			}
		).insert(ignore_permissions=True)

	def test_contribution_uses_rate_of_its_own_month(self):
		doc = self._make_contribution("2024-09-01", "March", 2026)
		self.assertEqual(doc.employee_contribution_rate, 10.25)
		self.assertEqual(doc.employee_contribution, 1025.0)

		later = self._make_contribution("2024-09-01", "August", 2026)
		self.assertEqual(later.employee_contribution_rate, 10.75)
		self.assertEqual(later.employee_contribution, 1075.0)

	def test_branch_breakdown_matches_total_rates(self):
		doc = self._make_contribution("2024-09-01", "August", 2026)
		self.assertEqual(doc.saudi_employee_pension_rate, 10.0)
		self.assertEqual(doc.saudi_employee_unemployment_rate, 0.75)
		self.assertEqual(doc.saudi_employer_hazard_rate, 2.0)
		self.assertAlmostEqual(
			doc.saudi_employee_pension_rate + doc.saudi_employee_unemployment_rate,
			doc.employee_contribution_rate,
			places=4,
		)

	def test_contribution_base_is_capped_at_forty_five_thousand(self):
		doc = self._make_contribution("2020-01-01", "August", 2026, base=60000)
		self.assertEqual(doc.contribution_base, 45000)
		self.assertEqual(doc.employee_contribution, round(45000 * 0.0975, 2))


class TestGOSINationalityGuard(FrappeTestCase):
	"""بدون الجنسية تُطبَّق نسبة غير السعوديين على السعوديين خطأً، فيجب منع الحفظ."""
	def _make_employee_without_nationality(self):
		seed = frappe.db.get_value(
			"Employee",
			{"status": "Active"},
			["company", "gender", "date_of_birth", "date_of_joining"],
			as_dict=True,
		)
		self.assertTrue(seed, "an active Employee fixture is required")
		return frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": f"GOSI Guard {frappe.generate_hash(length=8)}",
				"company": seed.company,
				"gender": seed.gender,
				"date_of_birth": seed.date_of_birth or "1990-01-01",
				"date_of_joining": seed.date_of_joining or "2020-01-01",
				"status": "Active",
				"nationality": None,
			}
		).insert(ignore_permissions=True).name

	def test_contribution_without_resolvable_nationality_is_rejected(self):
		employee = self._make_employee_without_nationality()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "GOSI Contribution",
					"employee": employee,
					"month": "August",
					"year": 2026,
					"contribution_base": 10000,
				}
			).insert(ignore_permissions=True)

	def test_explicit_nationality_is_accepted(self):
		employee = frappe.db.get_value("Employee", {"status": "Active"}, "name")
		doc = frappe.get_doc(
			{
				"doctype": "GOSI Contribution",
				"employee": employee,
				"nationality": "Saudi / سعودي",
				"month": "August",
				"year": 2026,
				"contribution_base": 10000,
			}
		).insert(ignore_permissions=True)
		self.assertGreater(doc.employee_contribution_rate, 0)


class TestGOSIFirstContributionBackfill(FrappeTestCase):
	"""تعبئة تاريخ أول اشتراك من تاريخ الالتحاق."""

	def setUp(self):
		self.employee = frappe.db.get_value("Employee", {"status": "Active"}, "name")
		self.original_joining = frappe.db.get_value("Employee", self.employee, "date_of_joining")
		frappe.db.set_value("Employee", self.employee, "gosi_first_contribution_date", None)
		frappe.db.set_value("Employee", self.employee, "gosi_subscription_date_source", None)

	def tearDown(self):
		frappe.db.set_value("Employee", self.employee, "date_of_joining", self.original_joining)

	def _touched(self, result):
		return {row["employee"] for row in result["employees"]}

	def test_dry_run_reports_without_writing(self):
		frappe.db.set_value("Employee", self.employee, "date_of_joining", "2025-03-01")
		result = backfill_gosi_first_contribution_dates(dry_run=1)

		self.assertTrue(result["dry_run"])
		self.assertIn(self.employee, self._touched(result))
		self.assertIsNone(frappe.db.get_value("Employee", self.employee, "gosi_first_contribution_date"))

	def test_backfill_writes_joining_date_and_marks_it_assumed(self):
		frappe.db.set_value("Employee", self.employee, "date_of_joining", "2025-03-01")
		backfill_gosi_first_contribution_dates(dry_run=0)

		self.assertEqual(
			str(frappe.db.get_value("Employee", self.employee, "gosi_first_contribution_date")),
			"2025-03-01",
		)
		self.assertEqual(
			frappe.db.get_value("Employee", self.employee, "gosi_subscription_date_source"),
			GOSI_SOURCE_ASSUMED,
		)

	def test_employees_who_joined_before_the_cutover_are_skipped(self):
		frappe.db.set_value("Employee", self.employee, "date_of_joining", "2024-07-02")
		result = backfill_gosi_first_contribution_dates(dry_run=0)

		self.assertNotIn(self.employee, self._touched(result))
		self.assertIsNone(frappe.db.get_value("Employee", self.employee, "gosi_first_contribution_date"))

	def test_existing_confirmed_date_is_never_overwritten(self):
		frappe.db.set_value("Employee", self.employee, "date_of_joining", "2025-03-01")
		frappe.db.set_value("Employee", self.employee, "gosi_first_contribution_date", "2019-01-01")
		result = backfill_gosi_first_contribution_dates(dry_run=0)

		self.assertNotIn(self.employee, self._touched(result))
		self.assertEqual(
			str(frappe.db.get_value("Employee", self.employee, "gosi_first_contribution_date")),
			"2019-01-01",
		)

	def test_backfill_is_idempotent(self):
		frappe.db.set_value("Employee", self.employee, "date_of_joining", "2025-03-01")
		backfill_gosi_first_contribution_dates(dry_run=0)
		second = backfill_gosi_first_contribution_dates(dry_run=0)

		self.assertNotIn(self.employee, self._touched(second))

	def test_backfilled_employee_resolves_to_the_new_system(self):
		frappe.db.set_value("Employee", self.employee, "date_of_joining", "2025-03-01")
		backfill_gosi_first_contribution_dates(dry_run=0)

		self.assertTrue(is_gosi_new_system_subscriber(self.employee))
