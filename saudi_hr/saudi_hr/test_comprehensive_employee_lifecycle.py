from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days

from saudi_hr.saudi_hr.test_support import (
	get_or_create_department,
	get_or_create_designation,
	make_qa_employee,
	select_option,
)


class TestComprehensiveEmployeeLifecycle(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.workflow_enqueue_patcher = patch("frappe.workflow.doctype.workflow_action.workflow_action.enqueue")
		self.workflow_enqueue_patcher.start()
		frappe.set_user("Administrator")
		self.company = frappe.get_all("Company", pluck="name", limit_page_length=1)[0]
		self.department = get_or_create_department(self.company)
		self.employee = make_qa_employee(self.company, "lifecycle")

	def tearDown(self):
		frappe.set_user("Administrator")
		self.workflow_enqueue_patcher.stop()
		frappe.db.rollback()
		super().tearDown()

	def test_recruitment_candidate_and_onboarding_cycle(self):
		requisition = frappe.get_doc(
			{
				"doctype": "Hiring Requisition",
				"requisition_title": "Saudi payroll specialist",
				"company": self.company,
				"department": self.department,
				"employment_type": select_option("Hiring Requisition", "employment_type", "Full Time"),
				"open_positions": 1,
			}
		).insert(ignore_permissions=True)
		self.assertIn("Draft", requisition.status)
		self.assertIn("Pending", requisition.approval_status)

		requisition.approval_status = select_option("Hiring Requisition", "approval_status", "Approved")
		requisition.save(ignore_permissions=True)
		self.assertIn("Open", requisition.status)

		invalid_requisition = frappe.copy_doc(requisition)
		invalid_requisition.open_positions = 0
		with self.assertRaises(frappe.ValidationError):
			invalid_requisition.insert(ignore_permissions=True)

		candidate = frappe.get_doc(
			{
				"doctype": "Candidate Profile",
				"candidate_name": "Fahad Alqahtani",
				"hiring_requisition": requisition.name,
				"email": "fahad.qa@example.com",
			}
		).insert(ignore_permissions=True)
		self.assertIn("Applied", candidate.status)
		candidate.linked_employee = self.employee
		candidate.save(ignore_permissions=True)
		self.assertIn("Onboarded", candidate.status)

		onboarding = frappe.get_doc(
			{
				"doctype": "Employee Onboarding",
				"employee": self.employee,
				"company": self.company,
				"government_registration_completed": 1,
				"medical_exam_completed": 1,
				"policy_acknowledged": 1,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(onboarding.completion_percentage, 50)
		self.assertIn("In Progress", onboarding.status)

		for fieldname in onboarding.CHECKLIST_FIELDS:
			onboarding.set(fieldname, 1)
		onboarding.save(ignore_permissions=True)
		self.assertEqual(onboarding.completion_percentage, 100)
		self.assertIn("Completed", onboarding.status)

	def test_contract_performance_salary_and_movement_cycle(self):
		contract = frappe.get_doc(
			{
				"doctype": "Saudi Employment Contract",
				"employee": self.employee,
				"company": self.company,
				"contract_type": select_option("Saudi Employment Contract", "contract_type", "Fixed Term"),
				"start_date": "2026-01-01",
				"end_date": "2026-12-31",
				"probation_period_days": 90,
				"extended_probation_days": 30,
				"basic_salary": 8000,
				"housing_allowance": 2000,
				"transport_allowance": 750,
				"other_allowances": 250,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(contract.total_salary, 11000)
		self.assertEqual(str(contract.probation_end_date), "2026-05-01")

		invalid_contract = frappe.copy_doc(contract)
		invalid_contract.probation_period_days = 150
		invalid_contract.extended_probation_days = 31
		with self.assertRaises(frappe.ValidationError):
			invalid_contract.insert(ignore_permissions=True)

		review = frappe.get_doc(
			{
				"doctype": "Performance Review",
				"employee": self.employee,
				"company": self.company,
				"review_type": select_option("Performance Review", "review_type", "Annual"),
				"review_period_start": "2026-01-01",
				"review_period_end": "2026-12-31",
				"attendance_rating": 4,
				"compliance_rating": 5,
				"productivity_rating": 4,
				"collaboration_rating": 3,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(review.overall_rating, 4)
		self.assertIn("Completed", review.status)

		invalid_review = frappe.copy_doc(review)
		invalid_review.attendance_rating = 6
		with self.assertRaises(frappe.ValidationError):
			invalid_review.insert(ignore_permissions=True)

		adjustment = frappe.get_doc(
			{
				"doctype": "Salary Adjustment",
				"employee": self.employee,
				"company": self.company,
				"performance_review": review.name,
				"effective_date": "2027-01-01",
				"adjustment_type": select_option("Salary Adjustment", "adjustment_type", "Merit"),
				"current_basic_salary": 8000,
				"proposed_basic_salary": 8800,
				"business_justification": "Annual performance cycle",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(adjustment.adjustment_amount, 800)
		self.assertEqual(adjustment.adjustment_percentage, 10)
		review.reload()
		self.assertEqual(review.salary_adjustment, adjustment.name)

		invalid_adjustment = frappe.copy_doc(adjustment)
		invalid_adjustment.current_basic_salary = -1
		invalid_adjustment.proposed_basic_salary = 0
		with self.assertRaises(frappe.ValidationError):
			invalid_adjustment.insert(ignore_permissions=True)

		current_designation = get_or_create_designation("Saudi QA Specialist")
		new_designation = get_or_create_designation("Saudi QA Senior Specialist")
		employee_doc = frappe.get_doc("Employee", self.employee)
		employee_doc.designation = current_designation
		employee_doc.save(ignore_permissions=True)
		movement = frappe.get_doc(
			{
				"doctype": "Promotion Transfer",
				"employee": self.employee,
				"company": self.company,
				"performance_review": review.name,
				"movement_type": select_option("Promotion Transfer", "movement_type", "Promotion /"),
				"effective_date": "2027-01-01",
				"current_designation": current_designation,
				"new_designation": new_designation,
				"business_justification": "Promotion after completed annual review",
			}
		).insert(ignore_permissions=True)
		review.reload()
		self.assertEqual(review.promotion_transfer, movement.name)
		self.assertTrue(review.promotion_recommended)

		invalid_movement = frappe.get_doc(
			{
				"doctype": "Promotion Transfer",
				"employee": self.employee,
				"company": self.company,
				"movement_type": select_option("Promotion Transfer", "movement_type", "Promotion /"),
				"effective_date": "2027-01-01",
				"current_designation": current_designation,
				"new_designation": current_designation,
				"business_justification": "Invalid same-designation promotion",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			invalid_movement.insert(ignore_permissions=True)

	def test_termination_interview_and_clearance_cycle(self):
		termination = frappe.get_doc(
			{
				"doctype": "Termination Notice",
				"employee": self.employee,
				"company": self.company,
				"termination_reason": select_option("Termination Notice", "termination_reason", "Resignation"),
				"salary_payment_type": select_option("Termination Notice", "salary_payment_type", "Monthly"),
				"notice_start_date": "2026-07-01",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(termination.notice_required_days, 60)
		self.assertEqual(str(termination.notice_end_date), str(add_days("2026-07-01", 60)))
		self.assertTrue(termination.eosb_applicable)
		termination.flags.ignore_permissions = True
		termination.flags.ignore_workflow = True
		termination.submit()
		settlement_name = frappe.db.get_value(
			"Final Settlement SLA", {"termination_notice": termination.name}, "name"
		)
		self.assertTrue(settlement_name)
		settlement = frappe.get_doc("Final Settlement SLA", settlement_name)
		self.assertEqual(str(settlement.settlement_due_date), str(add_days(termination.notice_end_date, 14)))
		self.assertEqual(str(settlement.document_return_due_date), str(settlement.settlement_due_date))

		eosb = frappe.get_doc(
			{
				"doctype": "End of Service Benefit",
				"employee": self.employee,
				"company": self.company,
				"termination_date": termination.notice_end_date,
				"termination_reason": select_option("End of Service Benefit", "termination_reason", "Resignation"),
				"last_basic_salary": 8000,
			}
		).insert(ignore_permissions=True)
		self.assertGreaterEqual(eosb.net_eosb, 0)
		eosb.flags.ignore_permissions = True
		eosb.submit()
		self.assertEqual(frappe.db.get_value("Employee", self.employee, "status"), "Left")
		settlement.eosb_document = eosb.name
		settlement.save(ignore_permissions=True)
		self.assertEqual(settlement.eosb_document, eosb.name)

		probation_termination = frappe.get_doc(
			{
				"doctype": "Termination Notice",
				"employee": self.employee,
				"company": self.company,
				"termination_reason": select_option("Termination Notice", "termination_reason", "Resignation"),
				"salary_payment_type": select_option("Termination Notice", "salary_payment_type", "Monthly"),
				"notice_start_date": "2026-07-01",
				"during_probation": 1,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(probation_termination.notice_required_days, 0)

		clearance = frappe.get_doc(
			{
				"doctype": "Exit Clearance",
				"employee": self.employee,
				"company": self.company,
				"termination_notice": termination.name,
				"access_revoked": 1,
				"assets_returned": 1,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(clearance.clearance_percentage, 25)
		self.assertIn("In Progress", clearance.status)

		interview = frappe.get_doc(
			{
				"doctype": "Exit Interview",
				"employee": self.employee,
				"company": self.company,
				"termination_notice": termination.name,
				"exit_clearance": clearance.name,
				"interview_date": "2026-08-30",
				"status": select_option("Exit Interview", "status", "Completed"),
			}
		).insert(ignore_permissions=True)
		clearance.reload()
		self.assertTrue(clearance.exit_interview_completed)

		clearance.exit_interview = interview.name
		for fieldname in clearance.CHECKLIST_FIELDS:
			clearance.set(fieldname, 1)
		clearance.save(ignore_permissions=True)
		self.assertEqual(clearance.clearance_percentage, 100)
		self.assertIn("Cleared", clearance.status)

		other_employee = make_qa_employee(self.company, "other-exit")
		invalid_interview = frappe.copy_doc(interview)
		invalid_interview.employee = other_employee
		with self.assertRaises(frappe.ValidationError):
			invalid_interview.insert(ignore_permissions=True)
