import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class LegalReferenceMatrix(Document):

	def validate(self):
		if self.next_review_date and self.effective_from:
			if getdate(self.next_review_date) < getdate(self.effective_from):
				frappe.throw(_("Next Review Date cannot be before Effective From"))

		if self.status == "Retired / متقاعد" and not self.retirement_reason:
			frappe.throw(_("Retirement Reason is required when the reference is retired"))