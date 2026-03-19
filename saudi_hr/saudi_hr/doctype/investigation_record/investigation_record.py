import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class InvestigationRecord(Document):

	def validate(self):
		if self.investigation_start_date and self.allegation_date:
			if getdate(self.investigation_start_date) < getdate(self.allegation_date):
				frappe.throw(_("Investigation Start Date cannot be before Allegation Date"))

		if self.investigation_end_date and self.investigation_start_date:
			if getdate(self.investigation_end_date) < getdate(self.investigation_start_date):
				frappe.throw(_("Investigation End Date cannot be before Investigation Start Date"))

		if self.closure_date and self.investigation_end_date:
			if getdate(self.closure_date) < getdate(self.investigation_end_date):
				frappe.throw(_("Closure Date cannot be before Investigation End Date"))

		if self.closure_date:
			self.status = "Closed / مغلق"
		elif self.investigation_end_date:
			self.status = "Findings Issued / صدرت النتائج"
		elif self.investigation_start_date:
			self.status = "In Progress / قيد التحقيق"