import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate


class EmployeeGrievance(Document):

	def validate(self):
		self._protect_employee_scope()
		self._set_response_due_date()
		self._validate_dates()
		self._sync_status()

	def _set_response_due_date(self):
		if self.grievance_date and not self.response_due_date:
			self.response_due_date = add_days(self.grievance_date, 5)

	def _validate_dates(self):
		if self.response_due_date and self.grievance_date:
			if getdate(self.response_due_date) < getdate(self.grievance_date):
				frappe.throw(_("Response Due Date cannot be before Grievance Date"))

		if self.first_response_date and self.grievance_date:
			if getdate(self.first_response_date) < getdate(self.grievance_date):
				frappe.throw(_("First Response Date cannot be before Grievance Date"))

		if self.resolution_date and self.first_response_date:
			if getdate(self.resolution_date) < getdate(self.first_response_date):
				frappe.throw(_("Resolution Date cannot be before First Response Date"))

	def _sync_status(self):
		if self.resolution_date:
			self.status = "Resolved / محلولة"
		elif self.first_response_date:
			self.status = "In Review / قيد المراجعة"

	def _protect_employee_scope(self):
		roles = set(frappe.get_roles())
		if frappe.session.user == "Administrator" or {"System Manager", "HR Manager", "HR User"}.intersection(roles):
			return
		employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user, "status": "Active"}, "name")
		if not employee:
			frappe.throw(_("Your user account is not linked to an active Employee record."), frappe.PermissionError)
		if self.employee and self.employee != employee:
			frappe.throw(_("You can create or update only your own grievance record."), frappe.PermissionError)
		self.employee = employee
