import frappe
from frappe.model.document import Document
from frappe import _


class DisciplinaryProcedure(Document):

    def validate(self):
        self._validate_dates()
        self._check_prior_warnings()

    def on_submit(self):
        if not self.penalty_type:
            frappe.throw(_("Penalty Type must be set before submitting (م.65 Saudi Labor Law)"))
        if not self.hr_manager_approval:
            frappe.throw(_("HR Manager Approval is required before submitting"))
        self.status = "Decision Issued / صدر القرار"
        self.db_set("status", self.status)

    def _validate_dates(self):
        if self.investigation_date and self.incident_date:
            if self.investigation_date < self.incident_date:
                frappe.throw(_("Investigation Date cannot be before Incident Date"))
        if self.penalty_start_date and self.penalty_end_date:
            if self.penalty_end_date < self.penalty_start_date:
                frappe.throw(_("Penalty End Date cannot be before Penalty Start Date"))
        if self.penalty_type and "Suspension" in self.penalty_type:
            if not self.penalty_days or self.penalty_days <= 0:
                frappe.throw(_("Penalty Days must be specified for Suspension (م.65)"))
            # م.65: suspension cannot exceed 5 days per month
            if self.penalty_days > 5:
                frappe.msgprint(
                    _("Warning: Saudi Labor Law م.65 limits single suspension to 5 days per month"),
                    indicator="orange",
                    title=_("Saudi Labor Law Warning")
                )

    def _check_prior_warnings(self):
        """Count prior warnings to enforce progressive discipline م.65"""
        if not self.employee or not self.penalty_type:
            return
        prior_count = frappe.db.count(
            "Disciplinary Procedure",
            filters={
                "employee": self.employee,
                "docstatus": 1,
                "name": ["!=", self.name or ""],
            }
        )
        if prior_count == 0 and self.penalty_type and "Termination" in self.penalty_type:
            frappe.msgprint(
                _(
                    "No prior disciplinary records found for this employee. "
                    "Saudi Labor Law م.65 requires progressive discipline before termination."
                ),
                indicator="orange",
                title=_("Progressive Discipline Warning")
            )


@frappe.whitelist()
def get_prior_warnings(employee):
    """Return count and list of prior disciplinary records for an employee"""
    records = frappe.get_all(
        "Disciplinary Procedure",
        filters={"employee": employee, "docstatus": 1},
        fields=["name", "incident_date", "violation_type", "penalty_type", "status"],
        order_by="incident_date desc",
        limit=10,
    )
    return {"count": len(records), "records": records}
