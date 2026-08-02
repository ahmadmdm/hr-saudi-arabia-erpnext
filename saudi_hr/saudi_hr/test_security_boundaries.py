from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from saudi_hr.saudi_hr.doctype.employee_loan.employee_loan import (
	approve_loan,
	approve_loan_disbursement,
	create_disbursement_journal_entry,
	reject_loan,
	request_loan_approval,
)
from saudi_hr.saudi_hr.test_support import make_qa_employee
from saudi_hr.saudi_hr.utils import (
	assert_employee_salary_access,
	can_access_complete_employee_file,
	get_active_contract,
)


class TestSecurityBoundaries(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.company = frappe.get_all("Company", pluck="name", limit_page_length=1)[0]

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		super().tearDown()

	def test_employee_loan_mutators_are_post_only(self):
		for method in (
			create_disbursement_journal_entry,
			request_loan_approval,
			approve_loan,
			reject_loan,
			approve_loan_disbursement,
		):
			self.assertEqual(
				frappe.allowed_http_methods_for_whitelisted_func[method],
				["POST"],
			)

	def test_employee_can_read_own_salary_but_not_another_employee_salary(self):
		employee = make_qa_employee(self.company, "salary-owner")
		other_employee = make_qa_employee(self.company, "salary-other")
		frappe.set_user(frappe.db.get_value("Employee", employee, "user_id"))

		self.assertTrue(assert_employee_salary_access(employee))
		with self.assertRaises(frappe.PermissionError):
			assert_employee_salary_access(other_employee)

	def test_complete_file_requires_privileged_role(self):
		employee = make_qa_employee(self.company, "complete-file")
		frappe.set_user(frappe.db.get_value("Employee", employee, "user_id"))
		self.assertFalse(can_access_complete_employee_file(employee))


class TestEmploymentContractLifecycle(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.company = frappe.get_all("Company", pluck="name", limit_page_length=1)[0]
		self.employee = make_qa_employee(self.company, "contract-lifecycle")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		super().tearDown()

	def _contract(self, start_date, end_date):
		return frappe.get_doc(
			{
				"doctype": "Saudi Employment Contract",
				"employee": self.employee,
				"company": self.company,
				"contract_type": "محدد المدة / Fixed Term",
				"contract_status": "Draft / مسودة",
				"start_date": start_date,
				"end_date": end_date,
				"basic_salary": 10000,
			}
		).insert(ignore_permissions=True)

	def test_current_contract_is_submitted_and_effective(self):
		current = self._contract(add_days(nowdate(), -30), add_days(nowdate(), 30))
		current.submit()
		future = self._contract(add_days(nowdate(), 31), add_days(nowdate(), 365))
		future.submit()

		self.assertEqual(current.contract_status, "Active / نشط")
		self.assertEqual(future.contract_status, "Scheduled / مجدول")
		self.assertEqual(get_active_contract(self.employee, ["name"]).name, current.name)

	def test_overlapping_submitted_contract_is_rejected(self):
		first = self._contract(add_days(nowdate(), -30), add_days(nowdate(), 30))
		first.submit()
		overlap = self._contract(add_days(nowdate(), 20), add_days(nowdate(), 60))

		with self.assertRaises(frappe.ValidationError):
			overlap.submit()
