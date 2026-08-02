from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate

from saudi_hr.saudi_hr.report.saudi_leave_balance_report import saudi_leave_balance_report as report_module


class TestSaudiLeaveBalanceReport(FrappeTestCase):
	def test_report_opens_without_filters(self):
		columns, data = report_module.execute({})

		self.assertTrue(columns)
		self.assertIsInstance(data, list)

	@patch.object(report_module, "get_annual_leave_balance")
	@patch.object(report_module.frappe.db, "sql")
	def test_report_exposes_resolved_policy_snapshot_for_as_of_date(self, db_sql, get_balance):
		db_sql.return_value = [
			frappe._dict(
				employee="EMP-POLICY-001",
				employee_name="موظف سياسة",
				department="Human Resources - QA",
				date_of_joining="2024-01-01",
				company="QA Company",
			)
		]
		get_balance.return_value = {
			"entitled": 26,
			"taken": 4,
			"balance": 22,
			"years_of_service": 2.42,
			"policy": "Saudi Leave Policy QA",
			"policy_name": "سياسة إجازات الموظف",
			"source_type": "Employee / موظف",
			"assignment": "SLPA-QA-0001",
		}

		data = report_module.get_data({"as_of_date": "2026-06-01"})

		self.assertEqual(len(data), 1)
		self.assertEqual(data[0]["entitlement"], 26)
		self.assertEqual(data[0]["leave_policy"], "Saudi Leave Policy QA")
		self.assertEqual(data[0]["policy_name"], "سياسة إجازات الموظف")
		self.assertEqual(data[0]["policy_source"], "Employee / موظف")
		self.assertEqual(data[0]["policy_assignment"], "SLPA-QA-0001")
		get_balance.assert_called_once_with("EMP-POLICY-001", getdate("2026-06-01"))
