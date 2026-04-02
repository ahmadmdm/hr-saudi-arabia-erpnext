import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate

from saudi_hr.saudi_hr.utils import calculate_eosb_components, get_employee_basic_salary


class EndofServiceBenefit(Document):

	def validate(self):
		self._fetch_joining_date()
		self._calculate_eosb()

	def _fetch_joining_date(self):
		emp = frappe.get_doc("Employee", self.employee)
		self.joining_date = emp.date_of_joining

	def _calculate_eosb(self):
		if not self.joining_date or not self.termination_date:
			return

		details = calculate_eosb_components(
			self.joining_date,
			self.termination_date,
			self.last_basic_salary,
			self.termination_reason,
			self.eosb_deductions,
		)
		self.years_of_service = details["years_of_service"]
		self.eosb_years_1_5 = details["eosb_years_1_5"]
		self.eosb_years_above_5 = details["eosb_years_above_5"]
		self.eosb_gross = details["eosb_gross"]
		self.resignation_factor = details["resignation_factor"]
		self.resignation_factor_label = details["resignation_factor_label"]
		self.net_eosb = details["net_eosb"]
		self.calculation_notes = details["calculation_notes"]

	def on_submit(self):
		"""تحديث حالة الموظف عند الاعتماد — دائماً يُعيَّن إلى 'Left'."""
		frappe.db.set_value("Employee", self.employee, "status", "Left")


@frappe.whitelist()
def get_last_basic_salary(employee):
	"""Return the employee's latest basic salary for JS auto-fill."""
	return get_employee_basic_salary(employee)


@frappe.whitelist()
def calculate_eosb_preview(joining_date, termination_date, last_basic_salary,
		termination_reason, eosb_deductions=0):
	"""
	Standalone EOSB calculation for JS preview (mirrors _calculate_eosb logic).
	Returns a dict with all computed fields.
	"""
	details = calculate_eosb_components(
		joining_date,
		termination_date,
		last_basic_salary,
		termination_reason,
		eosb_deductions,
	)
	return details
