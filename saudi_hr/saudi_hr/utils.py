"""
utils.py — Helper functions for Saudi HR calculations.
"""
import frappe
from frappe.utils import date_diff, getdate, flt


def get_annual_leave_entitlement(employee: str, date: str = None) -> int:
	"""
	إرجاع عدد أيام الإجازة السنوية بحسب سنوات الخدمة (م.109).
	< 5 سنوات: 21 يوم | ≥ 5 سنوات: 30 يوم
	"""
	emp = frappe.get_doc("Employee", employee)
	joining_date = getdate(emp.date_of_joining)
	ref_date = getdate(date) if date else getdate()
	years = date_diff(ref_date, joining_date) / 365.0
	settings = frappe.get_single("Saudi HR Settings")
	threshold = flt(settings.annual_leave_years_threshold) or 5
	return int(settings.annual_leave_after_threshold or 30) if years >= threshold else int(settings.annual_leave_before_threshold or 21)


def get_eosb_amount(employee: str, termination_reason: str, termination_date: str = None) -> dict:
	"""
	حساب مكافأة نهاية الخدمة وفق المادة 84 من نظام العمل السعودي.

	Returns dict with:
		- years_of_service
		- eosb_gross        (قبل معامل الاستقالة)
		- resignation_factor
		- eosb_net          (المستحق الفعلي)
	"""
	emp = frappe.get_doc("Employee", employee)
	joining_date = getdate(emp.date_of_joining)
	end_date = getdate(termination_date) if termination_date else getdate()

	total_days = date_diff(end_date, joining_date)
	years = total_days / 365.0

	# الأجر الأساسي الأخير
	basic_salary = flt(emp.get("ctc") or 0)
	# محاولة الحصول على الأجر الأساسي من هيكل الراتب الحالي
	sal_assign = frappe.get_all(
		"Salary Structure Assignment",
		filters={"employee": employee, "docstatus": 1},
		fields=["base"],
		order_by="from_date desc",
		limit=1,
	)
	if sal_assign:
		basic_salary = flt(sal_assign[0].base)

	monthly_basic = basic_salary  # افتراض أن الراتب شهري

	# حساب مكافأة نصف شهر عن السنوات 1-5 وشهر عن ما بعدها
	if years < 1:
		eosb_gross = 0.0
	elif years <= 5:
		eosb_gross = (monthly_basic / 2) * years
	else:
		eosb_gross = (monthly_basic / 2) * 5 + monthly_basic * (years - 5)

	# معامل الاستقالة (م.84)
	factor = _get_resignation_factor(years, termination_reason)

	return {
		"years_of_service": round(years, 2),
		"monthly_basic": monthly_basic,
		"eosb_gross": round(eosb_gross, 2),
		"resignation_factor": factor,
		"eosb_net": round(eosb_gross * factor, 2),
	}


def _get_resignation_factor(years: float, termination_reason: str) -> float:
	"""
	معامل الاستقالة:
	- استقالة < 2 سنة  → 0
	- استقالة 2–10 سنوات → 1/3
	- استقالة > 10 سنوات → 2/3
	- إنهاء من صاحب العمل / انتهاء عقد / وفاة → 1.0
	- فصل تأديبي (م.80) → 0
	"""
	resignation_reasons = {
		"Resignation / استقالة",
	}
	dismissal_reasons = {
		"Dismissal / فصل تأديبي (م.80)",
	}

	if termination_reason in dismissal_reasons:
		return 0.0

	if termination_reason in resignation_reasons:
		if years < 2:
			return 0.0
		elif years <= 10:
			return 1 / 3
		else:
			return 2 / 3

	# إنهاء من صاحب العمل، انتهاء عقد محدد، وفاة
	return 1.0


def get_gosi_rates(nationality: str) -> dict:
	"""
	إرجاع معدلات GOSI حسب الجنسية.
	"""
	settings = frappe.get_single("Saudi HR Settings")
	is_saudi = (nationality or "").lower() in ("saudi", "سعودي", "sa")

	if is_saudi:
		return {
			"employee_rate": flt(settings.gosi_saudi_employee_rate) or 10.0,
			"employer_rate": flt(settings.gosi_saudi_employer_rate) or 12.0,
		}
	else:
		return {
			"employee_rate": flt(settings.gosi_non_saudi_employee_rate) or 0.0,
			"employer_rate": flt(settings.gosi_non_saudi_employer_rate) or 2.0,
		}


def get_sick_leave_pay(employee: str, sick_days_this_year: int) -> dict:
	"""
	حساب أجر الإجازة المرضية بحسب م.117:
	  الأيام 1–30   → 100%
	  الأيام 31–90  → 75%
	  الأيام 91–120 → 0%
	"""
	settings = frappe.get_single("Saudi HR Settings")
	full_days = int(settings.sick_leave_full_pay_days or 30)
	partial_days = int(settings.sick_leave_partial_pay_days or 60)
	partial_pct = flt(settings.sick_leave_partial_pay_percentage or 75) / 100

	used = sick_days_this_year
	if used <= full_days:
		return {"rate": 1.0, "label": "Full Pay / أجر كامل"}
	elif used <= full_days + partial_days:
		return {"rate": partial_pct, "label": f"Partial Pay {partial_pct*100:.0f}% / أجر جزئي"}
	else:
		return {"rate": 0.0, "label": "No Pay / بدون أجر"}
