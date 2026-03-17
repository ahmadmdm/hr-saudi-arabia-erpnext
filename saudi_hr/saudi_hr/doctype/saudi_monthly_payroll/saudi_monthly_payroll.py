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

	# مسح الجدول الحالي
	doc.set("employees", [])

	for emp in employees:
		row = _build_employee_row(emp, doc.month, doc.year)
		doc.append("employees", row)

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
def create_payroll_entry(doc_name: str):
	"""
	إنشاء Payroll Entry في ERPNext من بيانات Saudi Monthly Payroll.
	يُستدعى من زر "Create Payroll Entry".
	"""
	doc = frappe.get_doc("Saudi Monthly Payroll", doc_name)
	frappe.has_permission("Saudi Monthly Payroll", "write", doc=doc, throw=True)

	if doc.payroll_entry:
		frappe.throw(
			_(f"Payroll Entry already created: {doc.payroll_entry}<br>"
			  f"قسيمة الراتب موجودة بالفعل: {doc.payroll_entry}"),
			title=_("Already Created / موجودة مسبقاً"),
		)

	if not doc.employees:
		frappe.throw(
			_("No employees in the payroll. Please fetch employees first.<br>"
			  "لا يوجد موظفون. الرجاء جلب الموظفين أولاً."),
			title=_("No Employees / لا يوجد موظفون"),
		)

	# تحديد نطاق تاريخ الشهر
	month_num = _month_name_to_num(doc.month)
	start_date = f"{doc.year}-{month_num:02d}-01"
	import calendar
	last_day = calendar.monthrange(int(doc.year), month_num)[1]
	end_date = f"{doc.year}-{month_num:02d}-{last_day:02d}"

	# إنشاء Payroll Entry
	pe = frappe.get_doc({
		"doctype": "Payroll Entry",
		"company": doc.company,
		"start_date": start_date,
		"end_date": end_date,
		"payroll_frequency": "Monthly",
		"posting_date": doc.posting_date or end_date,
		"payroll_payable_account": _get_payable_account(doc.company),
	})
	pe.flags.ignore_permissions = True
	pe.insert()

	# ربط قسيمة الرواتب بالسجل
	doc.db_set("payroll_entry", pe.name)
	doc.db_set("status", "Processing / قيد المعالجة")

	frappe.msgprint(
		_(f"Payroll Entry <b>{pe.name}</b> created successfully for {doc.month} {doc.year}.<br>"
		  f"تم إنشاء قسيمة الراتب <b>{pe.name}</b> بنجاح لـ {doc.month} {doc.year}."),
		title=_("Payroll Entry Created / تم إنشاء القسيمة"),
		indicator="green",
	)
	return pe.name


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
	daily = round(basic / 30, 2)
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
