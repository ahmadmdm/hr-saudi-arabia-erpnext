from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr.doctype.annual_leave_disbursement import annual_leave_disbursement as annual_leave_module


class TestAnnualLeaveDisbursement(FrappeTestCase):
	def test_get_supported_annual_leave_types_uses_existing_site_type(self):
		with patch.object(annual_leave_module.frappe, "get_all", return_value=["Saudi Annual Leave / إجازة سنوية"]):
			self.assertEqual(
				annual_leave_module._get_supported_annual_leave_types(),
				["Saudi Annual Leave / إجازة سنوية"],
			)

	def test_get_taken_annual_leave_days_falls_back_to_supported_candidates(self):
		calls = []

		def fake_get_all(doctype, **kwargs):
			calls.append((doctype, kwargs))
			if doctype == "Leave Type":
				return []
			return [frappe._dict(total_leave_days=5), frappe._dict(total_leave_days=2)]

		with patch.object(annual_leave_module.frappe, "get_all", side_effect=fake_get_all):
			total = annual_leave_module._get_taken_annual_leave_days("EMP-0001", 2026)

		self.assertEqual(total, 7)
		self.assertEqual(
			calls[1][1]["filters"]["leave_type"][1],
			list(annual_leave_module.ANNUAL_LEAVE_TYPE_CANDIDATES),
		)