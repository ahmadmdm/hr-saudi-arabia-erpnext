import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, date_diff


class SaudiEmploymentContract(Document):
	# ─── Validation ─────────────────────────────────────────────────────────────

	def validate(self):
		self._validate_probation_period()
		self._calculate_probation_end_date()
		self._calculate_total_salary()
		self._validate_end_date()

	def _validate_probation_period(self):
		"""لا يجوز أن تتجاوز فترة التجربة الإجمالية 180 يوماً (م.53)."""
		total_probation = (self.probation_period_days or 0) + (self.extended_probation_days or 0)
		if total_probation > 180:
			frappe.throw(
				_("Total probation period cannot exceed 180 days per Saudi Labor Law Art. 53.<br>"
				  "مجموع فترة التجربة لا يجوز أن يتجاوز 180 يوماً وفقاً للمادة 53 من نظام العمل."),
				title=_("Probation Period Exceeded / تجاوز فترة التجربة"),
			)

	def _calculate_probation_end_date(self):
		"""حساب تاريخ نهاية فترة التجربة."""
		if self.start_date and self.probation_period_days:
			total_days = (self.probation_period_days or 0) + (self.extended_probation_days or 0)
			self.probation_end_date = add_days(self.start_date, total_days)

	def _calculate_total_salary(self):
		"""حساب إجمالي الراتب."""
		self.total_salary = (
			(self.basic_salary or 0)
			+ (self.housing_allowance or 0)
			+ (self.transport_allowance or 0)
			+ (self.other_allowances or 0)
		)

	def _validate_end_date(self):
		"""التحقق من تاريخ انتهاء العقد المحدد المدة."""
		if self.contract_type == "محدد المدة / Fixed Term" and not self.end_date:
			frappe.throw(
				_("End Date is required for Fixed Term contracts.<br>تاريخ الانتهاء مطلوب للعقود محددة المدة."),
				title=_("End Date Required / تاريخ الانتهاء مطلوب"),
			)
		if self.end_date and self.start_date:
			if getdate(self.end_date) <= getdate(self.start_date):
				frappe.throw(
					_("End Date must be after Start Date.<br>يجب أن يكون تاريخ الانتهاء بعد تاريخ البدء."),
					title=_("Invalid Date / تاريخ غير صحيح"),
				)

	# ─── On Submit ──────────────────────────────────────────────────────────────

	def on_submit(self):
		self.contract_status = "Active / نشط"
		self.db_set("contract_status", "Active / نشط")
