import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, flt

# الأيام المستحقة بحسب نوع الإجازة (م.151 من نظام العمل السعودي)
LEAVE_DAYS = {
	"Maternity / أمومة (70 يوم)": 70,
	"Paternity / أبوة (3 أيام)": 3,
	"Miscarriage after 6 months / إجهاض بعد 6 أشهر (60 يوم)": 60,
}


class MaternityPaternityLeave(Document):

	def validate(self):
		self._set_entitled_days()
		self._calculate_end_date()
		self._calculate_pay()
		self._validate_certificate()

	def _set_entitled_days(self):
		self.entitled_days = LEAVE_DAYS.get(self.leave_type, 0)
		if not self.entitled_days:
			frappe.throw(
				_("Unknown leave type. Please select a valid type.<br>"
				  "نوع الإجازة غير معروف. يرجى اختيار نوع صحيح."),
				title=_("Invalid Leave Type"),
			)

	def _calculate_end_date(self):
		if self.leave_start_date and self.entitled_days:
			self.leave_end_date = add_days(self.leave_start_date, self.entitled_days - 1)

	def _calculate_pay(self):
		"""الأجر كامل لجميع أنواع إجازات الأمومة/الأبوة بموجب م.151."""
		self.full_pay = 1
		self.pay_note = "Full pay per Saudi Labor Law Art. 151 / أجر كامل وفقاً للمادة 151"

		sal = frappe.get_all(
			"Salary Structure Assignment",
			filters={"employee": self.employee, "docstatus": 1},
			fields=["base"],
			order_by="from_date desc",
			limit=1,
		)
		monthly = flt(sal[0].base) if sal else 0.0
		self.daily_salary = round(monthly / 30, 2)
		self.total_leave_pay = round(self.daily_salary * (self.entitled_days or 0), 2)

	def _validate_certificate(self):
		"""التحقق من إرفاق الشهادة الطبية عند الاعتماد."""
		if self.docstatus == 1 and not self.medical_certificate_attached:
			frappe.throw(
				_("Medical certificate must be attached before submitting.<br>"
				  "يجب إرفاق الشهادة الطبية قبل الاعتماد."),
				title=_("Certificate Required / الشهادة الطبية مطلوبة"),
			)


@frappe.whitelist()
def get_daily_salary(employee):
	"""Return daily salary (monthly_basic / 30) for JS auto-fill."""
	sal = frappe.get_all(
		"Salary Structure Assignment",
		filters={"employee": employee, "docstatus": 1},
		fields=["base"],
		order_by="from_date desc",
		limit=1,
	)
	monthly = flt(sal[0].base) if sal else 0.0
	return round(monthly / 30, 2)
