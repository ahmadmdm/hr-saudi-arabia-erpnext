import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, flt, getdate, now_datetime, nowdate

from saudi_hr.saudi_hr.utils import get_annual_leave_balance


class SaudiAnnualLeave(Document):
	def validate(self):
		self._sync_employee_context()
		self._set_status()
		self._calculate_days()
		self._calculate_balance()

	def on_submit(self):
		self.db_set("status", "Approved / موافق عليها")
		self.db_set("approved_by", frappe.session.user)
		self.db_set("approval_date", nowdate())

	def on_cancel(self):
		self.db_set("status", "Cancelled / ملغاة")

	def _set_status(self):
		if not self.status:
			self.status = "Draft / مسودة"

	def _sync_employee_context(self):
		if not self.employee:
			return

		employee = frappe.db.get_value(
			"Employee",
			self.employee,
			["employee_name", "company", "department"],
			as_dict=True,
		)
		if not employee:
			frappe.throw(
				_("Employee {0} was not found.<br>لم يتم العثور على الموظف {0}.").format(
					frappe.bold(self.employee)
				)
			)
		self.employee_name = employee.employee_name
		self.company = employee.company
		self.department = employee.department

	def _calculate_days(self):
		if not self.leave_start_date or not self.leave_end_date:
			return

		start_date = getdate(self.leave_start_date)
		end_date = getdate(self.leave_end_date)
		if end_date < start_date:
			frappe.throw(_("تاريخ نهاية الإجازة يجب أن يكون بعد أو مساوياً لتاريخ البداية."))
		if start_date.year != end_date.year:
			frappe.throw(
				_("Annual leave request must stay within one calendar year.<br>يجب أن تقع الإجازة السنوية ضمن سنة ميلادية واحدة."),
				title=_("Invalid Leave Period / فترة إجازة غير صالحة"),
			)

		if self.half_day and start_date != end_date:
			frappe.throw(_("نصف يوم إجازة متاح فقط عندما تكون بداية الإجازة ونهايتها في اليوم نفسه."))

		self.total_leave_days = 0.5 if self.half_day else flt(date_diff(end_date, start_date) + 1)

	def _calculate_balance(self):
		if not self.employee or not self.leave_start_date:
			return

		joining_date = frappe.db.get_value("Employee", self.employee, "date_of_joining")
		if joining_date and getdate(self.leave_start_date) < getdate(joining_date):
			frappe.throw(
				_("Annual leave cannot start before the employee joining date.<br>لا يمكن أن تبدأ الإجازة السنوية قبل تاريخ التحاق الموظف."),
				title=_("Invalid Leave Date / تاريخ إجازة غير صالح"),
			)

		balance = get_annual_leave_balance(self.employee, self.leave_start_date, exclude_name=self.name)
		self.annual_entitlement_days = balance.get("entitled", balance.get("balance", 0))
		self.leave_balance_before = balance["balance"]
		self.leave_balance_after = flt(balance["balance"]) - flt(self.total_leave_days)
		self.leave_policy = balance.get("policy")
		self.leave_policy_assignment = balance.get("assignment")
		self.entitlement_source = balance.get("source_type")
		if balance.get("source_type"):
			self.entitlement_resolved_on = now_datetime()

		if self.leave_balance_after < 0:
			frappe.throw(_("رصيد الإجازة السنوية غير كافٍ لهذا الطلب."), title=_("رصيد غير كافٍ"))
