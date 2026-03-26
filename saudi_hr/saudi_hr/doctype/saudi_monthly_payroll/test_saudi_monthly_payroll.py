from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr.doctype.saudi_monthly_payroll import saudi_monthly_payroll as payroll_module


class TestSaudiMonthlyPayroll(FrappeTestCase):
	def test_build_employee_row_includes_loan_in_total_deductions(self):
		emp = {"name": "EMP-0001", "employee_name": "Demo Employee", "department": "HR", "nationality": "Saudi"}
		with patch.object(
			payroll_module, "get_employee_salary_components", return_value={
				"basic_salary": 1000,
				"housing_allowance": 200,
				"transport_allowance": 100,
				"other_allowances": 50,
			}
		), patch.object(payroll_module.frappe, "get_all", side_effect=[[], []]), patch.object(
			payroll_module, "get_due_loan_deduction", return_value={"loan_deduction": 125, "installment_names": ["INST-1"]}
		):
			row = payroll_module._build_employee_row(emp, "March / مارس", 2026)

		self.assertEqual(row["gross_salary"], 1350)
		self.assertEqual(row["gosi_employee_deduction"], 100)
		self.assertEqual(row["loan_deduction"], 125)
		self.assertEqual(row["total_deductions"], 225)
		self.assertEqual(row["net_salary"], 1125)
		self.assertEqual(row["loan_installments"], "INST-1")

	def test_recalculate_totals_includes_loan_and_sick_deductions(self):
		doc = frappe.get_doc({
			"doctype": "Saudi Monthly Payroll",
			"company": "amd",
			"month": "March / مارس",
			"year": 2026,
			"posting_date": "2026-03-31",
			"employees": [
				{"employee": "EMP-1", "gross_salary": 1000, "gosi_employee_deduction": 100, "sick_leave_deduction": 20, "loan_deduction": 50, "overtime_addition": 10, "net_salary": 840},
				{"employee": "EMP-2", "gross_salary": 1200, "gosi_employee_deduction": 120, "sick_leave_deduction": 0, "loan_deduction": 80, "overtime_addition": 0, "net_salary": 1000},
			],
		})

		doc._recalculate_totals()

		self.assertEqual(doc.total_employees, 2)
		self.assertEqual(doc.total_gross, 2200)
		self.assertEqual(doc.total_gosi_deductions, 220)
		self.assertEqual(doc.total_sick_deductions, 20)
		self.assertEqual(doc.total_loan_deductions, 130)
		self.assertEqual(doc.total_overtime, 10)
		self.assertEqual(doc.total_net_payable, 1840)