from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from saudi_hr.saudi_hr.employee_profile import (
	_days_remaining,
	_expiry_state,
	_latest_payroll,
	calculate_employee_readiness,
)


def _complete_context():
	return {
		"employee": {
			"name": "HR-EMP-QA",
			"employee_name": "Saudi HR QA Employee",
			"status": "Active",
			"department": "Operations",
			"designation": "Specialist",
			"branch": "Riyadh",
			"company_email": "employee.qa@example.com",
			"user_id": "employee.qa@example.com",
		},
		"user_enabled": True,
		"nationality": "Saudi / سعودي",
		"contract": {
			"name": "CONTRACT-QA",
			"end_date": add_days(nowdate(), 365),
		},
		"permit": None,
		"attendance_setup": {
			"location": "Riyadh HQ",
			"shift_type": "Day Shift",
		},
		"leave": {
			"assignment": "LEAVE-ASSIGNMENT-QA",
			"policy_name": "Saudi Standard",
			"source_type": "Employee / موظف",
		},
		"visibility": {
			"contract": True,
			"permit": True,
			"leave": True,
			"attendance_setup": True,
		},
	}


class TestEmployeeProfile(FrappeTestCase):
	def test_latest_payroll_aggregates_all_employee_cost_center_rows(self):
		parent = frappe._dict({
			"name": "PAY-2026-08",
			"company": "Test Company",
			"period_label": "August 2026",
			"month": "August",
			"year": 2026,
			"posting_date": "2026-08-31",
			"status": "Draft / مسودة",
			"payroll_journal_entry": None,
			"docstatus": 0,
		})
		rows = [
			frappe._dict({
				"cost_center": "Riyadh",
				"basic_salary": 3000,
				"housing_allowance": 500,
				"transport_allowance": 200,
				"other_allowances": 0,
				"gross_salary": 3700,
				"gosi_employee_deduction": 300,
				"sick_leave_deduction": 0,
				"loan_deduction": 0,
				"absence_deduction": 0,
				"late_deduction": 0,
				"penalty_deduction": 0,
				"advance_deduction": 0,
				"other_deductions": 0,
				"total_deductions": 300,
				"overtime_addition": 0,
				"net_salary": 3400,
				"salary_mode": "Bank",
			}),
			frappe._dict({
				"cost_center": "Jeddah",
				"basic_salary": 1000,
				"housing_allowance": 0,
				"transport_allowance": 0,
				"other_allowances": 0,
				"gross_salary": 1000,
				"gosi_employee_deduction": 0,
				"sick_leave_deduction": 0,
				"loan_deduction": 0,
				"absence_deduction": 0,
				"late_deduction": 0,
				"penalty_deduction": 0,
				"advance_deduction": 250,
				"other_deductions": 0,
				"total_deductions": 250,
				"overtime_addition": 500,
				"net_salary": 1250,
				"salary_mode": "Bank",
			}),
		]

		with patch("saudi_hr.saudi_hr.employee_profile._can_read", return_value=True), patch(
			"saudi_hr.saudi_hr.employee_profile._doctype_exists", return_value=True
		), patch("saudi_hr.saudi_hr.employee_profile.frappe.get_list", return_value=[parent]), patch(
			"saudi_hr.saudi_hr.employee_profile.frappe.get_all", return_value=rows
		), patch("saudi_hr.saudi_hr.employee_profile.frappe.db.get_value", return_value="SAR"):
			result = _latest_payroll("EMP-1", "Test Company")

		self.assertEqual(result["row_count"], 2)
		self.assertEqual(result["gross_salary"], 4700)
		self.assertEqual(result["overtime_addition"], 500)
		self.assertEqual(result["advance_deduction"], 250)
		self.assertEqual(result["total_deductions"], 550)
		self.assertEqual(result["net_salary"], 4650)
		self.assertEqual(len(result["allocations"]), 2)
		self.assertFalse(result["paid"])

	def test_expiry_helpers_have_stable_boundaries(self):
		self.assertEqual(_days_remaining("2026-02-01", "2026-01-31"), 1)
		self.assertEqual(_expiry_state("2026-01-30", "2026-01-31"), "expired")
		self.assertEqual(_expiry_state("2026-03-31", "2026-01-31"), "expiring")
		self.assertEqual(_expiry_state("2026-04-02", "2026-01-31"), "valid")
		self.assertEqual(_expiry_state(None, "2026-01-31"), "missing")

	def test_complete_saudi_profile_is_ready_without_permit(self):
		result = calculate_employee_readiness(_complete_context())

		self.assertEqual(result["score"], 100)
		self.assertEqual(result["state"], "ready")
		self.assertFalse(result["attention"])
		permit_check = next(row for row in result["checks"] if row["code"] == "permit")
		self.assertEqual(permit_check["status"], "not_applicable")

	def test_expired_expat_permit_requires_action(self):
		context = _complete_context()
		context["nationality"] = "India"
		context["permit"] = {
			"name": "PERMIT-QA",
			"iqama_expiry_date": add_days(nowdate(), -1),
			"work_permit_expiry_date": add_days(nowdate(), 180),
		}

		result = calculate_employee_readiness(context)

		self.assertEqual(result["state"], "review")
		permit_check = next(row for row in result["checks"] if row["code"] == "permit")
		self.assertEqual(permit_check["status"], "action")
		self.assertIn(permit_check, result["attention"])

	def test_hidden_sensitive_sections_do_not_reduce_score(self):
		context = _complete_context()
		context["nationality"] = "India"
		context["contract"] = None
		context["permit"] = None
		context["visibility"]["contract"] = False
		context["visibility"]["permit"] = False

		result = calculate_employee_readiness(context)

		self.assertEqual(result["score"], 100)
		self.assertEqual(result["state"], "ready")
		self.assertEqual(
			{row["code"]: row["status"] for row in result["checks"] if row["code"] in {"contract", "permit"}},
			{"contract": "hidden", "permit": "hidden"},
		)

	def test_missing_operational_setup_is_prioritized(self):
		context = _complete_context()
		context["employee"]["branch"] = None
		context["employee"]["company_email"] = None
		context["employee"]["user_id"] = None
		context["user_enabled"] = False
		context["attendance_setup"] = {}
		context["leave"] = {}

		result = calculate_employee_readiness(context)

		self.assertEqual(result["state"], "incomplete")
		self.assertLess(result["score"], 70)
		self.assertTrue(
			{"profile_details", "user_access", "leave_policy", "attendance_setup"}.issubset(
				{row["code"] for row in result["attention"]}
			)
		)
