import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from saudi_hr.saudi_hr.utils import validate_leave_policy_values


class SaudiLeavePolicy(Document):
	def validate(self):
		self.policy_name = (self.policy_name or "").strip()
		if not self.policy_name:
			frappe.throw(
				_("Policy name is required.<br>اسم سياسة الإجازات مطلوب."),
				title=_("Missing Policy Name / اسم السياسة غير موجود"),
			)

		self.annual_leave_years_threshold = cint(self.annual_leave_years_threshold)
		self.annual_leave_before_threshold = cint(self.annual_leave_before_threshold)
		self.annual_leave_after_threshold = cint(self.annual_leave_after_threshold)
		self.sick_leave_full_pay_days = cint(self.sick_leave_full_pay_days)
		self.sick_leave_partial_pay_days = cint(self.sick_leave_partial_pay_days)
		self.sick_leave_partial_pay_percentage = flt(self.sick_leave_partial_pay_percentage)

		validate_leave_policy_values(
			self.annual_leave_years_threshold,
			self.annual_leave_before_threshold,
			self.annual_leave_after_threshold,
			self.sick_leave_full_pay_days,
			self.sick_leave_partial_pay_days,
			self.sick_leave_partial_pay_percentage,
		)

		duplicate = frappe.db.exists(
			"Saudi Leave Policy",
			{
				"company": self.company,
				"policy_name": self.policy_name,
				"name": ["!=", self.name],
			},
		)
		if duplicate:
			frappe.throw(
				_(
					"A leave policy named {0} already exists for this company.<br>"
					"توجد سياسة إجازات بالاسم {0} لهذه الشركة."
				).format(frappe.bold(self.policy_name)),
				title=_("Duplicate Leave Policy / سياسة إجازات مكررة"),
			)
