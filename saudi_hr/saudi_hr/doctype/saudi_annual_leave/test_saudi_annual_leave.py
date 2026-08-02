from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr.doctype.saudi_annual_leave.saudi_annual_leave import SaudiAnnualLeave
from saudi_hr.saudi_hr.test_support import make_qa_employee


class TestSaudiAnnualLeave(FrappeTestCase):
	def test_employee_policy_is_consumed_and_snapshotted_on_request(self):
		frappe.set_user("Administrator")
		company = frappe.get_all("Company", pluck="name", limit_page_length=1)[0]
		employee = make_qa_employee(company, f"annual-policy-{frappe.generate_hash(length=6)}")
		department = frappe.get_doc(
			{
				"doctype": "Department",
				"department_name": f"Annual Policy QA {frappe.generate_hash(length=8)}",
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
				"policy_name": f"Annual Employee Policy {frappe.generate_hash(length=8)}",
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
					"doctype": "Saudi Annual Leave",
					"employee": employee,
					"company": company,
					"department": department,
					"leave_start_date": "2026-06-10",
					"leave_end_date": "2026-06-12",
				}
			).insert(ignore_permissions=True)

		self.assertEqual(leave.annual_entitlement_days, 26)
		self.assertEqual(leave.leave_policy, policy.name)
		self.assertEqual(leave.leave_policy_assignment, assignment.name)
		self.assertEqual(leave.entitlement_source, "Employee / موظف")
		self.assertTrue(leave.entitlement_resolved_on)

	def test_validate_rejects_cross_year_request(self):
		doc = frappe.get_doc({
			"doctype": "Saudi Annual Leave",
			"employee": "HR-EMP-00001",
			"leave_start_date": "2026-12-31",
			"leave_end_date": "2027-01-02",
		})

		with self.assertRaises(frappe.ValidationError):
			doc.validate()

	def test_validate_rejects_leave_before_joining_date(self):
		doc = frappe.get_doc({
			"doctype": "Saudi Annual Leave",
			"employee": "HR-EMP-00001",
			"leave_start_date": "2026-01-01",
			"leave_end_date": "2026-01-03",
		})

		with patch.object(
			SaudiAnnualLeave, "_set_status"
		), patch.object(
			SaudiAnnualLeave, "_calculate_days", wraps=doc._calculate_days
		), patch(
			"saudi_hr.saudi_hr.doctype.saudi_annual_leave.saudi_annual_leave.get_annual_leave_balance",
			return_value={"balance": 21},
		), patch.object(
			frappe.db, "get_value", return_value="2026-02-01"
		):
			with self.assertRaises(frappe.ValidationError):
				doc._calculate_days()
				doc._calculate_balance()
