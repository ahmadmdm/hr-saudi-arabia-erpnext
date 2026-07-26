"""
utils.py — Helper functions for Saudi HR calculations.
"""
import frappe
from frappe import _
from frappe.utils import cint, cstr, date_diff, flt, getdate, today


def assert_doctype_permissions(doctype: str, permission_types, doc=None):
	if isinstance(permission_types, str):
		permission_types = (permission_types,)

	for permission_type in permission_types:
		frappe.has_permission(doctype, permission_type, doc=doc, throw=True)


def text_matches_tokens(value, *tokens: str) -> bool:
	normalized = cstr(value or "").strip().lower()
	if not normalized:
		return False
	return any(cstr(token).strip().lower() in normalized for token in tokens if cstr(token).strip())


def assert_positive_basic_salary(employee_label: str, basic_salary: float, context_label: str):
	if flt(basic_salary) > 0:
		return
	frappe.throw(
		_(
			"Basic salary for {0} must be greater than zero before {1}.<br>"
			"يجب أن يكون الراتب الأساسي للموظف {0} أكبر من صفر قبل {1}."
		).format(employee_label, context_label),
		title=_("Missing Basic Salary / راتب أساسي غير متوفر"),
	)


def get_overlap_days(start_date, end_date, range_start, range_end) -> int:
	period_start = max(getdate(start_date), getdate(range_start))
	period_end = min(getdate(end_date), getdate(range_end))
	if period_end < period_start:
		return 0
	return date_diff(period_end, period_start) + 1


def calculate_prorated_sick_leave_deduction(leave_rows: list, month_start, month_end, fallback_daily_salary: float = 0.0) -> float:
	deduction = 0.0
	for row in leave_rows or []:
		overlap_days = get_overlap_days(row.get("from_date"), row.get("to_date"), month_start, month_end)
		if overlap_days <= 0:
			continue

		total_days = flt(row.get("total_days") or overlap_days)
		daily_salary = flt(row.get("daily_salary") or fallback_daily_salary)
		full_pay = flt(overlap_days) * daily_salary
		actual_pay = flt(row.get("leave_pay_amount")) * (flt(overlap_days) / total_days if total_days else 0)
		if full_pay > actual_pay:
			deduction += round(full_pay - actual_pay, 2)

	return round(deduction, 2)


def get_active_contract(employee: str, fields=None, as_dict=True):
	field_list = fields or [
		"name",
		"basic_salary",
		"housing_allowance",
		"transport_allowance",
		"other_allowances",
		"total_salary",
	]
	return frappe.db.get_value(
		"Saudi Employment Contract",
		{"employee": employee, "contract_status": "Active / نشط"},
		field_list,
		as_dict=as_dict,
		order_by="start_date desc",
	)


def get_employee_basic_salary(employee: str) -> float:
	contract = get_active_contract(employee, ["basic_salary"], as_dict=True) or {}
	basic_salary = flt(contract.get("basic_salary"))
	if basic_salary:
		return basic_salary
	return flt(frappe.db.get_value("Employee", employee, "ctc") or 0)


def get_employee_salary_components(employee: str) -> dict:
	contract = get_active_contract(
		employee,
		["basic_salary", "housing_allowance", "transport_allowance", "other_allowances", "total_salary"],
		as_dict=True,
	) or {}
	basic = flt(contract.get("basic_salary") or frappe.db.get_value("Employee", employee, "ctc") or 0)
	housing = flt(contract.get("housing_allowance") or 0)
	transport = flt(contract.get("transport_allowance") or 0)
	other = flt(contract.get("other_allowances") or 0)
	total = flt(contract.get("total_salary") or (basic + housing + transport + other))
	return {
		"basic_salary": basic,
		"housing_allowance": housing,
		"transport_allowance": transport,
		"other_allowances": other,
		"total_salary": total,
	}


def get_annual_leave_days_taken(employee: str, leave_year: int, exclude_name: str | None = None) -> float:
	filters = {
		"employee": employee,
		"docstatus": 1,
	}
	if exclude_name:
		filters["name"] = ["!=", exclude_name]

	rows = frappe.get_all(
		"Saudi Annual Leave",
		filters=filters,
		fields=["leave_start_date", "leave_end_date", "total_leave_days", "half_day"],
	)
	year_start = f"{leave_year}-01-01"
	year_end = f"{leave_year}-12-31"
	total = 0.0
	for row in rows:
		overlap_days = get_overlap_days(row.leave_start_date, row.leave_end_date, year_start, year_end)
		if overlap_days <= 0:
			continue
		if getattr(row, "half_day", 0):
			total += 0.5
			continue
		document_days = max(flt(row.total_leave_days), flt(date_diff(row.leave_end_date, row.leave_start_date) + 1))
		total += flt(row.total_leave_days or overlap_days) * (flt(overlap_days) / document_days if document_days else 0)
	return round(total, 2)


def get_annual_leave_balance(employee: str, reference_date: str | None = None, exclude_name: str | None = None) -> dict:
	reference = getdate(reference_date) if reference_date else getdate()
	entitlement = get_annual_leave_entitlement(employee, reference)
	taken = get_annual_leave_days_taken(employee, reference.year, exclude_name=exclude_name)
	return {
		"entitled": entitlement,
		"taken": taken,
		"balance": flt(entitlement) - flt(taken),
		"year": reference.year,
	}


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
	details = calculate_eosb_components(
		emp.date_of_joining,
		termination_date or getdate(),
		get_employee_basic_salary(employee),
		termination_reason,
	)

	return {
		"years_of_service": details["years_of_service"],
		"monthly_basic": details["monthly_basic"],
		"eosb_gross": details["eosb_gross"],
		"resignation_factor": details["resignation_factor"],
		"eosb_net": details["net_eosb"],
	}


def _get_resignation_factor(years: float, termination_reason: str) -> float:
	"""
	معامل الاستقالة وفق المادة (الخامسة والثمانين) من نظام العمل:
	- استقالة < 2 سنة  → 0
	- استقالة 2–5 سنوات → 1/3
	- استقالة > 5 وأقل من 10 سنوات → 2/3
	- استقالة 10 سنوات فأكثر → 1.0 (المكافأة كاملة)
	- إنهاء من صاحب العمل / انتهاء عقد / وفاة → 1.0
	- فصل تأديبي (م.80) → 0
	"""
	return get_eosb_factor_and_label(termination_reason, years)[0]


def get_eosb_factor_and_label(termination_reason: str, years: float) -> tuple[float, str]:
	reason = termination_reason or ""
	if text_matches_tokens(reason, "dismissal", "فصل"):
		return 0.0, "فصل تأديبي (م.80) — لا مكافأة / Disciplinary Dismissal — No EOSB"

	if text_matches_tokens(reason, "resignation", "استقالة"):
		if years < 2:
			return 0.0, "استقالة < سنتان — لا مكافأة / Resignation < 2 yrs — No EOSB"
		if years <= 5:
			return round(1 / 3, 4), "استقالة 2–5 سنوات — ثلث المكافأة / Resignation 2–5 yrs — 1/3 EOSB"
		if years < 10:
			return round(2 / 3, 4), "استقالة 5–10 سنوات — ثلثا المكافأة / Resignation 5–10 yrs — 2/3 EOSB"
		return 1.0, "استقالة 10 سنوات فأكثر — المكافأة كاملة / Resignation 10+ yrs — Full EOSB"

	return 1.0, "مكافأة كاملة / Full EOSB"


def build_eosb_notes(years, monthly_basic, eosb_years_1_5, eosb_years_above_5, eosb_gross, factor, label, net_eosb):
	return (
		f"سنوات الخدمة: {years:.2f} سنة\n"
		f"الراتب الأساسي: {monthly_basic:,.2f}\n"
		f"مكافأة السنوات 1-5: {eosb_years_1_5:,.2f}\n"
		f"مكافأة السنوات >5: {eosb_years_above_5:,.2f}\n"
		f"المكافأة الإجمالية: {eosb_gross:,.2f}\n"
		f"معامل الاستقالة: {factor} ({label})\n"
		f"صافي المكافأة: {net_eosb:,.2f}"
	)


def calculate_eosb_components(joining_date, termination_date, last_basic_salary, termination_reason, eosb_deductions=0) -> dict:
	joining = getdate(joining_date)
	termination = getdate(termination_date)
	if termination <= joining:
		frappe.throw(
			_(
				"Termination date must be after the joining date.<br>"
				"تاريخ إنهاء الخدمة يجب أن يكون بعد تاريخ الالتحاق بالعمل."
			),
			title=_("Invalid Date / تاريخ غير صحيح"),
		)

	monthly_basic = flt(last_basic_salary)
	if monthly_basic <= 0:
		frappe.throw(
			_("Last basic salary must be greater than zero.<br>يجب أن يكون الراتب الأساسي الأخير أكبر من صفر."),
			title=_("Missing Basic Salary / راتب أساسي غير متوفر"),
		)

	deductions = flt(eosb_deductions)
	if deductions < 0:
		frappe.throw(
			_("EOSB deductions cannot be negative.<br>خصومات مكافأة نهاية الخدمة لا يمكن أن تكون سالبة."),
			title=_("Invalid Deduction / خصم غير صالح"),
		)

	total_days = date_diff(termination, joining)
	years = total_days / 365.0
	# المادة (84): يستحق العامل مكافأة عن أجزاء السنة بنسبة ما قضاه منها في العمل،
	# فلا يوجد حد أدنى قدره سنة. أما شرط السنتين فهو خاص بالاستقالة (المادة 85)
	# ويُطبَّق عبر معامل الاستقالة أدناه.
	if years <= 5:
		eosb_years_1_5 = round((monthly_basic / 2) * years, 2)
		eosb_years_above_5 = 0.0
	else:
		eosb_years_1_5 = round((monthly_basic / 2) * 5, 2)
		eosb_years_above_5 = round(monthly_basic * (years - 5), 2)

	eosb_gross = round(eosb_years_1_5 + eosb_years_above_5, 2)
	factor, label = get_eosb_factor_and_label(termination_reason, years)
	net_eosb = round(eosb_gross * factor - deductions, 2)
	if net_eosb < 0:
		frappe.throw(
			_("EOSB deductions exceed the payable amount.<br>خصومات مكافأة نهاية الخدمة تتجاوز المبلغ المستحق."),
			title=_("Invalid Deduction / خصم غير صالح"),
		)

	return {
		"years_of_service": round(years, 2),
		"monthly_basic": monthly_basic,
		"eosb_years_1_5": eosb_years_1_5,
		"eosb_years_above_5": eosb_years_above_5,
		"eosb_gross": eosb_gross,
		"resignation_factor": factor,
		"resignation_factor_label": label,
		"net_eosb": net_eosb,
		"calculation_notes": build_eosb_notes(
			years,
			monthly_basic,
			eosb_years_1_5,
			eosb_years_above_5,
			eosb_gross,
			factor,
			label,
			net_eosb,
		),
	}


# ---------------------------------------------------------------------------
# اشتراكات التأمينات الاجتماعية (GOSI)
#
# النظام السابق — لمن بدأ اشتراكه قبل 3 يوليو 2024:
#   المعاشات 9% على كل طرف + ساند 0.75% على كل طرف + الأخطار المهنية 2% على صاحب العمل
#   => العامل 9.75% وصاحب العمل 11.75%
#
# نظام التأمينات الاجتماعية الجديد (مرسوم ملكي م/273) — لمن لا توجد له مدد اشتراك
# سابقة قبل 3 يوليو 2024: ترتفع نسبة المعاشات من 9% إلى 11% على كل طرف بواقع
# 0.5% سنوياً اعتباراً من يوليو 2025 وحتى يوليو 2028.
#
# غير السعوديين: فرع الأخطار المهنية فقط 2% على صاحب العمل.
# وعاء الاشتراك = الأجر الأساسي + بدل السكن بحد أقصى 45,000 ريال شهرياً.
# ---------------------------------------------------------------------------
GOSI_NEW_SYSTEM_START_DATE = "2024-07-03"
GOSI_OLD_SYSTEM_PENSION_RATE = 9.0
GOSI_DEFAULT_SANED_RATE = 0.75
GOSI_DEFAULT_OCCUPATIONAL_HAZARDS_RATE = 2.0

# تُطبَّق الزيادة على شهر الاشتراك كاملاً، والذكرى النظامية للقانون هي 3 يوليو.
GOSI_NEW_SYSTEM_PENSION_SCHEDULE = [
	("2028-07-01", 11.0),
	("2027-07-01", 10.5),
	("2026-07-01", 10.0),
	("2025-07-01", 9.5),
]


def get_gosi_pension_rate(is_new_system: bool, as_on_date=None) -> float:
	"""نسبة فرع المعاشات على كل طرف في التاريخ المطلوب."""
	if not is_new_system:
		return GOSI_OLD_SYSTEM_PENSION_RATE

	reference = getdate(as_on_date or today())
	for start_date, rate in GOSI_NEW_SYSTEM_PENSION_SCHEDULE:
		if reference >= getdate(start_date):
			return rate
	return GOSI_OLD_SYSTEM_PENSION_RATE


def is_gosi_new_system_subscriber(employee: str) -> bool:
	"""هل يخضع العامل لنظام التأمينات الجديد (لا توجد له مدد اشتراك قبل 3 يوليو 2024)."""
	if not employee:
		return False

	first_contribution_date = None
	if frappe.get_meta("Employee").has_field("gosi_first_contribution_date"):
		first_contribution_date = frappe.db.get_value("Employee", employee, "gosi_first_contribution_date")
	# عند غياب تاريخ أول اشتراك يُستخدم تاريخ الالتحاق كتقدير، وقد يخالف الواقع
	# إذا كانت للعامل مدد اشتراك سابقة لدى صاحب عمل آخر.
	if not first_contribution_date:
		first_contribution_date = frappe.db.get_value("Employee", employee, "date_of_joining")
	if not first_contribution_date:
		return False

	return getdate(first_contribution_date) >= getdate(GOSI_NEW_SYSTEM_START_DATE)


GOSI_SOURCE_ASSUMED = "Assumed from Joining Date / مُقدَّر من تاريخ الالتحاق"
GOSI_SOURCE_CONFIRMED = "Confirmed from GOSI / مؤكد من التأمينات"


@frappe.whitelist()
def backfill_gosi_first_contribution_dates(dry_run=1, company=None):
	"""
	تعبئة تاريخ أول اشتراك من تاريخ الالتحاق لمن التحق في 3 يوليو 2024 أو بعده.

	التاريخ المُعبَّأ تقدير وليس واقعة مؤكدة: من التحق بعد هذا التاريخ وله مدد
	اشتراك سابقة لدى صاحب عمل آخر يبقى على النظام السابق، ولا سبيل لمعرفة ذلك
	إلا من سجل التأمينات. لذلك تُوسم كل قيمة تُكتب هنا بأنها مُقدَّرة.

	لا يُمسّ أي موظف لديه تاريخ مسجّل مسبقاً.
	"""
	assert_doctype_permissions("Employee", ("read", "write"))
	dry_run = cint(dry_run)

	meta = frappe.get_meta("Employee")
	if not meta.has_field("gosi_first_contribution_date"):
		frappe.throw(_("Employee is missing the GOSI first contribution date field."))

	filters = {
		"date_of_joining": (">=", GOSI_NEW_SYSTEM_START_DATE),
		"gosi_first_contribution_date": ("is", "not set"),
	}
	if company:
		filters["company"] = company

	candidates = frappe.get_all(
		"Employee",
		filters=filters,
		fields=["name", "employee_name", "date_of_joining"],
		order_by="date_of_joining",
	)

	updated = []
	has_source_field = meta.has_field("gosi_subscription_date_source")
	for row in candidates:
		if not dry_run:
			frappe.db.set_value(
				"Employee",
				row.name,
				{
					"gosi_first_contribution_date": row.date_of_joining,
					**({"gosi_subscription_date_source": GOSI_SOURCE_ASSUMED} if has_source_field else {}),
				},
				update_modified=False,
			)
		updated.append(
			{
				"employee": row.name,
				"employee_name": row.employee_name,
				"assumed_date": str(row.date_of_joining),
			}
		)

	# لا يُستدعى commit هنا: طلبات الويب تُثبِّت تلقائياً، ويبقى الاستدعاء من
	# السكربتات والاختبارات ضمن معاملة واحدة يتحكم بها المستدعي.
	return {
		"dry_run": bool(dry_run),
		"cutover_date": GOSI_NEW_SYSTEM_START_DATE,
		"count": len(updated),
		"employees": updated,
	}


def get_gosi_rates(nationality: str, employee: str = None, as_on_date=None) -> dict:
	"""
	إرجاع معدلات GOSI حسب الجنسية ونظام الاشتراك المطبَّق على العامل.
	"""
	settings = frappe.get_single("Saudi HR Settings")

	if not is_saudi_nationality(nationality):
		return {
			"employee_rate": flt(settings.gosi_non_saudi_employee_rate),
			"employer_rate": flt(settings.gosi_non_saudi_employer_rate) or GOSI_DEFAULT_OCCUPATIONAL_HAZARDS_RATE,
			"pension_rate": 0.0,
			"system": "Non-Saudi / غير سعودي",
		}

	# القيمة غير المضبوطة تُعامل كمفعّلة، لأن الجدول الجديد هو الوضع النظامي القائم.
	new_system_flag = getattr(settings, "gosi_apply_new_system_schedule", None)
	apply_new_system = 1 if new_system_flag is None else cint(new_system_flag)
	if apply_new_system and is_gosi_new_system_subscriber(employee):
		saned = flt(getattr(settings, "gosi_saned_rate", None) or GOSI_DEFAULT_SANED_RATE)
		hazards = flt(
			getattr(settings, "gosi_occupational_hazards_rate", None) or GOSI_DEFAULT_OCCUPATIONAL_HAZARDS_RATE
		)
		pension = get_gosi_pension_rate(True, as_on_date)
		return {
			"employee_rate": round(pension + saned, 4),
			"employer_rate": round(pension + saned + hazards, 4),
			"pension_rate": pension,
			"system": "New System / نظام التأمينات الجديد",
		}

	return {
		"employee_rate": flt(settings.gosi_saudi_employee_rate) or 9.75,
		"employer_rate": flt(settings.gosi_saudi_employer_rate) or 11.75,
		"pension_rate": GOSI_OLD_SYSTEM_PENSION_RATE,
		"system": "Previous System / النظام السابق",
	}


def is_saudi_nationality(nationality: str) -> bool:
	text = (nationality or "").strip().lower()
	if not text:
		return False
	return text == "sa" or "saudi" in text or "سعودي" in text


def get_employee_nationality(employee: str) -> str:
	if not employee:
		return ""

	if frappe.get_meta("Employee").has_field("nationality"):
		return frappe.db.get_value("Employee", employee, "nationality") or ""

	return get_contract_nationality_lookup([employee]).get(employee) or ""


def get_contract_nationality_lookup(employees: list[str]) -> dict[str, str]:
	if not employees:
		return {}

	lookup = {}
	for row in frappe.get_all(
		"Saudi Employment Contract",
		filters={"employee": ["in", employees], "docstatus": ["<", 2]},
		fields=["employee", "nationality"],
		order_by="start_date desc, modified desc",
		limit_page_length=0,
	):
		employee = row.get("employee")
		if row.get("nationality") and employee and employee not in lookup:
			lookup[employee] = row.get("nationality")
	return lookup


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
