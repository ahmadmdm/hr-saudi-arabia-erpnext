import frappe
from frappe.model.document import Document


class CandidateProfile(Document):
	def validate(self):
		if not self.status:
			self.status = "Applied / تم التقديم"

		if self.linked_employee and self.status not in ("Onboarded / تم التعيين", "Accepted / مقبول"):
			self.status = "Onboarded / تم التعيين"
