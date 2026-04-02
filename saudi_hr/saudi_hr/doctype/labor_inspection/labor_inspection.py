import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from saudi_hr.saudi_hr.utils import assert_doctype_permissions


OPEN_VIOLATION_STATUSES = {
	"Open / مفتوح",
	"Under Review / قيد المراجعة",
	"Corrective Action In Progress / التصحيح جارٍ",
}


class LaborInspection(Document):

	def validate(self):
		self._validate_required_rows()
		self._validate_dates()
		self._sync_violation_rows()
		self._update_totals()
		self._sync_status()

	def on_submit(self):
		self._create_compliance_actions()
		self._sync_status(persist=True)

	def _validate_required_rows(self):
		if not self.violations:
			frappe.throw(_("At least one violation row is required"))

	def _validate_dates(self):
		if self.follow_up_due_date and self.inspection_date and getdate(self.follow_up_due_date) < getdate(self.inspection_date):
			frappe.throw(_("Follow-up Due Date cannot be before Inspection Date"))

		if self.closure_date and self.inspection_date and getdate(self.closure_date) < getdate(self.inspection_date):
			frappe.throw(_("Closure Date cannot be before Inspection Date"))

		for row in self.violations:
			if row.correction_due_date and getdate(row.correction_due_date) < getdate(self.inspection_date):
				frappe.throw(_("Correction Due Date cannot be before Inspection Date in row {0}").format(row.idx))
			if row.resolved_on and getdate(row.resolved_on) < getdate(self.inspection_date):
				frappe.throw(_("Resolved On cannot be before Inspection Date in row {0}").format(row.idx))

	def _sync_violation_rows(self):
		for row in self.violations:
			if row.resolved_on and row.status in OPEN_VIOLATION_STATUSES:
				row.status = "Corrected / تم التصحيح"

	def _update_totals(self):
		self.total_violations = len(self.violations)
		self.open_violations = sum(1 for row in self.violations if row.status in OPEN_VIOLATION_STATUSES)
		self.total_fines = sum(flt(row.fine_amount) for row in self.violations)

	def _sync_status(self, persist=False):
		if self.closure_date:
			status = "Closed / مغلق"
		elif self.open_violations:
			status = "Under Follow-up / قيد المتابعة" if any(row.action_log for row in self.violations) else "Open Findings / مخالفات مفتوحة"
		elif self.total_violations:
			status = "Corrected / تم التصحيح"
		else:
			status = "Draft / مسودة"

		self.status = status
		if persist and self.name:
			self.db_set("status", status)

	def _create_compliance_actions(self):
		for row in self.violations:
			if row.status not in OPEN_VIOLATION_STATUSES:
				continue
			if row.action_log and frappe.db.exists("HR Compliance Action Log", row.action_log):
				continue

			action = frappe.get_doc(
				{
					"doctype": "HR Compliance Action Log",
					"action_title": _("Inspection {0}: {1}").format(self.name, row.violation_category),
					"compliance_area": "Government Relations / العلاقات الحكومية",
					"company": self.company,
					"action_date": self.inspection_date,
					"assigned_to": self.internal_owner,
					"due_date": row.correction_due_date or self.follow_up_due_date,
					"reference_doctype": "Labor Inspection",
					"reference_name": self.name,
					"description": row.violation_description,
					"corrective_action": row.corrective_action,
				}
			)
			assert_doctype_permissions("HR Compliance Action Log", "create", doc=action)
			action.insert()
			frappe.db.set_value("Labor Inspection Violation", row.name, "action_log", action.name, update_modified=False)
			row.action_log = action.name