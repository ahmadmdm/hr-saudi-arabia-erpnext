import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from saudi_hr.saudi_hr.utils import LEAVE_SCOPE_DEPARTMENT, LEAVE_SCOPE_EMPLOYEE


class SaudiLeavePolicyAssignment(Document):
	def validate(self):
		self._load_policy_company()
		self._validate_scope_and_target()
		self._validate_effective_period()
		self._validate_no_overlap()

	def _load_policy_company(self):
		if not self.policy:
			frappe.throw(
				_("Select a leave policy.<br>اختر سياسة إجازات."),
				title=_("Leave Policy Required / سياسة الإجازات مطلوبة"),
			)
		policy = frappe.db.get_value(
			"Saudi Leave Policy",
			self.policy,
			["company", "enabled"],
			as_dict=True,
		)
		if not policy:
			frappe.throw(
				_("Leave policy {0} was not found.<br>لم يتم العثور على سياسة الإجازات {0}.").format(
					frappe.bold(self.policy)
				),
				title=_("Missing Leave Policy / سياسة الإجازات غير موجودة"),
			)
		if self.enabled and not policy.enabled:
			frappe.throw(
				_("Enable the selected leave policy before activating its assignment.<br>فعّل سياسة الإجازات المحددة قبل تفعيل تعيينها."),
				title=_("Disabled Leave Policy / سياسة إجازات معطلة"),
			)
		self.company = policy.company

	def _validate_scope_and_target(self):
		if self.applies_to == LEAVE_SCOPE_EMPLOYEE:
			if not self.employee:
				frappe.throw(
					_("Select an employee for this assignment.<br>اختر موظفًا لهذا التعيين."),
					title=_("Employee Required / الموظف مطلوب"),
				)
			self.department = None
			target_company = frappe.db.get_value("Employee", self.employee, "company")
			target_label = _("employee / الموظف")
		elif self.applies_to == LEAVE_SCOPE_DEPARTMENT:
			if not self.department:
				frappe.throw(
					_("Select a department for this assignment.<br>اختر قسمًا لهذا التعيين."),
					title=_("Department Required / القسم مطلوب"),
				)
			self.employee = None
			target_company = frappe.db.get_value("Department", self.department, "company")
			target_label = _("department / القسم")
		else:
			frappe.throw(
				_("Assignment scope must be Employee or Department.<br>يجب أن يكون نطاق التعيين موظفًا أو قسمًا."),
				title=_("Invalid Assignment Scope / نطاق تعيين غير صالح"),
			)

		if not target_company:
			frappe.throw(
				_("The selected {0} has no company or does not exist.<br>العنصر المحدد ({0}) غير موجود أو غير مرتبط بشركة.").format(
					target_label
				),
				title=_("Missing Company / الشركة غير موجودة"),
			)
		if target_company != self.company:
			frappe.throw(
				_("The selected {0} belongs to a different company than the leave policy.<br>العنصر المحدد ({0}) تابع لشركة مختلفة عن شركة سياسة الإجازات.").format(
					target_label
				),
				title=_("Company Mismatch / اختلاف الشركة"),
			)

	def _validate_effective_period(self):
		if not self.effective_from:
			frappe.throw(
				_("Effective From is required.<br>تاريخ بداية السريان مطلوب."),
				title=_("Effective Date Required / تاريخ السريان مطلوب"),
			)
		if self.effective_to and getdate(self.effective_to) < getdate(self.effective_from):
			frappe.throw(
				_("Effective To cannot be earlier than Effective From.<br>لا يمكن أن يكون تاريخ نهاية السريان قبل تاريخ بدايته."),
				title=_("Invalid Effective Period / فترة سريان غير صالحة"),
			)

	def _validate_no_overlap(self):
		if not self.enabled:
			return

		target_field = "employee" if self.applies_to == LEAVE_SCOPE_EMPLOYEE else "department"
		target = self.employee if target_field == "employee" else self.department
		filters = {
			"enabled": 1,
			"company": self.company,
			"applies_to": self.applies_to,
			target_field: target,
			"effective_from": ["<=", self.effective_to or "9999-12-31"],
		}
		if self.name:
			filters["name"] = ["!=", self.name]

		assignments = frappe.get_all(
			"Saudi Leave Policy Assignment",
			filters=filters,
			fields=["name", "effective_from", "effective_to"],
			order_by="effective_from asc",
			limit_page_length=100,
		)
		for assignment in assignments:
			if not assignment.effective_to or getdate(assignment.effective_to) >= getdate(self.effective_from):
				frappe.throw(
					_(
						"This assignment overlaps {0}. End or disable the existing assignment first.<br>"
						"يتداخل هذا التعيين مع {0}. أنهِ التعيين الحالي أو عطّله أولًا."
					).format(frappe.bold(assignment.name)),
					title=_("Overlapping Leave Policy Assignment / تداخل تعيين سياسة الإجازات"),
				)
