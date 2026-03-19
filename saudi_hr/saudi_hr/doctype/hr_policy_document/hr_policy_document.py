import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today


class HRPolicyDocument(Document):

	def validate(self):
		self._validate_dates()
		self._sync_status()

	def _validate_dates(self):
		if self.review_date and self.effective_date:
			if getdate(self.review_date) < getdate(self.effective_date):
				frappe.throw(_("Review Date cannot be before Effective Date"))

	def _sync_status(self):
		if self.status == "Archived / مؤرشف":
			return

		if self.review_date and getdate(self.review_date) < getdate(today()):
			self.status = "Under Review / قيد المراجعة"
		elif self.effective_date and getdate(self.effective_date) <= getdate(today()):
			self.status = "Active / سارية"
		else:
			self.status = self.status or "Draft / مسودة"