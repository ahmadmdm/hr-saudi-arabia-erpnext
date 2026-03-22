import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate, getdate, date_diff, add_days

# معدلات GOSI الافتراضية
GOSI_SAUDI_EMP = 10.0      # اقتطاع الموظف السعودي
GOSI_NON_SAUDI_EMP = 0.0   # الموظف غير السعودي لا يُقتطع
GOSI_MAX_BASE = 45000.0


class SaudiMonthlyPayroll(Document):

	def validate(self):
		self.period_label = f"{self.month} {self.year}"
		if not self.status:
			self.status = "Draft / مسودة"
		self._recalculate_totals()

	def _recalculate_totals(self):
		"""إعادة حساب الإجماليات من الجدول الفرعي."""
		self.total_employees = len(self.employees)
		self.total_gross = round(sum(flt(r.gross_salary) for r in self.employees), 2)
		self.total_gosi_deductions = round(sum(flt(r.gosi_employee_deduction) for r in self.employees), 2)
		self.total_overtime = round(sum(flt(r.overtime_addition) for r in self.employees), 2)
		self.total_net_payable = round(sum(flt(r.net_salary) for r in self.employees), 2)

	def on_submit(self):
		self.db_set("status", "Completed / مكتمل")

	def on_cancel(self):
		self.db_set("status", "Cancelled / ملغى")


# ─── Whitelist API Methods ───────────────────────────────────────────────────────

@frappe.whitelist()
def fetch_employees(doc_name: str):
	"""
	جلب جميع الموظفين النشطين للشركة وملء الجدول الفرعي.
	يُستدعى من زر JavaScript.
	"""
	doc = frappe.get_doc("Saudi Monthly Payroll", doc_name)
	frappe.has_permission("Saudi Monthly Payroll", "write", doc=doc, throw=True)

	employees = frappe.get_all(
		"Employee",
		filters={"company": doc.company, "status": "Active"},
		fields=["name", "employee_name", "department", "nationality"],
		order_by="employee_name",
	)

	if not employees:
		doc.set("employees", [])
		doc._recalculate_totals()
		doc.save(ignore_permissions=True)
		return {"count": 0, "total_net": 0.0}

	emp_names = [e["name"] for e in employees]

	# ── جلب الرواتب دفعةً واحدة (batch) لتجنب N+1 queries ──────────────────
	sal_rows = frappe.db.sql(
		"""SELECT employee, base FROM `tabSalary Structure Assignment`
		   WHERE employee IN %(names)s AND docstatus=1
		   ORDER BY from_date DESC""",
		{"names": emp_names},
		as_dict=True,
	)
	# أحدث راتب أساسي لكل موظف (القائمة مرتّبة تنازلياً، نأخذ أول ظهور)
	salary_map = {}
	for row in sal_rows:
		if row["employee"] not in salary_map:
			salary_map[row["employee"]] = flt(row["base"])

	# ── جلب بدلات العقود دفعةً واحدة ──────────────────────────────────────
	contract_rows = frappe.db.sql(
		"""SELECT employee, housing_allowance, transport_allowance, other_allowances
		   FROM `tabSaudi Employment Contract`
		   WHERE employee IN %(names)s
		     AND contract_status = 'Active / نشط'
		     AND docstatus = 1
		   ORDER BY start_date DESC""",
		{"names": emp_names},
		as_dict=True,
	)
	contract_map = {}
	for row in contract_rows:
		if row["employee"] not in contract_map:
			contract_map[row["employee"]] = row

	# ── حساب نطاق الشهر مرة واحدة ──────────────────────────────────────────
	import calendar as _cal
	month_num = _month_name_to_num(doc.month)
	month_start = f"{doc.year}-{month_num:02d}-01"
	last_day = _cal.monthrange(int(doc.year), month_num)[1]
	month_end = f"{doc.year}-{month_num:02d}-{last_day:02d}"

	# ── جلب الإجازات المرضية دفعةً واحدة ───────────────────────────────────
	sick_rows = frappe.db.sql(
		"""SELECT employee, leave_pay_amount, total_days
		   FROM `tabSaudi Sick Leave`
		   WHERE employee IN %(names)s AND docstatus=1
		     AND from_date >= %(start)s AND to_date <= %(end)s""",
		{"names": emp_names, "start": month_start, "end": month_end},
		as_dict=True,
	)
	sick_map: dict = {}
	for sr in sick_rows:
		sick_map.setdefault(sr["employee"], []).append(sr)

	# ── جلب العمل الإضافي المعتمد دفعةً واحدة ───────────────────────────────
	ot_rows = frappe.db.sql(
		"""SELECT employee, overtime_amount
		   FROM `tabOvertime Request`
		   WHERE employee IN %(names)s AND docstatus=1
		     AND approval_status = 'Approved / موافق'
		     AND date BETWEEN %(start)s AND %(end)s""",
		{"names": emp_names, "start": month_start, "end": month_end},
		as_dict=True,
	)
	ot_map: dict = {}
	for ot in ot_rows:
		ot_map[ot["employee"]] = ot_map.get(ot["employee"], 0.0) + flt(ot["overtime_amount"])

	# مسح الجدول الحالي
	doc.set("employees", [])

	for emp in employees:
		basic = salary_map.get(emp["name"], 0.0)
		contract = contract_map.get(emp["name"])
		housing = flt(contract["housing_allowance"]) if contract else 0.0
		transport = flt(contract["transport_allowance"]) if contract else 0.0
		other = flt(contract["other_allowances"]) if contract else 0.0
		gross = round(basic + housing + transport + other, 2)

		nat = (emp.get("nationality") or "").lower()
		is_saudi = nat in ("saudi", "سعودي", "sa", "saudi arabia")
		gosi_rate = GOSI_SAUDI_EMP if is_saudi else GOSI_NON_SAUDI_EMP
		gosi_base = min(basic, GOSI_MAX_BASE)
		gosi_deduction = round(gosi_base * gosi_rate / 100, 2)

		daily = round(basic / last_day, 2)
		sick_deduction = 0.0
		for sr in sick_map.get(emp["name"], []):
			full_pay = flt(sr["total_days"]) * daily
			actual_pay = flt(sr["leave_pay_amount"])
			if full_pay > actual_pay:
				sick_deduction += round(full_pay - actual_pay, 2)

		overtime = round(ot_map.get(emp["name"], 0.0), 2)
		net = round(gross - gosi_deduction - sick_deduction + overtime, 2)

		doc.append("employees", {
			"employee": emp["name"],
			"employee_name": emp.get("employee_name", ""),
			"department": emp.get("department", ""),
			"nationality": emp.get("nationality", ""),
			"basic_salary": basic,
			"housing_allowance": housing,
			"transport_allowance": transport,
			"other_allowances": other,
			"gross_salary": gross,
			"gosi_employee_deduction": gosi_deduction,
			"sick_leave_deduction": round(sick_deduction, 2),
			"overtime_addition": overtime,
			"net_salary": net,
		})

	doc._recalculate_totals()
	doc.save(ignore_permissions=True)
	return {"count": len(employees), "total_net": doc.total_net_payable}


@frappe.whitelist()
def calculate_employee_row(employee: str, month: str, year: int):
	"""
	حساب الراتب الشهري لموظف واحد وإرجاع dict للتحديث في الواجهة.
	"""
	emp_doc = frappe.get_all(
		"Employee",
		filters={"name": employee},
		fields=["name", "employee_name", "department", "nationality"],
		limit=1,
	)
	if not emp_doc:
		frappe.throw(_("Employee not found"))
	row = _build_employee_row(emp_doc[0], month, int(year))
	return row


@frappe.whitelist()
def create_journal_entry_from_payroll(doc_name: str):
	"""
	إنشاء قيد يومي مباشر من بيانات Saudi Monthly Payroll
	بدلاً من الاعتماد على Payroll Entry في ERPNext/HRMS.
	يُستدعى من زر "Create Journal Entry".
	"""
	import calendar as _cal
	doc = frappe.get_doc("Saudi Monthly Payroll", doc_name)
	frappe.has_permission("Saudi Monthly Payroll", "write", doc=doc, throw=True)

	if doc.payroll_journal_entry:
		frappe.throw(
			_(f"Journal Entry already created: {doc.payroll_journal_entry}<br>"
			  f"القيد اليومي موجود بالفعل: {doc.payroll_journal_entry}"),
			title=_("Already Created / موجودة مسبقاً"),
		)

	if not doc.employees:
		frappe.throw(
			_("No employees in the payroll. Please fetch employees first.<br>"
			  "لا يوجد موظفون. الرجاء جلب الموظفين أولاً."),
			title=_("No Employees / لا يوجد موظفون"),
		)

	company = doc.company
	month_num = _month_name_to_num(doc.month)
	last_day = _cal.monthrange(int(doc.year), month_num)[1]
	posting_date = f"{doc.year}-{month_num:02d}-{last_day:02d}"

	# ── حسابات الإجمالي ─────────────────────────────────────────────────────
	total_gross = flt(doc.total_gross)
	total_gosi = flt(doc.total_gosi_deductions)
	total_net = flt(doc.total_net_payable)

	# ── الحسابات المحاسبية ───────────────────────────────────────────────────
	expense_account = (
		frappe.db.get_value(
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
	gosi_payable_account = (
		frappe.db.get_value(
			"Account",
			{"company": company, "account_name": ["like", "%GOSI%"],
			 "root_type": "Liability", "is_group": 0},
			"name",
		)
		or payable_account
	)

	if not expense_account or not payable_account:
		frappe.throw(
			_("Could not find Salary expense/payable accounts. "
			  "Please configure them in the Chart of Accounts.<br>"
			  "تعذّر إيجاد حسابات الرواتب. يرجى إعداد شجرة الحسابات."),
			title=_("Account Not Found / حساب غير موجود"),
		)

	# ── بناء قيود الحساب ────────────────────────────────────────────────────
	# Dr. Salary Expense    → إجمالي الرواتب
	# Cr. GOSI Payable      → اشتراكات GOSI للموظف
	# Cr. Salary Payable    → صافي المستحق للموظفين
	accounts = [
		{
			"account": expense_account,
			"debit_in_account_currency": total_gross,
			"reference_type": "Saudi Monthly Payroll",
			"reference_name": doc.name,
		},
	]
	if total_gosi > 0:
		accounts.append({
			"account": gosi_payable_account,
			"credit_in_account_currency": total_gosi,
			"reference_type": "Saudi Monthly Payroll",
			"reference_name": doc.name,
		})
	accounts.append({
		"account": payable_account,
		"credit_in_account_currency": total_net,
		"reference_type": "Saudi Monthly Payroll",
		"reference_name": doc.name,
	})

	je = frappe.get_doc({
		"doctype": "Journal Entry",
		"voucher_type": "Journal Entry",
		"company": company,
		"posting_date": posting_date,
		"user_remark": (
			f"Monthly Payroll — {doc.month} {doc.year} — "
			f"{doc.total_employees} employees — Net: {total_net:,.2f} SAR"
		),
		"accounts": accounts,
	})
	je.flags.ignore_permissions = True
	je.insert()
	je.submit()

	doc.db_set("payroll_journal_entry", je.name)
	doc.db_set("status", "Completed / مكتمل")

	frappe.msgprint(
		_(f"Journal Entry <b>{je.name}</b> created for {doc.month} {doc.year} payroll.<br>"
		  f"تم إنشاء القيد اليومي <b>{je.name}</b> لرواتب {doc.month} {doc.year}."),
		title=_("Journal Entry Created / تم إنشاء القيد"),
		indicator="green",
	)
	return je.name


# ─── Private Helpers ────────────────────────────────────────────────────────────

def _build_employee_row(emp: dict, month: str, year: int) -> dict:
	"""بناء بيانات صف الموظف الواحد في الجدول الفرعي."""
	# جلب الراتب من هيكل الراتب
	sal = frappe.get_all(
		"Salary Structure Assignment",
		filters={"employee": emp["name"], "docstatus": 1},
		fields=["base"],
		order_by="from_date desc",
		limit=1,
	)
	basic = flt(sal[0].base) if sal else 0.0

	# جلب بدلات العقد إن وجد
	contract = frappe.get_all(
		"Saudi Employment Contract",
		filters={
			"employee": emp["name"],
			"contract_status": "Active / نشط",
			"docstatus": 1,
		},
		fields=["housing_allowance", "transport_allowance", "other_allowances"],
		order_by="start_date desc",
		limit=1,
	)
	housing = flt(contract[0].housing_allowance) if contract else 0.0
	transport = flt(contract[0].transport_allowance) if contract else 0.0
	other = flt(contract[0].other_allowances) if contract else 0.0

	gross = round(basic + housing + transport + other, 2)

	# اقتطاع GOSI للموظف
	nat = (emp.get("nationality") or "").lower()
	is_saudi = nat in ("saudi", "سعودي", "sa", "saudi arabia")
	gosi_rate = GOSI_SAUDI_EMP if is_saudi else GOSI_NON_SAUDI_EMP
	gosi_base = min(basic, GOSI_MAX_BASE)
	gosi_deduction = round(gosi_base * gosi_rate / 100, 2)

	# خصم الإجازة المرضية (إن وجدت في الشهر الحالي)
	month_num = _month_name_to_num(month)
	month_start = f"{year}-{month_num:02d}-01"
	import calendar
	last_day = calendar.monthrange(int(year), month_num)[1]
	month_end = f"{year}-{month_num:02d}-{last_day:02d}"

	sick_rows = frappe.get_all(
		"Saudi Sick Leave",
		filters={
			"employee": emp["name"],
			"docstatus": 1,
			"from_date": [">=", month_start],
			"to_date": ["<=", month_end],
		},
		fields=["leave_pay_amount", "daily_salary", "total_days", "pay_rate"],
	)
	# الخصم = الفرق بين الأجر الكامل والأجر المستحق
	sick_deduction = 0.0
	daily = round(basic / last_day, 2)  # الأجر اليومي يعتمد على أيام الشهر الفعلية
	for sr in sick_rows:
		full_pay = flt(sr.total_days) * daily
		actual_pay = flt(sr.leave_pay_amount)
		if full_pay > actual_pay:
			sick_deduction += round(full_pay - actual_pay, 2)

	# إضافة العمل الإضافي المعتمد في الشهر
	ot_rows = frappe.get_all(
		"Overtime Request",
		filters={
			"employee": emp["name"],
			"docstatus": 1,
			"approval_status": "Approved / موافق",
			"date": ["between", [month_start, month_end]],
		},
		fields=["overtime_amount"],
	)
	overtime = round(sum(flt(r.overtime_amount) for r in ot_rows), 2)

	net = round(gross - gosi_deduction - sick_deduction + overtime, 2)

	return {
		"employee": emp["name"],
		"employee_name": emp.get("employee_name", ""),
		"department": emp.get("department", ""),
		"nationality": emp.get("nationality", ""),
		"basic_salary": basic,
		"housing_allowance": housing,
		"transport_allowance": transport,
		"other_allowances": other,
		"gross_salary": gross,
		"gosi_employee_deduction": gosi_deduction,
		"sick_leave_deduction": round(sick_deduction, 2),
		"overtime_addition": overtime,
		"net_salary": net,
	}


def _month_name_to_num(month_label: str) -> int:
	"""تحويل اسم الشهر الثنائي إلى رقم."""
	MONTHS = {
		"january": 1, "february": 2, "march": 3, "april": 4,
		"may": 5, "june": 6, "july": 7, "august": 8,
		"september": 9, "october": 10, "november": 11, "december": 12,
		"يناير": 1, "فبراير": 2, "مارس": 3, "أبريل": 4,
		"مايو": 5, "يونيو": 6, "يوليو": 7, "أغسطس": 8,
		"سبتمبر": 9, "أكتوبر": 10, "نوفمبر": 11, "ديسمبر": 12,
	}
	# الاسم قد يكون "January / يناير"
	for part in (month_label or "").replace("/", " ").split():
		key = part.strip().lower()
		if key in MONTHS:
			return MONTHS[key]
	return 1


def _get_payable_account(company: str) -> str:
	"""الحصول على حساب الرواتب المستحقة للشركة."""
	account = frappe.db.get_value(
		"Account",
		{"company": company, "account_type": "Payable", "is_group": 0},
		"name",
	)
	return account or ""
