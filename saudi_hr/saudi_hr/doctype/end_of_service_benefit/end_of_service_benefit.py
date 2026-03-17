import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, getdate, flt, nowdate


class EndOfServiceBenefit(Document):

	def validate(self):
		self._fetch_joining_date()
		self._calculate_eosb()

	def _fetch_joining_date(self):
		emp = frappe.get_doc("Employee", self.employee)
		self.joining_date = emp.date_of_joining

	def _calculate_eosb(self):
		"""
		حساب مكافأة نهاية الخدمة وفق المادة 84 من نظام العمل السعودي.

		السنوات 1–5: نصف شهر (0.5) عن كل سنة.
		أكثر من 5 سنوات: شهر كامل (1.0) عن كل سنة إضافية.
		"""
		if not self.joining_date or not self.termination_date:
			return

		total_days = date_diff(self.termination_date, self.joining_date)
		years = total_days / 365.0
		self.years_of_service = round(years, 2)

		monthly_basic = flt(self.last_basic_salary)

		# حساب المكافأة الإجمالية بالشريحتين
		if years < 1:
			self.eosb_years_1_5 = 0.0
			self.eosb_years_above_5 = 0.0
		elif years <= 5:
			self.eosb_years_1_5 = round((monthly_basic / 2) * years, 2)
			self.eosb_years_above_5 = 0.0
		else:
			self.eosb_years_1_5 = round((monthly_basic / 2) * 5, 2)
			self.eosb_years_above_5 = round(monthly_basic * (years - 5), 2)

		self.eosb_gross = round(
			flt(self.eosb_years_1_5) + flt(self.eosb_years_above_5), 2
		)

		# معامل الاستقالة
		factor, label = self._get_resignation_factor(years)
		self.resignation_factor = factor
		self.resignation_factor_label = label

		# صافي المكافأة
		self.net_eosb = round(
			flt(self.eosb_gross) * factor - flt(self.eosb_deductions), 2
		)

		# ملاحظات الحساب
		self.calculation_notes = self._build_notes(years, monthly_basic, factor, label)

	def _get_resignation_factor(self, years: float):
		"""
		معامل الاستقالة وفق م.84:
		  استقالة < 2 سنة     → 0      (لا مكافأة)
		  استقالة 2–10 سنوات  → 1/3
		  استقالة > 10 سنوات  → 2/3
		  فصل تأديبي (م.80)   → 0
		  إنهاء صاحب العمل / انتهاء عقد / وفاة / عجز → 1
		"""
		reason = self.termination_reason or ""

		if "Dismissal" in reason or "فصل" in reason:
			return 0.0, "فصل تأديبي (م.80) — لا مكافأة / Disciplinary Dismissal — No EOSB"

		if "Resignation" in reason or "استقالة" in reason:
			if years < 2:
				return 0.0, "استقالة < سنتان — لا مكافأة / Resignation < 2 yrs — No EOSB"
			elif years <= 10:
				return round(1 / 3, 4), "استقالة 2–10 سنوات — ثلث المكافأة / Resignation 2–10 yrs — 1/3 EOSB"
			else:
				return round(2 / 3, 4), "استقالة > 10 سنوات — ثلثا المكافأة / Resignation >10 yrs — 2/3 EOSB"

		return 1.0, "مكافأة كاملة / Full EOSB"

	def _build_notes(self, years, monthly_basic, factor, label):
		return (
			f"سنوات الخدمة: {years:.2f} سنة\n"
			f"الراتب الأساسي: {monthly_basic:,.2f}\n"
			f"مكافأة السنوات 1-5: {self.eosb_years_1_5:,.2f}\n"
			f"مكافأة السنوات >5: {self.eosb_years_above_5:,.2f}\n"
			f"المكافأة الإجمالية: {self.eosb_gross:,.2f}\n"
			f"معامل الاستقالة: {factor} ({label})\n"
			f"صافي المكافأة: {self.net_eosb:,.2f}"
		)

	def on_submit(self):
		"""تحديث حالة الموظف عند الاعتماد."""
		if self.termination_reason not in ("Resignation / استقالة",):
			frappe.db.set_value(
				"Employee", self.employee, "status", "Left"
			)


@frappe.whitelist()
def get_last_basic_salary(employee):
	"""Return the employee's latest basic salary for JS auto-fill."""
	sal = frappe.get_all(
		"Salary Structure Assignment",
		filters={"employee": employee, "docstatus": 1},
		fields=["base"],
		order_by="from_date desc",
		limit=1,
	)
	return flt(sal[0].base) if sal else 0.0


@frappe.whitelist()
def calculate_eosb_preview(joining_date, termination_date, last_basic_salary,
		termination_reason, eosb_deductions=0):
	"""
	Standalone EOSB calculation for JS preview (mirrors _calculate_eosb logic).
	Returns a dict with all computed fields.
	"""
	from frappe.utils import date_diff

	total_days = date_diff(termination_date, joining_date)
	years = total_days / 365.0
	monthly_basic = flt(last_basic_salary)
	eosb_deductions = flt(eosb_deductions)

	if years < 1:
		eosb_1_5 = 0.0
		eosb_above_5 = 0.0
	elif years <= 5:
		eosb_1_5 = round((monthly_basic / 2) * years, 2)
		eosb_above_5 = 0.0
	else:
		eosb_1_5 = round((monthly_basic / 2) * 5, 2)
		eosb_above_5 = round(monthly_basic * (years - 5), 2)

	eosb_gross = round(eosb_1_5 + eosb_above_5, 2)

	reason = termination_reason or ""
	if "Dismissal" in reason or "فصل" in reason:
		factor, label = 0.0, "فصل تأديبي — لا مكافأة / Disciplinary Dismissal — No EOSB"
	elif "Resignation" in reason or "استقالة" in reason:
		if years < 2:
			factor, label = 0.0, "استقالة < سنتان — لا مكافأة / Resignation < 2 yrs — No EOSB"
		elif years <= 10:
			factor, label = round(1 / 3, 4), "استقالة 2–10 سنوات — ثلث المكافأة / Resignation 2–10 yrs — 1/3 EOSB"
		else:
			factor, label = round(2 / 3, 4), "استقالة > 10 سنوات — ثلثا المكافأة / Resignation >10 yrs — 2/3 EOSB"
	else:
		factor, label = 1.0, "مكافأة كاملة / Full EOSB"

	net_eosb = round(eosb_gross * factor - eosb_deductions, 2)
	notes = (
		f"سنوات الخدمة: {years:.2f}\n"
		f"الراتب الأساسي: {monthly_basic:,.2f}\n"
		f"مكافأة السنوات 1-5: {eosb_1_5:,.2f}\n"
		f"مكافأة السنوات >5: {eosb_above_5:,.2f}\n"
		f"الإجمالي: {eosb_gross:,.2f}\n"
		f"المعامل: {factor} ({label})\n"
		f"الصافي: {net_eosb:,.2f}"
	)

	return {
		"years_of_service": round(years, 2),
		"eosb_years_1_5": eosb_1_5,
		"eosb_years_above_5": eosb_above_5,
		"eosb_gross": eosb_gross,
		"resignation_factor": factor,
		"resignation_factor_label": label,
		"net_eosb": net_eosb,
		"calculation_notes": notes,
	}
