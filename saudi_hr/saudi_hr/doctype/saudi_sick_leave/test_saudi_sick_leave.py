# Copyright (c) 2026, IdeaOrbit and Contributors
# See license.txt

from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr.doctype.saudi_sick_leave.saudi_sick_leave import (
	SaudiSickLeave,
	calculate_sick_leave_cycle,
	calculate_sick_leave_pay_breakdown,
)
from saudi_hr.saudi_hr.test_support import make_qa_employee


class TestSaudiSickLeave(FrappeTestCase):
	def test_employee_policy_is_consumed_and_snapshotted_on_request(self):
		frappe.set_user("Administrator")
		company = frappe.get_all("Company", pluck="name", limit_page_length=1)[0]
		employee = make_qa_employee(company, f"sick-policy-{frappe.generate_hash(length=6)}")
		department = frappe.get_doc(
			{
				"doctype": "Department",
				"department_name": f"Sick Policy QA {frappe.generate_hash(length=8)}",
				"company": company,
				"is_group": 0,
			}
		).insert(ignore_permissions=True).name
		frappe.db.set_value(
			"Employee",
			employee,
			{"department": department, "date_of_joining": "2024-01-01"},
		)
		policy = frappe.get_doc(
			{
				"doctype": "Saudi Leave Policy",
				"policy_name": f"Sick Employee Policy {frappe.generate_hash(length=8)}",
				"company": company,
				"enabled": 1,
				"annual_leave_years_threshold": 5,
				"annual_leave_before_threshold": 26,
				"annual_leave_after_threshold": 36,
				"sick_leave_full_pay_days": 40,
				"sick_leave_partial_pay_days": 50,
				"sick_leave_partial_pay_percentage": 80,
			}
		).insert(ignore_permissions=True)
		assignment = frappe.get_doc(
			{
				"doctype": "Saudi Leave Policy Assignment",
				"policy": policy.name,
				"company": company,
				"applies_to": "Employee / موظف",
				"employee": employee,
				"effective_from": "2026-01-01",
				"effective_to": "2026-12-31",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

		with patch("frappe.workflow.doctype.workflow_action.workflow_action.frappe.attach_print"):
			leave = frappe.get_doc(
				{
					"doctype": "Saudi Sick Leave",
					"employee": employee,
					"company": company,
					"department": department,
					"from_date": "2026-06-01",
					"to_date": "2026-07-05",
					"medical_certificate_attached": 1,
				}
			).insert(ignore_permissions=True)

		self.assertEqual(leave.full_pay_days, 35)
		self.assertEqual(leave.partial_pay_days, 0)
		self.assertEqual(leave.policy_full_pay_days, 40)
		self.assertEqual(leave.policy_partial_pay_days, 50)
		self.assertEqual(leave.policy_partial_pay_percentage, 80)
		self.assertEqual(leave.leave_policy, policy.name)
		self.assertEqual(leave.leave_policy_assignment, assignment.name)
		self.assertEqual(leave.entitlement_source, "Employee / موظف")
		self.assertTrue(leave.entitlement_resolved_on)

	def test_cycle_crosses_calendar_year_from_first_sick_leave(self):
		prior = [
			SimpleNamespace(from_date="2025-12-20", to_date="2026-01-10", total_days=22),
			SimpleNamespace(from_date="2026-03-01", to_date="2026-03-05", total_days=5),
		]

		result = calculate_sick_leave_cycle("2026-05-01", prior)

		self.assertEqual(str(result["cycle_start"]), "2025-12-20")
		self.assertEqual(str(result["cycle_end"]), "2026-12-19")
		self.assertEqual(result["used_days"], 27)

	def test_expired_cycle_restarts_on_next_sick_leave(self):
		prior = [SimpleNamespace(from_date="2025-01-01", to_date="2025-01-30", total_days=30)]

		result = calculate_sick_leave_cycle("2026-02-01", prior)

		self.assertEqual(str(result["cycle_start"]), "2026-02-01")
		self.assertEqual(str(result["cycle_end"]), "2027-01-31")
		self.assertEqual(result["used_days"], 0)

	def test_request_can_span_full_and_partial_pay_tiers(self):
		result = calculate_sick_leave_pay_breakdown(25, 10, 100)

		self.assertEqual(result["full_pay_days"], 5)
		self.assertEqual(result["partial_pay_days"], 5)
		self.assertEqual(result["unpaid_days"], 0)
		self.assertEqual(result["amount"], 875)
		self.assertEqual(result["effective_rate"], 87.5)
		self.assertEqual(result["label"], "Mixed Statutory Tiers / شرائح نظامية مختلطة")

	def test_request_can_span_partial_and_unpaid_tiers(self):
		result = calculate_sick_leave_pay_breakdown(85, 10, 100)

		self.assertEqual(result["partial_pay_days"], 5)
		self.assertEqual(result["unpaid_days"], 5)
		self.assertEqual(result["amount"], 375)
		self.assertEqual(result["effective_rate"], 37.5)

	def test_days_after_ninety_are_unpaid_without_automatic_termination(self):
		result = calculate_sick_leave_pay_breakdown(90, 30, 100)

		self.assertEqual(result["full_pay_days"], 0)
		self.assertEqual(result["partial_pay_days"], 0)
		self.assertEqual(result["unpaid_days"], 30)
		self.assertEqual(result["amount"], 0)

	@patch("saudi_hr.saudi_hr.doctype.saudi_sick_leave.saudi_sick_leave.frappe.throw", side_effect=ValueError)
	@patch("saudi_hr.saudi_hr.doctype.saudi_sick_leave.saudi_sick_leave.frappe.db.exists", return_value="SAU-SL-2026-0001")
	def test_overlapping_request_is_rejected(self, _exists, _throw):
		doc = SimpleNamespace(
			employee="EMP-DEMO-001",
			from_date="2026-07-01",
			to_date="2026-07-05",
			name=None,
		)

		with self.assertRaises(ValueError):
			SaudiSickLeave._validate_no_overlap(doc)
