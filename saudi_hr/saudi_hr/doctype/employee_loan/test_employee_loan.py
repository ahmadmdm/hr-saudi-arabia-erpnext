from datetime import date
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr.doctype.employee_loan import employee_loan as loan_module


class TestEmployeeLoan(FrappeTestCase):
	def test_build_installment_plan_equal_installments_balances_last_row(self):
		rows = loan_module._build_installment_plan(
			1000,
			"Equal Installments / أقساط متساوية",
			3,
			0,
			date(2026, 1, 1),
		)

		self.assertEqual(len(rows), 3)
		self.assertEqual(rows[0]["installment_amount"], 333.33)
		self.assertEqual(rows[1]["installment_amount"], 333.33)
		self.assertEqual(rows[2]["installment_amount"], 333.34)

	def test_build_installment_plan_fixed_installment_creates_final_partial_row(self):
		rows = loan_module._build_installment_plan(
			950,
			"Fixed Installment Amount / قسط ثابت",
			0,
			300,
			date(2026, 1, 1),
		)

		self.assertEqual([row["installment_amount"] for row in rows], [300, 300, 300, 50])

	def test_get_due_loan_deduction_sums_outstanding_rows(self):
		fake_rows = [
			frappe._dict(loan_name="LOAN-1", installment_name="INST-1", installment_amount=250, outstanding_amount=250),
			frappe._dict(loan_name="LOAN-1", installment_name="INST-2", installment_amount=250, outstanding_amount=100),
		]
		with patch.object(loan_module.frappe.db, "sql", return_value=fake_rows):
			result = loan_module.get_due_loan_deduction("EMP-0001", 3, 2026)

		self.assertEqual(result["loan_deduction"], 350)
		self.assertEqual(result["installment_names"], ["INST-1", "INST-2"])
		self.assertEqual(result["loan_names"], ["LOAN-1"])