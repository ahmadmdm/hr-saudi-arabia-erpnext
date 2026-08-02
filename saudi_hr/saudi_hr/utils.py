"""
utils.py — Helper functions for Saudi HR calculations.
"""
import frappe
from frappe import _
from frappe.utils import add_years, cint, cstr, date_diff, flt, getdate, today


LEAVE_SCOPE_EMPLOYEE = "Employee / موظف"
LEAVE_SCOPE_DEPARTMENT = "Department / قسم"
LEAVE_SOURCE_SETTINGS = "Saudi HR Settings / إعدادات الموارد البشرية"
STATUTORY_ANNUAL_THRESHOLD_YEARS = 5
STATUTORY_ANNUAL_BEFORE_DAYS = 21
STATUTORY_ANNUAL_AFTER_DAYS = 30
STATUTORY_SICK_FULL_PAY_DAYS = 30
STATUTORY_SICK_PAID_TIER_DAYS = 90
STATUTORY_SICK_PARTIAL_PAY_PERCENTAGE = 75
STATUTORY_SICK_MAX_DAYS = 120


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


def get_active_contract(employee: str, fields=None, as_dict=True, reference_date=None):
	"""Return the submitted contract that is active on the requested date."""
	reference_date = getdate(reference_date or today())
	field_list = fields or [
		"name",
		"basic_salary",
		"housing_allowance",
		"transport_allowance",
		"other_allowances",
		"total_salary",
	]
	rows = frappe.get_all(
		"Saudi Employment Contract",
		filters={
			"employee": employee,
			"docstatus": 1,
			"contract_status": "Active / نشط",
			"start_date": ["<=", reference_date],
		},
		or_filters=[
			["Saudi Employment Contract", "end_date", "is", "not set"],
			["Saudi Employment Contract", "end_date", ">=", reference_date],
		],
		fields=field_list,
		order_by="start_date desc",
		limit=1,
	)
	if not rows:
		return None
	row = rows[0]
	if as_dict:
		return row
	values = tuple(row.get(field) for field in field_list)
	return values[0] if len(values) == 1 else values


def assert_employee_record_access(employee: str, related_doctype: str | None = None) -> bool:
	"""Allow access to employee-scoped data for the employee or an authorized reader."""
	employee_doc = frappe.get_doc("Employee", employee)
	if employee_doc.user_id and employee_doc.user_id == frappe.session.user:
		return True

	frappe.has_permission("Employee", "read", doc=employee_doc, throw=True)
	if related_doctype:
		frappe.has_permission(related_doctype, "read", throw=True)
	return True


def assert_employee_salary_access(employee: str) -> bool:
	"""Allow salary lookup only for the employee themself or an authorized reader."""
	assert_employee_record_access(employee)
	if frappe.db.get_value("Employee", employee, "user_id") == frappe.session.user:
		return True
	contract = get_active_contract(employee, ["name"], as_dict=True)
	if contract:
		contract_doc = frappe.get_doc("Saudi Employment Contract", contract.name)
		frappe.has_permission("Saudi Employment Contract", "read", doc=contract_doc, throw=True)
	else:
		frappe.has_permission("Saudi Employment Contract", "read", throw=True)
	return True


def can_access_complete_employee_file(employee: str) -> bool:
	"""Return whether the current user may print the full, salary-bearing HR file."""
	if frappe.session.user == "Guest":
		return False
	roles = set(frappe.get_roles(frappe.session.user))
	if frappe.session.user != "Administrator" and not roles.intersection({"HR Manager", "System Manager"}):
		return False
	try:
		employee_doc = frappe.get_doc("Employee", employee)
		return bool(frappe.has_permission("Employee", "print", doc=employee_doc))
	except (frappe.DoesNotExistError, frappe.PermissionError):
		return False


def assert_complete_employee_file_access(employee: str) -> bool:
	"""Jinja security gate for the comprehensive employee print format."""
	if not can_access_complete_employee_file(employee):
		frappe.throw(
			_("Only HR Managers may print the complete employee file.<br>طباعة ملف الموظف الشامل متاحة لمدير الموارد البشرية فقط."),
			frappe.PermissionError,
		)
	return True


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


def validate_leave_policy_values(
	annual_threshold,
	annual_before,
	annual_after,
	sick_full_days,
	sick_partial_days,
	sick_partial_percentage,
):
	"""Keep configurable benefits at or above the Saudi statutory minimums."""
	threshold = flt(annual_threshold)
	before_days = flt(annual_before)
	after_days = flt(annual_after)
	full_days = flt(sick_full_days)
	partial_days = flt(sick_partial_days)
	partial_percentage = flt(sick_partial_percentage)

	if threshold < 1 or threshold > STATUTORY_ANNUAL_THRESHOLD_YEARS:
		frappe.throw(
			_(
				"Annual leave threshold must be between 1 and 5 years.<br>"
				"يجب أن تكون عتبة الإجازة السنوية بين سنة وخمس سنوات."
			),
			title=_("Invalid Leave Threshold / عتبة إجازة غير صالحة"),
		)
	if before_days < STATUTORY_ANNUAL_BEFORE_DAYS:
		frappe.throw(
			_("Annual leave before the threshold cannot be less than 21 days.<br>لا يجوز أن يقل الاستحقاق قبل العتبة عن 21 يومًا."),
			title=_("Statutory Minimum / الحد النظامي"),
		)
	if after_days < STATUTORY_ANNUAL_AFTER_DAYS:
		frappe.throw(
			_("Annual leave after the threshold cannot be less than 30 days.<br>لا يجوز أن يقل الاستحقاق بعد العتبة عن 30 يومًا."),
			title=_("Statutory Minimum / الحد النظامي"),
		)
	if after_days < before_days:
		frappe.throw(
			_("Entitlement after the threshold cannot be lower than the earlier entitlement.<br>لا يجوز أن ينخفض الاستحقاق بعد بلوغ العتبة."),
			title=_("Invalid Entitlement / استحقاق غير صالح"),
		)
	if full_days < STATUTORY_SICK_FULL_PAY_DAYS:
		frappe.throw(
			_("Full-pay sick leave cannot be less than 30 days.<br>لا يجوز أن تقل الإجازة المرضية بأجر كامل عن 30 يومًا."),
			title=_("Statutory Minimum / الحد النظامي"),
		)
	if full_days + partial_days < STATUTORY_SICK_PAID_TIER_DAYS:
		frappe.throw(
			_("Full and partial paid sick-leave tiers must cover at least 90 days.<br>يجب أن تغطي شرائح المرضية المدفوعة 90 يومًا على الأقل."),
			title=_("Statutory Minimum / الحد النظامي"),
		)
	if full_days + partial_days > STATUTORY_SICK_MAX_DAYS:
		frappe.throw(
			_("Paid sick-leave tiers cannot exceed the 120-day benefit cycle.<br>لا يجوز أن تتجاوز شرائح المرضية المدفوعة دورة الاستحقاق البالغة 120 يومًا."),
			title=_("Invalid Sick Leave Tiers / شرائح مرضية غير صالحة"),
		)
	if partial_days and partial_percentage < STATUTORY_SICK_PARTIAL_PAY_PERCENTAGE:
		frappe.throw(
			_("Partial sick-leave pay cannot be less than 75%.<br>لا يجوز أن تقل نسبة أجر المرضية الجزئي عن 75٪."),
			title=_("Statutory Minimum / الحد النظامي"),
		)


def _normalize_leave_policy_values(values):
	threshold = min(
		STATUTORY_ANNUAL_THRESHOLD_YEARS,
		max(1, flt(values.get("annual_leave_years_threshold") or STATUTORY_ANNUAL_THRESHOLD_YEARS)),
	)
	before_days = max(
		STATUTORY_ANNUAL_BEFORE_DAYS,
		int(flt(values.get("annual_leave_before_threshold") or STATUTORY_ANNUAL_BEFORE_DAYS)),
	)
	after_days = max(
		STATUTORY_ANNUAL_AFTER_DAYS,
		before_days,
		int(flt(values.get("annual_leave_after_threshold") or STATUTORY_ANNUAL_AFTER_DAYS)),
	)
	full_days = min(
		STATUTORY_SICK_MAX_DAYS,
		max(
			STATUTORY_SICK_FULL_PAY_DAYS,
			int(flt(values.get("sick_leave_full_pay_days") or STATUTORY_SICK_FULL_PAY_DAYS)),
		),
	)
	partial_days = max(0, int(flt(values.get("sick_leave_partial_pay_days") or 0)))
	if full_days + partial_days < STATUTORY_SICK_PAID_TIER_DAYS:
		partial_days = STATUTORY_SICK_PAID_TIER_DAYS - full_days
	if full_days + partial_days > STATUTORY_SICK_MAX_DAYS:
		partial_days = max(0, STATUTORY_SICK_MAX_DAYS - full_days)
	partial_percentage = max(
		STATUTORY_SICK_PARTIAL_PAY_PERCENTAGE,
		flt(values.get("sick_leave_partial_pay_percentage") or STATUTORY_SICK_PARTIAL_PAY_PERCENTAGE),
	)
	return {
		"annual_leave_years_threshold": threshold,
		"annual_leave_before_threshold": before_days,
		"annual_leave_after_threshold": after_days,
		"sick_leave_full_pay_days": full_days,
		"sick_leave_partial_pay_days": partial_days,
		"sick_leave_partial_pay_percentage": partial_percentage,
	}


def _get_employee_leave_context(employee):
	context = frappe.db.get_value(
		"Employee",
		employee,
		["name", "company", "department", "date_of_joining"],
		as_dict=True,
	)
	if not context:
		frappe.throw(_("Employee {0} was not found. / لم يتم العثور على الموظف {0}.").format(employee))
	if not context.date_of_joining:
		frappe.throw(
			_("Employee joining date is required to calculate leave entitlement.<br>تاريخ مباشرة الموظف مطلوب لحساب استحقاق الإجازة."),
			title=_("Missing Joining Date / تاريخ المباشرة غير موجود"),
		)
	return context


def _find_leave_policy_assignment(context, reference_date):
	if not frappe.db.exists("DocType", "Saudi Leave Policy Assignment"):
		return None

	targets = [
		(LEAVE_SCOPE_EMPLOYEE, "employee", context.name),
		(LEAVE_SCOPE_DEPARTMENT, "department", context.department),
	]
	for scope, target_field, target in targets:
		if not target:
			continue
		assignments = frappe.get_all(
			"Saudi Leave Policy Assignment",
			filters=[
				["enabled", "=", 1],
				["company", "=", context.company],
				["applies_to", "=", scope],
				[target_field, "=", target],
				["effective_from", "<=", reference_date],
			],
			or_filters=[
				["effective_to", "is", "not set"],
				["effective_to", ">=", reference_date],
			],
			fields=["name", "policy", "applies_to", "effective_from"],
			order_by="effective_from desc, modified desc",
			limit_page_length=20,
		)
		for assignment in assignments:
			policy = frappe.db.get_value(
				"Saudi Leave Policy",
				assignment.policy,
				[
					"name",
					"policy_name",
					"company",
					"enabled",
					"annual_leave_years_threshold",
					"annual_leave_before_threshold",
					"annual_leave_after_threshold",
					"sick_leave_full_pay_days",
					"sick_leave_partial_pay_days",
					"sick_leave_partial_pay_percentage",
				],
				as_dict=True,
			)
			if policy and policy.enabled and policy.company == context.company:
				return assignment, policy
	return None


def resolve_leave_policy(employee: str, reference_date: str | None = None) -> dict:
	"""Resolve employee > department > global settings using the employee master record."""
	reference = getdate(reference_date) if reference_date else getdate()
	context = _get_employee_leave_context(employee)
	resolved = _find_leave_policy_assignment(context, reference)

	if resolved:
		assignment, policy = resolved
		values = _normalize_leave_policy_values(policy)
		return {
			**values,
			"policy": policy.name,
			"policy_name": policy.policy_name,
			"assignment": assignment.name,
			"source_type": assignment.applies_to,
			"company": context.company,
			"department": context.department,
			"reference_date": reference,
		}

	settings = frappe.get_cached_doc("Saudi HR Settings")
	values = _normalize_leave_policy_values(settings)
	return {
		**values,
		"policy": None,
		"policy_name": _("Saudi HR Settings / إعدادات الموارد البشرية"),
		"assignment": None,
		"source_type": LEAVE_SOURCE_SETTINGS,
		"company": context.company,
		"department": context.department,
		"reference_date": reference,
	}


def get_annual_leave_entitlement_details(employee: str, date: str | None = None) -> dict:
	"""Return the auditable annual entitlement and its resolved policy source."""
	reference = getdate(date) if date else getdate()
	context = _get_employee_leave_context(employee)
	policy = resolve_leave_policy(employee, reference)
	threshold = flt(policy["annual_leave_years_threshold"])
	policy_threshold_date = add_years(context.date_of_joining, int(threshold))
	statutory_threshold_date = add_years(context.date_of_joining, STATUTORY_ANNUAL_THRESHOLD_YEARS)
	policy_entitlement = (
		policy["annual_leave_after_threshold"]
		if reference >= getdate(policy_threshold_date)
		else policy["annual_leave_before_threshold"]
	)
	statutory_minimum = (
		STATUTORY_ANNUAL_AFTER_DAYS
		if reference >= getdate(statutory_threshold_date)
		else STATUTORY_ANNUAL_BEFORE_DAYS
	)
	return {
		**policy,
		"entitled": int(max(flt(policy_entitlement), statutory_minimum)),
		"statutory_minimum": statutory_minimum,
		"joining_date": getdate(context.date_of_joining),
		"years_of_service": round(date_diff(reference, context.date_of_joining) / 365.25, 2),
	}


def get_annual_leave_balance(employee: str, reference_date: str | None = None, exclude_name: str | None = None) -> dict:
	reference = getdate(reference_date) if reference_date else getdate()
	details = get_annual_leave_entitlement_details(employee, reference)
	taken = get_annual_leave_days_taken(employee, reference.year, exclude_name=exclude_name)
	return {
		**details,
		"taken": taken,
		"balance": flt(details["entitled"]) - flt(taken),
		"year": reference.year,
	}


def get_annual_leave_entitlement(employee: str, date: str = None) -> int:
	return get_annual_leave_entitlement_details(employee, date)["entitled"]


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


@frappe.whitelist(methods=["POST"])
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
