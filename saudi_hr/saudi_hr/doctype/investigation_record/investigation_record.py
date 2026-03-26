import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, today


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


@frappe.whitelist()
def create_warning_notice(record_name: str):
	record = frappe.get_doc("Investigation Record", record_name)
	if record.employee_warning_notice and frappe.db.exists("Employee Warning Notice", record.employee_warning_notice):
		return {"warning_notice": record.employee_warning_notice, "created": False}

	warning_notice = frappe.get_doc(
		{
			"doctype": "Employee Warning Notice",
			"employee": record.subject_employee,
			"company": record.company,
			"department": record.department,
			"warning_date": record.investigation_end_date or today(),
			"warning_level": "First Written Warning / إنذار كتابي أول",
			"investigation_record": record.name,
			"legal_reference_matrix": record.legal_reference_matrix,
			"issue_reason": record.allegation_summary,
			"corrective_action": record.recommendation,
			"due_date": add_days(record.investigation_end_date or today(), 7),
		}
	).insert(ignore_permissions=True)
	record.db_set("employee_warning_notice", warning_notice.name, update_modified=False)
	return {"warning_notice": warning_notice.name, "created": True}