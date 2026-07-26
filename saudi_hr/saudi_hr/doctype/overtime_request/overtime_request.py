import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, flt, getdate, nowdate

from saudi_hr.saudi_hr.utils import (
	assert_doctype_permissions,
	assert_positive_basic_salary,
	get_employee_basic_salary as get_current_basic_salary,
	get_employee_salary_components,
	text_matches_tokens,
)


WORKING_HOURS_PER_MONTH = 240
ANNUAL_OVERTIME_LIMIT_HOURS = 720
COMPENSATORY_LEAVE_FACTOR = 1.5
COMPENSATORY_LEAVE_USE_DAYS = 60
COMPENSATORY_LEAVE_ANNUAL_CAP_DAYS = 30
STANDARD_WORKDAY_HOURS = 8
CASH_PAYMENT = "Cash Payment / بدل نقدي"
COMPENSATORY_LEAVE = "Compensatory Leave / إجازة تعويضية"


def calculate_overtime_breakdown(monthly_actual_wage, monthly_basic, overtime_hours, working_hours_per_month=WORKING_HOURS_PER_MONTH):
	"""Return the Article 107 overtime components in an auditable structure.

	Payable overtime hour = actual hourly wage + 50% of basic hourly wage.
	"""
	actual_wage = flt(monthly_actual_wage)
	basic_wage = flt(monthly_basic)
	hours = flt(overtime_hours)
	monthly_hours = flt(working_hours_per_month)
	if actual_wage <= 0 or basic_wage <= 0 or hours < 0 or monthly_hours <= 0:
		raise ValueError("Overtime inputs must contain positive wages and monthly hours, and non-negative overtime hours.")

	basic_hourly_rate = basic_wage / monthly_hours
	actual_hourly_rate = actual_wage / monthly_hours
	overtime_premium_hourly = basic_hourly_rate * 0.5
	payable_hourly_rate = actual_hourly_rate + overtime_premium_hourly
	return {
		"basic_hourly_rate": round(basic_hourly_rate, 4),
		"actual_hourly_rate": round(actual_hourly_rate, 4),
		"overtime_premium_hourly": round(overtime_premium_hourly, 4),
		"payable_hourly_rate": round(payable_hourly_rate, 4),
		"equivalent_basic_rate": round(payable_hourly_rate / basic_hourly_rate, 4),
		"overtime_amount": round(hours * payable_hourly_rate, 2),
	}


def calculate_compensatory_leave_entitlement(overtime_hours, request_date=None, normal_hours=STANDARD_WORKDAY_HOURS):
	"""Return the minimum compensatory-leave entitlement in the Executive Regulations.

	Each overtime hour produces at least 1.5 paid leave hours. The employer may
	normally schedule the balance within 60 days, and the ordinary annual cap is
	30 leave days unless the parties agree otherwise.
	"""
	hours = flt(overtime_hours)
	workday_hours = flt(normal_hours or STANDARD_WORKDAY_HOURS)
	if hours < 0 or workday_hours <= 0:
		raise ValueError("Overtime hours must be non-negative and normal hours must be positive.")
	leave_hours = round(hours * COMPENSATORY_LEAVE_FACTOR, 2)
	return {
		"factor": COMPENSATORY_LEAVE_FACTOR,
		"leave_hours": leave_hours,
		"leave_days": round(leave_hours / workday_hours, 4),
		"use_by": add_days(getdate(request_date), COMPENSATORY_LEAVE_USE_DAYS) if request_date else None,
		"annual_cap_days": COMPENSATORY_LEAVE_ANNUAL_CAP_DAYS,
	}


def calculate_annual_overtime_status(existing_hours, requested_hours):
	total = max(0, flt(existing_hours)) + max(0, flt(requested_hours))
	return {
		"total_hours": round(total, 2),
		"limit_hours": ANNUAL_OVERTIME_LIMIT_HOURS,
		"consent_required": total > ANNUAL_OVERTIME_LIMIT_HOURS,
	}


class OvertimeRequest(Document):

	WORKING_HOURS_PER_MONTH = WORKING_HOURS_PER_MONTH

	def validate(self):
		self._validate_overtime_hours()
		self._validate_compensation_method()
		self._fetch_salary()
		self._calculate_overtime()
		self._validate_annual_limits()

	def _validate_overtime_hours(self):
		"""العمل الإضافي لا يتجاوز حد معقول (لا تزيد ساعات اليوم الإجمالية عن 12)."""
		total = (self.normal_hours or 0) + (self.overtime_hours or 0)
		if total > 12:
			frappe.throw(
				_("Total working hours per day (normal + overtime) cannot exceed 12 hours.<br>"
				  "لا يمكن أن يتجاوز مجموع ساعات العمل اليومية (العادي + الإضافي) 12 ساعة."),
				title=_("Hours Limit Exceeded / تجاوز حد الساعات"),
			)
		if (self.overtime_hours or 0) <= 0:
			frappe.throw(_("Overtime hours must be greater than 0 / يجب أن تكون ساعات الإضافي أكبر من الصفر"))

	def _validate_compensation_method(self):
		self.compensation_method = self.compensation_method or CASH_PAYMENT
		if self.compensation_method == COMPENSATORY_LEAVE and not (self.written_consent_reference or "").strip():
			frappe.throw(
				_("Written employee consent is required for compensatory leave.<br>"
				  "تلزم موافقة الموظف الكتابية عند اختيار الإجازة التعويضية."),
				title=_("Written Consent Required / الموافقة الكتابية مطلوبة"),
			)

	def _fetch_salary(self):
		"""Fetch actual and basic monthly wages from the active Saudi contract."""
		salary = get_employee_salary_components(self.employee)
		self.monthly_basic = flt(salary.get("basic_salary"))
		self.monthly_actual_wage = flt(salary.get("total_salary") or self.monthly_basic)
		assert_positive_basic_salary(self.employee_name or self.employee, self.monthly_basic, _("calculating overtime / احتساب العمل الإضافي"))
		if self.monthly_actual_wage <= 0:
			frappe.throw(_("Actual monthly wage must be greater than zero / يجب أن يكون الأجر الفعلي الشهري أكبر من صفر"))

	def _calculate_overtime(self):
		"""Apply Article 107: actual hourly wage plus 50% of basic hourly wage."""
		breakdown = calculate_overtime_breakdown(
			self.monthly_actual_wage,
			self.monthly_basic,
			self.overtime_hours,
			self.WORKING_HOURS_PER_MONTH,
		)
		self.basic_hourly_rate = breakdown["basic_hourly_rate"]
		self.actual_hourly_rate = breakdown["actual_hourly_rate"]
		self.overtime_premium_hourly = breakdown["overtime_premium_hourly"]
		self.hourly_rate = breakdown["payable_hourly_rate"]
		self.overtime_rate = breakdown["equivalent_basic_rate"]
		if self.compensation_method == COMPENSATORY_LEAVE:
			entitlement = calculate_compensatory_leave_entitlement(
				self.overtime_hours,
				self.date,
				self.normal_hours,
			)
			self.overtime_amount = 0
			self.compensatory_leave_factor = entitlement["factor"]
			self.compensatory_leave_hours = entitlement["leave_hours"]
			self.compensatory_leave_days = entitlement["leave_days"]
			self.compensatory_leave_use_by = entitlement["use_by"]
		else:
			self.overtime_amount = breakdown["overtime_amount"]
			self.compensatory_leave_factor = COMPENSATORY_LEAVE_FACTOR
			self.compensatory_leave_hours = 0
			self.compensatory_leave_days = 0
			self.compensatory_leave_use_by = None

	def _validate_annual_limits(self):
		if not self.employee or not self.date:
			return

		year = getdate(self.date).year
		rows = frappe.get_all(
			"Overtime Request",
			filters={
				"employee": self.employee,
				"date": ["between", [f"{year}-01-01", f"{year}-12-31"]],
				"docstatus": 1,
			},
			fields=["name", "overtime_hours", "compensation_method", "compensatory_leave_days"],
		)
		rows = [row for row in rows if row.name != self.name]
		annual_status = calculate_annual_overtime_status(
			sum(flt(row.overtime_hours) for row in rows),
			self.overtime_hours,
		)
		self.annual_overtime_hours = annual_status["total_hours"]
		if annual_status["consent_required"] and not (self.annual_limit_consent_reference or "").strip():
			frappe.throw(
				_("The annual overtime total is {0} hours and exceeds the ordinary 720-hour limit. "
				  "Record the worker's consent before continuing.<br>"
				  "بلغ مجموع العمل الإضافي السنوي {0} ساعة وتجاوز الحد المعتاد البالغ 720 ساعة. "
				  "سجّل موافقة العامل قبل المتابعة.").format(annual_status["total_hours"]),
				title=_("Worker Consent Required / موافقة العامل مطلوبة"),
			)

		if self.compensation_method != COMPENSATORY_LEAVE:
			return
		existing_leave_days = sum(
			flt(row.compensatory_leave_days)
			for row in rows
			if row.compensation_method == COMPENSATORY_LEAVE
		)
		total_leave_days = round(existing_leave_days + flt(self.compensatory_leave_days), 4)
		self.annual_compensatory_leave_days = total_leave_days
		if total_leave_days > COMPENSATORY_LEAVE_ANNUAL_CAP_DAYS and not (self.compensatory_leave_exception_reference or "").strip():
			frappe.throw(
				_("Compensatory leave totals {0} days this year and exceeds the ordinary 30-day cap. "
				  "Record the parties' exception agreement before continuing.<br>"
				  "بلغ رصيد الإجازة التعويضية {0} يوماً هذا العام وتجاوز السقف المعتاد البالغ 30 يوماً. "
				  "سجّل اتفاق الطرفين على الاستثناء قبل المتابعة.").format(total_leave_days),
				title=_("Exception Agreement Required / اتفاق الاستثناء مطلوب"),
			)

	def on_submit(self):
		"""عند الاعتماد: إنشاء قيد يومي بدلاً من Additional Salary."""
		if not text_matches_tokens(self.approval_status, "approved", "موافق"):
			frappe.throw(
				_("Cannot submit unless Approval Status is 'Approved'.<br>"
				  "لا يمكن الاعتماد إلا إذا كانت حالة الموافقة 'موافق'."),
				title=_("Not Approved / لم يُوافق بعد"),
			)
		if self.compensation_method == CASH_PAYMENT:
			self._create_overtime_journal_entry()

	def _create_overtime_journal_entry(self):
		"""إنشاء قيد يومي لتحميل مبلغ العمل الإضافي بدلاً من Additional Salary."""
		if self.overtime_journal_entry:
			return

		if not flt(self.overtime_amount) > 0:
			return

		company = self.company

		# ── حساب مصاريف العمل الإضافي ────────────────────────────────────────
		expense_account = (
			frappe.db.get_value(
				"Account",
				{"company": company, "account_name": ["like", "%Overtime%"],
				 "root_type": "Expense", "is_group": 0},
				"name",
			)
			or frappe.db.get_value(
				"Account",
				{"company": company, "account_name": ["like", "%Salary%"],
				 "root_type": "Expense", "is_group": 0},
				"name",
			)
			or frappe.db.get_value(
				"Account",
				{"company": company, "root_type": "Expense", "is_group": 0},
				"name",
			)
		)

		payable_account = (
			frappe.db.get_value(
				"Account",
				{"company": company, "account_name": ["like", "%Salary Payable%"],
				 "root_type": "Liability", "is_group": 0},
				"name",
			)
			or frappe.db.get_value(
				"Account",
				{"company": company, "account_type": "Payable", "is_group": 0},
				"name",
			)
		)

		if not expense_account or not payable_account:
			frappe.msgprint(
				_("Could not find accounts for Overtime Journal Entry. "
				  "Please configure Salary/Overtime expense accounts in the Chart of Accounts.<br>"
				  "تعذّر إيجاد حسابات لقيد العمل الإضافي."),
				title=_("Account Not Found / حساب غير موجود"),
				indicator="orange",
			)
			return

		je = frappe.get_doc({
			"doctype": "Journal Entry",
			"voucher_type": "Journal Entry",
			"company": company,
			"posting_date": self.date or nowdate(),
			"user_remark": (
				f"Overtime Pay — {self.employee_name} — {self.date} — "
				f"{self.overtime_hours}h × {flt(self.hourly_rate):.4f} = {flt(self.overtime_amount):.2f} SAR"
			),
			"accounts": [
				{
					"account": expense_account,
					"debit_in_account_currency": flt(self.overtime_amount),
					"party_type": "Employee",
					"party": self.employee,
					"reference_type": "Overtime Request",
					"reference_name": self.name,
				},
				{
					"account": payable_account,
					"credit_in_account_currency": flt(self.overtime_amount),
					"reference_type": "Overtime Request",
					"reference_name": self.name,
				},
			],
		})
		assert_doctype_permissions("Journal Entry", ("create", "submit"))
		je.insert()
		je.submit()

		self.db_set("overtime_journal_entry", je.name)
		frappe.msgprint(
			_("Journal Entry <b>{0}</b> created for overtime of {1} SAR.<br>"
			  "تم إنشاء القيد اليومي <b>{0}</b> للعمل الإضافي بمبلغ {1} ريال.").format(
				je.name, flt(self.overtime_amount)
			),
			title=_("Journal Entry Created / تم إنشاء القيد"),
			indicator="green",
		)


@frappe.whitelist()
def create_overtime_journal_entry(doc, method=None):
	"""Hook called from hooks.py on_submit — delegates to document method."""
	if isinstance(doc, str):
		doc = frappe.get_doc("Overtime Request", doc)
	# Guard: _create_overtime_journal_entry() already ran inside on_submit(); avoid double-creation
	if not doc.overtime_journal_entry:
		doc._create_overtime_journal_entry()


@frappe.whitelist()
def get_employee_basic_salary(employee):
	"""Return the employee's current basic salary for JS auto-fill."""
	return get_current_basic_salary(employee)


@frappe.whitelist()
def get_employee_overtime_salary(employee):
	"""Return the wage components needed for the Article 107 preview."""
	return get_employee_salary_components(employee)
