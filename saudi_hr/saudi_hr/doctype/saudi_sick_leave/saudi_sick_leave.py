import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, getdate, flt, get_first_day_of_week


class SaudiSickLeave(Document):

	def validate(self):
		self._calculate_total_days()
		self._calculate_cumulative_days()
		self._validate_max_sick_days()
		self._calculate_pay()
		self._set_alerts()

	def _calculate_total_days(self):
		if self.from_date and self.to_date:
			self.total_days = date_diff(self.to_date, self.from_date) + 1
			if self.total_days <= 0:
				frappe.throw(_("To Date must be after From Date / يجب أن يكون تاريخ الانتهاء بعد تاريخ البدء"))

	def _get_sick_days_this_year(self, exclude_current=True):
		"""مجموع أيام المرض في سنة العقد الحالية (باستثناء الوثيقة الحالية)."""
		filters = {
			"employee": self.employee,
			"docstatus": 1,
			"from_date": [">=", f"{getdate(self.from_date).year}-01-01"],
			"to_date": ["<=", f"{getdate(self.from_date).year}-12-31"],
		}
		if exclude_current and self.name:
			filters["name"] = ["!=", self.name]

		rows = frappe.get_all("Saudi Sick Leave", filters=filters, fields=["total_days"])
		return sum(r.total_days or 0 for r in rows)

	def _calculate_cumulative_days(self):
		self.sick_days_this_year_before = self._get_sick_days_this_year()
		self.sick_days_this_year_after = self.sick_days_this_year_before + (self.total_days or 0)

	def _validate_max_sick_days(self):
		"""الحد الأقصى للإجازة المرضية 120 يوماً في السنة (م.117)."""
		if self.sick_days_this_year_after > 120:
			frappe.throw(
				_("Total sick days in the year cannot exceed 120 per Saudi Labor Law Art. 117.<br>"
				  "لا يجوز أن يتجاوز مجموع أيام الإجازة المرضية في السنة 120 يوماً وفقاً للمادة 117."),
				title=_("Sick Leave Limit Exceeded / تجاوز حد الإجازة المرضية"),
			)

	def _calculate_pay(self):
		"""حساب أجر الإجازة المرضية بحسب الشرائح."""
		settings = frappe.get_single("Saudi HR Settings")
		full_days = int(settings.sick_leave_full_pay_days or 30)
		partial_days = int(settings.sick_leave_partial_pay_days or 60)
		partial_pct = flt(settings.sick_leave_partial_pay_percentage or 75) / 100

		used_before = self.sick_days_this_year_before
		new_days = self.total_days or 0

		# حساب الأجر اليومي
		sal_assign = frappe.get_all(
			"Salary Structure Assignment",
			filters={"employee": self.employee, "docstatus": 1},
			fields=["base"],
			order_by="from_date desc",
			limit=1,
		)
		monthly = flt(sal_assign[0].base) if sal_assign else 0.0
		self.daily_salary = round(monthly / 30, 2)

		# حساب معدل الأجر بحسب الشريحة التراكمية
		if used_before < full_days:
			full_day_quota = min(new_days, full_days - used_before)
			partial_quota = 0
			if new_days > full_day_quota:
				remaining = new_days - full_day_quota
				partial_quota = min(remaining, partial_days - max(0, used_before - full_days))
		else:
			full_day_quota = 0
			partial_from = max(0, used_before - full_days)
			partial_quota = min(new_days, max(0, partial_days - partial_from))

		unpaid_quota = new_days - full_day_quota - partial_quota

		pay = (
			full_day_quota * self.daily_salary * 1.0
			+ partial_quota * self.daily_salary * partial_pct
			+ unpaid_quota * 0
		)
		self.leave_pay_amount = round(pay, 2)

		# تحديد التسمية الرئيسية للقسيمة
		if used_before < full_days:
			self.pay_rate = 100.0
			self.pay_label = "Full Pay / أجر كامل (100%)"
		elif used_before < full_days + partial_days:
			self.pay_rate = partial_pct * 100
			self.pay_label = f"Partial Pay / أجر جزئي ({partial_pct*100:.0f}%)"
		else:
			self.pay_rate = 0.0
			self.pay_label = "No Pay / بدون أجر"

	def _set_alerts(self):
		after = self.sick_days_this_year_after or 0
		settings = frappe.get_single("Saudi HR Settings")
		full_days = int(settings.sick_leave_full_pay_days or 30)
		partial_days = int(settings.sick_leave_partial_pay_days or 60)

		self.alert_30_days = 1 if after > full_days else 0
		self.alert_90_days = 1 if after > full_days + partial_days else 0

		if self.alert_90_days:
			frappe.msgprint(
				_("⚠ Employee has exceeded 90 sick days. Termination is permissible per Art. 117.<br>"
				  "⚠ تجاوز الموظف 90 يوماً مرضياً. يجوز إنهاء الخدمة وفقاً للمادة 117."),
				title=_("Sick Leave Alert / تنبيه إجازة مرضية"),
				indicator="red",
			)


@frappe.whitelist()
def get_sick_days_this_year(employee, exclude_doc=""):
	"""
	Return the total approved sick days for *employee* in the current year,
	optionally excluding a specific document (used during editing).
	"""
	from frappe.utils import getdate, nowdate

	current_year = getdate(nowdate()).year
	filters = {
		"employee": employee,
		"docstatus": 1,
		"from_date": [">=", f"{current_year}-01-01"],
		"to_date": ["<=", f"{current_year}-12-31"],
	}
	if exclude_doc:
		filters["name"] = ["!=", exclude_doc]

	rows = frappe.get_all("Saudi Sick Leave", filters=filters, fields=["total_days"])
	return sum(flt(r.total_days) for r in rows)


@frappe.whitelist()
def get_daily_salary(employee):
	"""Return daily salary (monthly_basic / 30) for the employee."""
	sal = frappe.get_all(
		"Salary Structure Assignment",
		filters={"employee": employee, "docstatus": 1},
		fields=["base"],
		order_by="from_date desc",
		limit=1,
	)
	monthly = flt(sal[0].base) if sal else 0.0
	return round(monthly / 30, 2)
