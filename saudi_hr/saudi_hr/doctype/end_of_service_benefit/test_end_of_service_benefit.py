import frappe
from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr.doctype.end_of_service_benefit import end_of_service_benefit as eosb_module


test_ignore = ["Journal Entry"]


class TestEndOfServiceBenefit(FrappeTestCase):
	def test_calculate_eosb_preview_rejects_invalid_dates(self):
		with self.assertRaises(frappe.ValidationError):
			eosb_module.calculate_eosb_preview(
				"2026-04-02",
				"2026-04-01",
				5000,
				"Resignation / استقالة",
			)

	def test_calculate_eosb_preview_rejects_negative_net_amount(self):
		with self.assertRaises(frappe.ValidationError):
			eosb_module.calculate_eosb_preview(
				"2015-01-01",
				"2026-04-02",
				5000,
				"Termination by Employer / إنهاء من صاحب العمل",
				eosb_deductions=999999,
			)

	def test_resignation_below_two_years_earns_nothing(self):
		result = eosb_module.calculate_eosb_preview(
			"2025-01-01",
			"2026-04-02",
			6000,
			"Resignation / استقالة",
		)

		self.assertEqual(result["resignation_factor"], 0.0)
		self.assertEqual(result["net_eosb"], 0)

	def test_resignation_between_two_and_five_years_earns_one_third(self):
		result = eosb_module.calculate_eosb_preview(
			"2022-01-01",
			"2026-04-02",
			6000,
			"Resignation / استقالة",
		)

		self.assertEqual(result["resignation_factor"], round(1 / 3, 4))
		self.assertIn("1/3 EOSB", result["resignation_factor_label"])

	def test_resignation_between_five_and_ten_years_earns_two_thirds(self):
		result = eosb_module.calculate_eosb_preview(
			"2018-01-01",
			"2026-04-02",
			6000,
			"Resignation / استقالة",
		)

		self.assertEqual(result["resignation_factor"], round(2 / 3, 4))
		self.assertIn("2/3 EOSB", result["resignation_factor_label"])

	def test_resignation_at_ten_years_or_more_earns_full_award(self):
		"""المادة (85): يستحق المكافأة كاملة إذا بلغت مدة خدمته عشر سنوات فأكثر."""
		result = eosb_module.calculate_eosb_preview(
			"2010-01-01",
			"2026-04-02",
			6000,
			"Resignation / استقالة",
		)

		self.assertEqual(result["resignation_factor"], 1.0)
		self.assertIn("Full EOSB", result["resignation_factor_label"])
		self.assertEqual(result["net_eosb"], result["eosb_gross"])

	def test_employer_termination_below_one_year_is_prorated(self):
		"""المادة (84): يستحق العامل مكافأة عن أجزاء السنة بنسبة ما قضاه منها."""
		result = eosb_module.calculate_eosb_preview(
			"2025-10-02",
			"2026-04-02",
			6000,
			"Termination by Employer / إنهاء من صاحب العمل",
		)

		self.assertGreater(result["net_eosb"], 0)
		# نصف أجر شهر × نسبة ما قضاه من السنة (182 يوماً / 365)
		self.assertAlmostEqual(result["net_eosb"], (6000 / 2) * (182 / 365), places=2)