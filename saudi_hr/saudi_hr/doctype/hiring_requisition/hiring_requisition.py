import frappe
from frappe import _
from frappe.model.document import Document


class HiringRequisition(Document):
	def validate(self):
		if not self.status:
			self.status = "Draft / مسودة"

		if not self.approval_status:
			self.approval_status = "Pending / معلق"

		if (self.open_positions or 0) <= 0:
			frappe.throw(_("Open positions must be greater than zero / يجب أن يكون عدد الشواغر أكبر من صفر"))

		if self.approval_status == "Approved / معتمد" and self.status == "Draft / مسودة":
			self.status = "Open / مفتوح"
