from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr import utils


class TestAnnualLeaveDisbursement(FrappeTestCase):
	def test_get_annual_leave_days_taken_reads_saudi_annual_leave(self):
		with patch.object(
			utils.frappe,
			"get_all",
			return_value=[frappe._dict(total_leave_days=5), frappe._dict(total_leave_days=2.5)],
		):
			total = utils.get_annual_leave_days_taken("EMP-0001", 2026)

		self.assertEqual(total, 7.5)