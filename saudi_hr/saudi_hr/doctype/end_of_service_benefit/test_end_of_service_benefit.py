import frappe
from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr.doctype.end_of_service_benefit import end_of_service_benefit as eosb_module


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

	def test_calculate_eosb_preview_uses_shared_resignation_rules(self):
		result = eosb_module.calculate_eosb_preview(
			"2010-01-01",
			"2026-04-02",
			6000,
			"Resignation / استقالة",
		)

		self.assertEqual(result["resignation_factor"], round(2 / 3, 4))
		self.assertIn("2/3 EOSB", result["resignation_factor_label"])
		self.assertGreater(result["net_eosb"], 0)