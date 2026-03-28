from io import BytesIO

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr, flt, getdate
from frappe.utils.file_manager import save_file
from frappe.utils.xlsxutils import make_xlsx
from openpyxl import load_workbook

from saudi_hr.saudi_hr.doctype.employee_loan.employee_loan import apply_payroll_loan_deductions, get_due_loan_deduction, revert_payroll_loan_deductions
from saudi_hr.saudi_hr.utils import get_employee_salary_components

# معدلات GOSI الافتراضية
GOSI_SAUDI_EMP = 10.0      # اقتطاع الموظف السعودي
GOSI_NON_SAUDI_EMP = 0.0   # الموظف غير السعودي لا يُقتطع
GOSI_MAX_BASE = 45000.0
PREFERRED_SOURCE_WORKBOOK_SHEETS = ("كشف الرواتب طباعة", "كشف الرواتب", "كشف المصدر")
EMPLOYEE_SETUP_TEMPLATE_HEADERS = [
	"source_row",
	"payroll_employee_id",
	"payroll_employee_name",
	"national_id",
	"company",
	"department",
	"designation",
	"employee_number",
	"first_name",
	"middle_name",
	"last_name",
	"gender",
	"date_of_birth",
	"date_of_joining",
	"status",
	"remarks",
]

WORKBOOK_HEADER_ALIASES = {
	"employee_id": {"الرقم الوظيفي"},
	"employee_name": {"الاسم", "الإسم"},
	"designation": {"الوظيفة"},
	"work_location": {"مكان العمل"},
	"department": {"الإدارة"},
	"salary_mode": {"بنك كاش", "بنك / كاش", "بنك/كاش"},
	"basic_salary": {"الاساسي"},
	"housing_allowance": {"بدل السكن"},
	"transport_allowance": {"بدل المواصلات"},
	"other_allowances": {"بدلات اخرى"},
	"gross_salary": {"الاجمالي", "اجمالي البدلات", "إجمالي البدلات"},
	"working_days": {"ايام العمل"},
	"absence_days": {"ايام الغياب", "عدد أيام الغياب"},
	"absence_value": {"قيمة ايام الغياب"},
	"late_hours": {"ساعات التأخير"},
	"late_value": {"قيمة التأخير"},
	"gosi_deduction": {"خصم التأمينات"},
	"additions": {"إضافات", "الإضافي", "اضافي", "إضافي"},
	"manual_deduction": {"خصم", "خصم السلف", "خصم السلف والاستقطاعات", "خصم الجزاءات"},
	"total_deductions": {"اجمالي الخصم", "إجمالي الخصم"},
	"net_salary": {"صافى الراتب", "صافي الراتب"},
	"national_id": {"رقم الهوية"},
	"gosi_registration": {"التأمينات", "رقم اشتراك التأمينات"},
}


class SaudiMonthlyPayroll(Document):

	def validate(self):
		self.period_label = f"{self.month} {self.year}"
		if not self.status:
			self.status = "Draft / مسودة"
		self._recalculate_employee_rows()
		self._recalculate_totals()

	def _recalculate_employee_rows(self):
		for row in self.employees:
			gross = round(
				flt(row.basic_salary)
				+ flt(row.housing_allowance)
				+ flt(row.transport_allowance)
				+ flt(row.other_allowances),
				2,
			)
			total_deductions = round(
				flt(row.gosi_employee_deduction)
				+ flt(row.sick_leave_deduction)
				+ flt(row.loan_deduction)
				+ flt(getattr(row, "other_deductions", 0.0)),
				2,
			)
			row.gross_salary = gross
			row.total_deductions = total_deductions
			row.net_salary = round(gross + flt(row.overtime_addition) - total_deductions, 2)

	def _recalculate_totals(self):
		"""إعادة حساب الإجماليات من الجدول الفرعي."""
		self.total_employees = len(self.employees)
		self.total_gross = round(sum(flt(r.gross_salary) for r in self.employees), 2)
		self.total_gosi_deductions = round(sum(flt(r.gosi_employee_deduction) for r in self.employees), 2)
		self.total_sick_deductions = round(sum(flt(r.sick_leave_deduction) for r in self.employees), 2)
		self.total_loan_deductions = round(sum(flt(r.loan_deduction) for r in self.employees), 2)
		self.total_other_deductions = round(sum(flt(getattr(r, "other_deductions", 0.0)) for r in self.employees), 2)
		self.total_overtime = round(sum(flt(r.overtime_addition) for r in self.employees), 2)
		self.total_net_payable = round(sum(flt(r.net_salary) for r in self.employees), 2)

	def on_submit(self):
		apply_payroll_loan_deductions(self)
		self.db_set("status", "Completed / مكتمل")

	def on_cancel(self):
		revert_payroll_loan_deductions(self)
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
		fields=_get_employee_fetch_fields(),
		order_by="employee_name",
	)

	if not employees:
		doc.set("employees", [])
		doc._recalculate_totals()
		doc.save(ignore_permissions=True)
		return {"count": 0, "total_net": 0.0}

	emp_names = [e["name"] for e in employees]

	# ── جلب بدلات العقود ورواتبها دفعةً واحدة ───────────────────────────────
	contract_rows = frappe.db.sql(
		"""SELECT employee, basic_salary, housing_allowance, transport_allowance, other_allowances, total_salary
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

	loan_map = {emp_name: get_due_loan_deduction(emp_name, month_num, int(doc.year)) for emp_name in emp_names}

	# مسح الجدول الحالي
	doc.set("employees", [])

	for emp in employees:
		contract = contract_map.get(emp["name"])
		basic = flt(contract["basic_salary"]) if contract else 0.0
		if not basic:
			basic = get_employee_salary_components(emp["name"])["basic_salary"]
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
		loan_info = loan_map.get(emp["name"], {"loan_deduction": 0.0, "installment_names": []})
		loan_deduction = round(flt(loan_info.get("loan_deduction")), 2)
		total_deductions = round(gosi_deduction + sick_deduction + loan_deduction, 2)
		net = round(gross + overtime - total_deductions, 2)

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
			"loan_deduction": loan_deduction,
			"total_deductions": total_deductions,
			"overtime_addition": overtime,
			"loan_installments": ", ".join(loan_info.get("installment_names", [])),
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
		fields=_get_employee_fetch_fields(),
		limit=1,
	)
	if not emp_doc:
		frappe.throw(_("Employee not found"))
	row = _build_employee_row(emp_doc[0], month, int(year))
	return row


@frappe.whitelist()
def import_payroll_workbook(doc_name: str, file_url: str | None = None):
	"""استيراد ملف رواتب خارجي إلى كشف الرواتب الشهري."""
	doc = frappe.get_doc("Saudi Monthly Payroll", doc_name)
	frappe.has_permission("Saudi Monthly Payroll", "write", doc=doc, throw=True)

	workbook_url = file_url or doc.source_workbook
	if not workbook_url:
		frappe.throw(_("Attach the source payroll workbook first.<br>أرفق ملف الرواتب المصدر أولاً."))

	analysis = _preview_payroll_workbook(doc.company, workbook_url)
	import_rows = analysis["import_rows"]
	warnings = analysis["warnings"]

	if not import_rows:
		frappe.throw(
			_(
				"Could not import any payroll rows from the workbook. "
				f"Employees in company: {analysis['company_employee_count']}. "
				f"Unmatched workbook rows: {analysis['unmatched_rows']}. "
				f"Sample IDs: {', '.join(analysis['sample_unmatched'][:5]) or 'N/A'}"
				"<br>تعذّر استيراد أي صفوف رواتب من الملف بسبب عدم وجود مطابقة مع بيانات الموظفين الحالية."
			),
			title=_("No Importable Rows / لا توجد صفوف قابلة للاستيراد"),
		)

	doc.source_workbook = workbook_url
	doc.set("employees", [])
	for row in import_rows:
		doc.append("employees", row)

	doc._recalculate_employee_rows()
	doc._recalculate_totals()
	doc.save(ignore_permissions=True)

	return {
		"count": len(import_rows),
		"warnings": warnings,
		"total_net": doc.total_net_payable,
	}


@frappe.whitelist()
def preview_payroll_workbook_import(doc_name: str, file_url: str | None = None):
	"""معاينة ملف الرواتب قبل الاستيراد وإظهار نسبة المطابقة."""
	doc = frappe.get_doc("Saudi Monthly Payroll", doc_name)
	frappe.has_permission("Saudi Monthly Payroll", "read", doc=doc, throw=True)
	workbook_url = file_url or doc.source_workbook
	if not workbook_url:
		frappe.throw(_("Attach the source payroll workbook first.<br>أرفق ملف الرواتب المصدر أولاً."))
	return _preview_payroll_workbook(doc.company, workbook_url)


@frappe.whitelist()
def download_payroll_workbook_gap_report(doc_name: str, file_url: str | None = None):
	"""إنشاء ملف Excel لصفوف الرواتب غير المطابقة مع بيانات الموظفين الحالية."""
	doc = frappe.get_doc("Saudi Monthly Payroll", doc_name)
	frappe.has_permission("Saudi Monthly Payroll", "read", doc=doc, throw=True)
	workbook_url = file_url or doc.source_workbook
	if not workbook_url:
		frappe.throw(_("Attach the source payroll workbook first.<br>أرفق ملف الرواتب المصدر أولاً."))

	summary = _preview_payroll_workbook(doc.company, workbook_url)
	gap_rows = _build_gap_report_rows(summary.get("unmatched_details", []))
	if len(gap_rows) == 1:
		frappe.throw(
			_("No unmatched workbook rows were found.<br>لا توجد صفوف غير مطابقة في ملف الرواتب."),
			title=_("No Gaps / لا توجد فجوات"),
		)

	file_name = f"payroll-workbook-gaps-{doc.name}.xlsx"
	file_doc = save_file(file_name, make_xlsx(gap_rows, "Payroll Gaps").getvalue(), doc.doctype, doc.name, is_private=1)
	return {"file_url": file_doc.file_url, "file_name": file_doc.file_name, "row_count": len(gap_rows) - 1}


@frappe.whitelist()
def download_employee_setup_template(doc_name: str, file_url: str | None = None):
	"""إنشاء قالب إعداد موظفين من صفوف الرواتب غير المطابقة."""
	doc = frappe.get_doc("Saudi Monthly Payroll", doc_name)
	frappe.has_permission("Saudi Monthly Payroll", "read", doc=doc, throw=True)
	workbook_url = file_url or doc.source_workbook
	if not workbook_url:
		frappe.throw(_("Attach the source payroll workbook first.<br>أرفق ملف الرواتب المصدر أولاً."))

	summary = _preview_payroll_workbook(doc.company, workbook_url)
	template_rows = _build_employee_setup_template_rows(doc.company, summary.get("unmatched_details", []))
	if len(template_rows) == 1:
		frappe.throw(
			_("No unmatched workbook rows were found.<br>لا توجد صفوف غير مطابقة في ملف الرواتب."),
			title=_("No Gaps / لا توجد فجوات"),
		)

	file_name = f"employee-setup-template-{doc.name}.xlsx"
	file_doc = save_file(file_name, make_xlsx(template_rows, "Employee Setup").getvalue(), doc.doctype, doc.name, is_private=1)
	return {"file_url": file_doc.file_url, "file_name": file_doc.file_name, "row_count": len(template_rows) - 1}


@frappe.whitelist()
def import_employee_setup_workbook(doc_name: str, file_url: str | None = None):
	"""استيراد ملف إعداد الموظفين المكتمل وإنشاء سجلات Employee الناقصة."""
	doc = frappe.get_doc("Saudi Monthly Payroll", doc_name)
	frappe.has_permission("Saudi Monthly Payroll", "write", doc=doc, throw=True)
	workbook_url = file_url or doc.employee_setup_workbook
	if not workbook_url:
		frappe.throw(_("Attach the completed employee setup workbook first.<br>أرفق ملف إعداد الموظفين المكتمل أولاً."))

	doc.db_set("employee_setup_workbook", workbook_url)
	rows = _extract_employee_setup_rows(_get_attached_file_content(workbook_url))
	created, skipped = _import_employee_setup_rows(doc.company, rows)
	return {"created_count": len(created), "skipped": skipped, "created_employees": created}


@frappe.whitelist()
def autofill_employee_setup_workbook_names(doc_name: str, file_url: str | None = None):
	"""تعبئة حقول الاسم تلقائياً في ملف إعداد الموظفين من اسم الموظف القادم من ملف الرواتب."""
	doc = frappe.get_doc("Saudi Monthly Payroll", doc_name)
	frappe.has_permission("Saudi Monthly Payroll", "write", doc=doc, throw=True)
	workbook_url = file_url or doc.employee_setup_workbook
	if not workbook_url:
		frappe.throw(_("Attach the employee setup workbook first.<br>أرفق ملف إعداد الموظفين أولاً."))

	rows = _extract_employee_setup_rows(_get_attached_file_content(workbook_url))
	autofilled_rows, updated_count = _autofill_employee_setup_names(rows)
	file_name = f"employee-setup-autofilled-{doc.name}.xlsx"
	file_doc = save_file(
		file_name,
		make_xlsx(_build_employee_setup_workbook_rows(autofilled_rows), "Employee Setup").getvalue(),
		doc.doctype,
		doc.name,
		is_private=1,
	)
	doc.db_set("employee_setup_workbook", file_doc.file_url)
	return {
		"file_url": file_doc.file_url,
		"file_name": file_doc.file_name,
		"updated_count": updated_count,
	}


@frappe.whitelist()
def create_basic_employees_from_payroll(
	doc_name: str,
	default_gender: str,
	default_date_of_birth,
	default_date_of_joining=None,
	default_status: str = "Active",
):
	"""Create placeholder Employee records for imported payroll rows that are not linked yet."""
	doc = frappe.get_doc("Saudi Monthly Payroll", doc_name)
	frappe.has_permission("Saudi Monthly Payroll", "write", doc=doc, throw=True)
	defaults = _normalize_basic_employee_creation_defaults(
		default_gender,
		default_date_of_birth,
		default_date_of_joining or doc.posting_date,
		default_status,
	)
	created, linked, skipped = _create_basic_employees_for_payroll(doc, defaults)
	doc.save(ignore_permissions=True)

	remaining_unlinked = sum(1 for row in doc.employees if not cstr(row.employee or "").strip())
	return {
		"created_count": len(created),
		"linked_count": linked,
		"created_employees": created,
		"skipped": skipped,
		"remaining_unlinked_rows": remaining_unlinked,
	}


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
	total_sick = flt(doc.total_sick_deductions)
	total_loan = flt(doc.total_loan_deductions)
	total_other = flt(getattr(doc, "total_other_deductions", 0.0))
	total_overtime = flt(doc.total_overtime)
	total_net = flt(doc.total_net_payable)
	total_salary_cost = round(total_gross + total_overtime - total_sick - total_other, 2)

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
	payable_account = _get_payroll_payable_account(company)
	gosi_payable_account = (
		frappe.db.get_value(
			"Account",
			{"company": company, "account_name": ["like", "%GOSI%"],
			 "root_type": "Liability", "is_group": 0},
			"name",
		)
		or payable_account
	)
	loan_receivable_account = (
		frappe.db.get_value(
			"Account",
			{"company": company, "account_name": ["like", "%Loan%"], "root_type": "Asset", "is_group": 0},
			"name",
		)
		or frappe.db.get_value(
			"Account",
			{"company": company, "account_type": "Receivable", "is_group": 0},
			"name",
		)
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
			"debit_in_account_currency": total_salary_cost,
		},
	]
	if total_gosi > 0:
		accounts.append({
			"account": gosi_payable_account,
			"credit_in_account_currency": total_gosi,
		})
	if total_loan > 0 and loan_receivable_account:
		accounts.append({
			"account": loan_receivable_account,
			"credit_in_account_currency": total_loan,
		})
	accounts.append({
		"account": payable_account,
		"credit_in_account_currency": total_net,
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


def _get_payroll_payable_account(company: str) -> str | None:
	accounts = frappe.get_all(
		"Account",
		filters={"company": company, "root_type": "Liability", "is_group": 0},
		fields=["name", "account_name", "account_type"],
	)

	def rank(account: dict):
		name = cstr(account.get("account_name") or account.get("name") or "").strip().lower()
		account_type = cstr(account.get("account_type") or "").strip().lower()

		if "payroll payable" in name:
			return (0, name)
		if "salary payable" in name:
			return (1, name)
		if "payroll" in name and account_type != "payable":
			return (2, name)
		if "salary" in name and account_type != "payable":
			return (3, name)
		if "payable" in name and account_type != "payable":
			return (4, name)
		return (99, name)

	preferred = [account for account in accounts if rank(account)[0] < 99]
	if preferred:
		preferred.sort(key=rank)
		return preferred[0]["name"]

	payable_accounts = [account for account in accounts if cstr(account.get("account_type") or "").strip().lower() == "payable"]
	if payable_accounts:
		frappe.throw(
			_(
				"Could not find a payroll payable liability account. Generic payable accounts require Party details. "
				"Please configure an account such as Payroll Payable or Salary Payable.<br>"
				"تعذّر العثور على حساب التزامات مناسب للرواتب. حسابات الدائنين العامة تتطلب طرفاً محاسبياً، لذا يرجى إعداد حساب مثل Payroll Payable أو Salary Payable."
			),
			title=_("Payroll Payable Account Missing / حساب رواتب دائن غير موجود"),
		)

	return None


# ─── Private Helpers ────────────────────────────────────────────────────────────

def _build_employee_row(emp: dict, month: str, year: int) -> dict:
	"""بناء بيانات صف الموظف الواحد في الجدول الفرعي."""
	salary = get_employee_salary_components(emp["name"])
	basic = salary["basic_salary"]
	housing = salary["housing_allowance"]
	transport = salary["transport_allowance"]
	other = salary["other_allowances"]

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
	loan_info = get_due_loan_deduction(emp["name"], month_num, int(year))
	loan_deduction = round(flt(loan_info.get("loan_deduction")), 2)
	total_deductions = round(gosi_deduction + sick_deduction + loan_deduction, 2)

	net = round(gross + overtime - total_deductions, 2)

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
		"loan_deduction": loan_deduction,
		"other_deductions": 0.0,
		"total_deductions": total_deductions,
		"overtime_addition": overtime,
		"loan_installments": ", ".join(loan_info.get("installment_names", [])),
		"net_salary": net,
	}


def _extract_source_workbook_rows(content: bytes) -> list[dict]:
	workbook = load_workbook(BytesIO(content), data_only=True, read_only=True)
	worksheet = _get_source_workbook_sheet(workbook)
	header_row_index, header_map = _find_source_header_row(worksheet)
	rows = []

	for row_index, values in enumerate(
		worksheet.iter_rows(min_row=header_row_index + 1, values_only=True),
		start=header_row_index + 1,
	):
		payload = {
			fieldname: values[column_index] if column_index < len(values) else None
			for fieldname, column_index in header_map.items()
		}
		if _is_empty_source_row(payload):
			continue
		payload["source_row"] = row_index
		rows.append(payload)

	return rows


def _preview_payroll_workbook(company: str, workbook_url: str) -> dict:
	raw_rows = _extract_source_workbook_rows(_get_attached_file_content(workbook_url))
	import_rows, warnings = _map_workbook_rows_to_payroll(company, raw_rows)
	unmatched_rows = [warning for warning in warnings if "could not match employee" in warning]
	matched_fallbacks = [warning for warning in warnings if "matched employee" in warning]
	unmatched_details = _collect_unmatched_workbook_rows(company, raw_rows)
	company_employee_count = frappe.db.count("Employee", {"company": company})

	return {
		"total_rows": len(raw_rows),
		"importable_rows": len(import_rows),
		"unmatched_rows": len(unmatched_rows),
		"company_employee_count": company_employee_count,
		"sample_unmatched": unmatched_rows[:10],
		"sample_matched": matched_fallbacks[:10],
		"unmatched_details": unmatched_details,
		"warnings": warnings,
		"import_rows": import_rows,
	}


def _collect_unmatched_workbook_rows(company: str, raw_rows: list[dict]) -> list[dict]:
	lookup = _get_company_employee_lookup(company)
	missing = []
	for raw in raw_rows:
		employee, _matched_by = _match_workbook_employee(raw, lookup)
		if employee:
			continue
		missing.append(raw)
	return missing


def _build_gap_report_rows(unmatched_rows: list[dict]) -> list[list]:
	rows = [[
		"source_row",
		"employee_id",
		"employee_name",
		"national_id",
		"department",
		"work_location",
		"designation",
		"gross_salary",
		"net_salary",
		"reason",
	]]

	for row in unmatched_rows:
		rows.append([
			row.get("source_row"),
			row.get("employee_id"),
			row.get("employee_name"),
			row.get("national_id"),
			row.get("department"),
			row.get("work_location"),
			row.get("designation"),
			row.get("gross_salary"),
			row.get("net_salary"),
			"No matching Employee record in selected company",
		])

	return rows


def _build_employee_setup_template_rows(company: str, unmatched_rows: list[dict]) -> list[list]:
	rows = [EMPLOYEE_SETUP_TEMPLATE_HEADERS]

	for row in unmatched_rows:
		payroll_employee_id = cstr(row.get("employee_id") or "").strip()
		first_name, middle_name, last_name = _split_payroll_employee_name(row.get("employee_name"))
		rows.append([
			row.get("source_row"),
			payroll_employee_id,
			row.get("employee_name"),
			row.get("national_id"),
			company,
			row.get("department"),
			row.get("designation"),
			payroll_employee_id,
			first_name,
			middle_name,
			last_name,
			"",
			"",
			"",
			"Active",
			"Fill the required HR fields before import",
		])

	return rows


def _extract_employee_setup_rows(content: bytes) -> list[dict]:
	workbook = load_workbook(BytesIO(content), data_only=True, read_only=True)
	worksheet = workbook["Employee Setup"] if "Employee Setup" in workbook.sheetnames else workbook[workbook.sheetnames[0]]
	rows = list(worksheet.iter_rows(values_only=True))
	if not rows:
		return []

	header_map = {
		_normalize_header_text(value): index
		for index, value in enumerate(rows[0])
		if _normalize_header_text(value)
	}
	missing_headers = [header for header in EMPLOYEE_SETUP_TEMPLATE_HEADERS if header not in header_map]
	if missing_headers:
		frappe.throw(
			_(
				"The employee setup workbook is missing required columns: {0}<br>"
				"ملف إعداد الموظفين ينقصه الأعمدة المطلوبة: {0}"
			).format(", ".join(missing_headers))
		)

	payloads = []
	for row_values in rows[1:]:
		payload = {
			header: row_values[column_index] if column_index < len(row_values) else None
			for header, column_index in header_map.items()
			if header in EMPLOYEE_SETUP_TEMPLATE_HEADERS
		}
		if _is_empty_employee_setup_row(payload):
			continue
		payloads.append(payload)

	return payloads


def _build_employee_setup_workbook_rows(rows: list[dict]) -> list[list]:
	output = [EMPLOYEE_SETUP_TEMPLATE_HEADERS]
	for row in rows:
		output.append([row.get(header) for header in EMPLOYEE_SETUP_TEMPLATE_HEADERS])
	return output


def _autofill_employee_setup_names(rows: list[dict]) -> tuple[list[dict], int]:
	updated = 0
	for row in rows:
		first_name, middle_name, last_name = _split_payroll_employee_name(row.get("payroll_employee_name"))
		row_updated = False
		if first_name and not cstr(row.get("first_name") or "").strip():
			row["first_name"] = first_name
			row_updated = True
		if middle_name and not cstr(row.get("middle_name") or "").strip():
			row["middle_name"] = middle_name
			row_updated = True
		if last_name and not cstr(row.get("last_name") or "").strip():
			row["last_name"] = last_name
			row_updated = True
		if row_updated:
			updated += 1
	return rows, updated


def _split_payroll_employee_name(value) -> tuple[str, str, str]:
	name = " ".join(cstr(value or "").replace("\n", " ").replace("\t", " ").split()).strip()
	if not name:
		return "", "", ""

	parts = [part for part in name.split(" ") if part]
	if len(parts) == 1:
		return parts[0], "", ""
	if len(parts) == 2:
		return parts[0], "", parts[1]
	return parts[0], " ".join(parts[1:-1]), parts[-1]


def _is_empty_employee_setup_row(payload: dict) -> bool:
	key_fields = [
		payload.get("employee_number") or payload.get("payroll_employee_id"),
		payload.get("payroll_employee_name"),
		payload.get("first_name"),
	]
	return all(_is_blank(value) for value in key_fields)


def _import_employee_setup_rows(company: str, rows: list[dict]) -> tuple[list[str], list[str]]:
	if not rows:
		frappe.throw(_("The employee setup workbook does not contain any rows.<br>ملف إعداد الموظفين لا يحتوي على أي صفوف."))

	prepared_rows = []
	skipped = []
	for row in rows:
		prepared = _prepare_employee_setup_row(company, row)
		if not prepared:
			skipped.append(
				_(
					"Row {0}: employee {1} already exists and was skipped."
				).format(row.get("source_row") or "?", row.get("employee_number") or row.get("payroll_employee_id") or row.get("payroll_employee_name") or "N/A")
			)
			continue
		prepared_rows.append(prepared)

	created = []
	for payload in prepared_rows:
		employee = frappe.get_doc(payload)
		employee.flags.ignore_permissions = True
		employee.insert()
		created.append(employee.name)

	return created, skipped


def _prepare_employee_setup_row(company: str, row: dict) -> dict | None:
	meta = frappe.get_meta("Employee")
	employee_number = cstr(row.get("employee_number") or row.get("payroll_employee_id") or "").strip()
	row_label = row.get("source_row") or "?"
	if not employee_number:
		frappe.throw(_("Row {0}: employee_number is required.<br>الصف {0}: الرقم الوظيفي مطلوب.").format(row_label))

	if frappe.db.exists("Employee", {"company": company, "employee_number": employee_number}):
		return None

	name_parts = _split_payroll_employee_name(row.get("payroll_employee_name"))
	first_name = cstr(row.get("first_name") or name_parts[0] or "").strip()
	middle_name = cstr(row.get("middle_name") or name_parts[1] or "").strip()
	last_name = cstr(row.get("last_name") or name_parts[2] or "").strip()
	gender = cstr(row.get("gender") or "").strip()
	status = cstr(row.get("status") or "Active").strip()
	if not first_name:
		frappe.throw(_("Row {0}: first_name is required.<br>الصف {0}: الاسم الأول مطلوب.").format(row_label))
	if not gender:
		frappe.throw(_("Row {0}: gender is required.<br>الصف {0}: الجنس مطلوب.").format(row_label))

	try:
		date_of_birth = getdate(row.get("date_of_birth"))
	except Exception:
		frappe.throw(_("Row {0}: date_of_birth is invalid.<br>الصف {0}: تاريخ الميلاد غير صالح.").format(row_label))

	try:
		date_of_joining = getdate(row.get("date_of_joining"))
	except Exception:
		frappe.throw(_("Row {0}: date_of_joining is invalid.<br>الصف {0}: تاريخ المباشرة غير صالح.").format(row_label))

	payload = {
		"doctype": "Employee",
		"company": cstr(row.get("company") or company).strip() or company,
		"employee_number": employee_number,
		"first_name": first_name,
		"gender": gender,
		"date_of_birth": date_of_birth,
		"date_of_joining": date_of_joining,
		"status": status,
	}

	if payload["company"] != company:
		frappe.throw(
			_("Row {0}: company must match the payroll company {1}.<br>الصف {0}: يجب أن تطابق الشركة شركة كشف الرواتب {1}.").format(row_label, company)
		)

	for fieldname, value in (
		("middle_name", middle_name),
		("last_name", last_name),
		("department", cstr(row.get("department") or "").strip()),
		("designation", cstr(row.get("designation") or "").strip()),
	):
		if value and meta.has_field(fieldname):
			payload[fieldname] = value

	return payload


def _normalize_basic_employee_creation_defaults(
	default_gender: str,
	default_date_of_birth,
	default_date_of_joining,
	default_status: str,
) -> dict:
	gender = cstr(default_gender or "").strip()
	if not gender:
		frappe.throw(_("Default gender is required.<br>الجنس الافتراضي مطلوب."))
	if frappe.db.exists("DocType", "Gender") and not frappe.db.exists("Gender", gender):
		frappe.throw(_("Default gender was not found.<br>الجنس الافتراضي غير موجود."))

	try:
		date_of_birth = getdate(default_date_of_birth)
	except Exception:
		frappe.throw(_("Default date of birth is invalid.<br>تاريخ الميلاد الافتراضي غير صالح."))

	try:
		date_of_joining = getdate(default_date_of_joining)
	except Exception:
		frappe.throw(_("Default date of joining is invalid.<br>تاريخ المباشرة الافتراضي غير صالح."))

	status = cstr(default_status or "Active").strip() or "Active"
	return {
		"gender": gender,
		"date_of_birth": date_of_birth,
		"date_of_joining": date_of_joining,
		"status": status,
	}


def _create_basic_employees_for_payroll(doc, defaults: dict) -> tuple[list[str], int, list[str]]:
	lookup = _get_company_employee_lookup(doc.company)
	created = []
	linked = 0
	skipped = []

	for row in doc.employees:
		if cstr(row.employee or "").strip():
			continue

		raw = {
			"employee_id": getattr(row, "payroll_employee_id", None),
			"employee_name": getattr(row, "employee_name", None),
		}
		has_payroll_employee_id = bool(cstr(getattr(row, "payroll_employee_id", "") or "").strip())
		employee, _matched_by = _match_workbook_employee(
			raw,
			lookup,
			allow_related_employee_id=not has_payroll_employee_id,
			allow_name_match=not has_payroll_employee_id,
		)
		if employee:
			_hydrate_payroll_row_from_employee(row, employee)
			linked += 1
			continue

		if not cstr(getattr(row, "payroll_employee_id", "") or "").strip() and not cstr(getattr(row, "employee_name", "") or "").strip():
			skipped.append(
				_("Row {0}: missing payroll employee id and employee name.").format(row.idx or "?")
			)
			continue

		payload = _build_basic_employee_payload_from_payroll_row(doc.company, row, defaults)
		employee_doc = frappe.get_doc(payload)
		employee_doc.flags.ignore_permissions = True
		employee_doc.insert()

		employee_data = {
			"name": employee_doc.name,
			"employee_name": employee_doc.get("employee_name") or cstr(getattr(row, "employee_name", "") or "").strip(),
			"department": employee_doc.get("department") or "",
			"nationality": employee_doc.get("nationality") or "",
			"employee_number": employee_doc.get("employee_number") or payload.get("employee_number") or "",
		}

		for source, matched_by in (
			(employee_data.get("name"), "name"),
			(employee_data.get("employee_number"), "employee_id"),
			(employee_data.get("employee_name"), "employee_name"),
		):
			_merge_employee_lookup(lookup, employee_data, source, matched_by)

		_hydrate_payroll_row_from_employee(row, employee_data)
		created.append(employee_doc.name)

	return created, linked, skipped


def _build_basic_employee_payload_from_payroll_row(company: str, row, defaults: dict) -> dict:
	meta = frappe.get_meta("Employee")
	employee_number = cstr(getattr(row, "payroll_employee_id", "") or "").strip()
	first_name, middle_name, last_name = _split_payroll_employee_name(getattr(row, "employee_name", None))
	first_name = first_name or employee_number or _("Payroll")

	payload = {
		"doctype": "Employee",
		"company": company,
		"first_name": first_name,
		"gender": defaults["gender"],
		"date_of_birth": defaults["date_of_birth"],
		"date_of_joining": defaults["date_of_joining"],
		"status": defaults["status"],
	}

	if employee_number:
		payload["employee_number"] = employee_number

	for fieldname, value in (
		("middle_name", middle_name),
		("last_name", last_name),
		("department", _resolve_department_link(getattr(row, "department", None) or getattr(row, "workbook_department", None))),
	):
		if value and meta.has_field(fieldname):
			payload[fieldname] = value

	return payload


def _hydrate_payroll_row_from_employee(row, employee: dict):
	row.employee = employee.get("name") or row.employee
	row.employee_name = employee.get("employee_name") or row.employee_name
	department = _resolve_department_link(employee.get("department") or getattr(row, "department", None) or getattr(row, "workbook_department", None))
	if department:
		row.department = department
	if employee.get("nationality"):
		row.nationality = employee.get("nationality")


def _get_source_workbook_sheet(workbook):
	for sheet_name in PREFERRED_SOURCE_WORKBOOK_SHEETS:
		if sheet_name not in workbook.sheetnames:
			continue

		worksheet = workbook[sheet_name]
		try:
			_find_source_header_row(worksheet)
			return worksheet
		except frappe.ValidationError:
			continue

	for worksheet in workbook.worksheets:
		try:
			_find_source_header_row(worksheet)
			return worksheet
		except frappe.ValidationError:
			continue

	frappe.throw(
		_("Could not locate the source payroll sheet in the workbook.<br>تعذّر العثور على شيت الرواتب المصدر داخل الملف."),
		title=_("Sheet Not Found / الشيت غير موجود"),
	)


def _find_source_header_row(worksheet):
	for row_index, values in enumerate(worksheet.iter_rows(min_row=1, max_row=20, values_only=True), start=1):
		header_map = {}
		for column_index, cell_value in enumerate(values):
			canonical = _canonical_workbook_header(cell_value)
			if canonical and canonical not in header_map:
				header_map[canonical] = column_index

		if {"employee_id", "employee_name", "basic_salary", "net_salary"}.issubset(header_map):
			return row_index, header_map

	frappe.throw(
		_("Could not find the payroll header row in the workbook.<br>تعذّر العثور على صف رؤوس الرواتب داخل الملف."),
		title=_("Header Not Found / لم يتم العثور على الرؤوس"),
	)


def _canonical_workbook_header(value) -> str | None:
	normalized = _normalize_header_text(value)
	if not normalized:
		return None

	for fieldname, aliases in WORKBOOK_HEADER_ALIASES.items():
		if normalized in {_normalize_header_text(alias) for alias in aliases}:
			return fieldname

	return None


def _normalize_header_text(value) -> str:
	return " ".join(cstr(value or "").replace("\n", " ").replace("\r", " ").split()).strip()


def _is_empty_source_row(payload: dict) -> bool:
	if _is_blank(payload.get("employee_id")) and _is_blank(payload.get("employee_name")):
		return True

	key_fields = [
		payload.get("employee_id"),
		payload.get("employee_name"),
		payload.get("gross_salary"),
		payload.get("net_salary"),
	]
	return all(_is_blank(value) for value in key_fields)


def _map_workbook_rows_to_payroll(company: str, raw_rows: list[dict]) -> tuple[list[dict], list[str]]:
	employees_by_key = _get_company_employee_lookup(company)
	import_rows = []
	warnings = []

	for raw in raw_rows:
		employee, matched_by = _match_workbook_employee(raw, employees_by_key)
		if not employee:
			warnings.append(
				_(f"Row {raw.get('source_row')}: could not match employee {raw.get('employee_id') or raw.get('employee_name')}.")
			)

		basic = _to_currency(raw.get("basic_salary"))
		housing = _to_currency(raw.get("housing_allowance"))
		transport = _to_currency(raw.get("transport_allowance"))
		other_allowances = _to_currency(raw.get("other_allowances"))
		gross = round(_to_currency(raw.get("gross_salary")) or (basic + housing + transport + other_allowances), 2)
		gosi = _to_currency(raw.get("gosi_deduction"))
		overtime = _to_currency(raw.get("additions"))
		total_deductions = _to_currency(raw.get("total_deductions"))
		if not total_deductions:
			total_deductions = round(
				gosi + _to_currency(raw.get("manual_deduction")) + _to_currency(raw.get("absence_value")) + _to_currency(raw.get("late_value")),
				2,
			)

		other_deductions = round(max(total_deductions - gosi, 0.0), 2)
		net = _to_currency(raw.get("net_salary"))
		if not net:
			net = round(gross + overtime - gosi - other_deductions, 2)

		calculated_net = round(gross + overtime - total_deductions, 2)
		if net and abs(net - calculated_net) > 0.01:
			warnings.append(
				_(
					f"Row {raw.get('source_row')}: net salary mismatch in workbook for "
					f"{(employee or {}).get('name') or raw.get('employee_id') or raw.get('employee_name')}; "
					f"imported net {net:.2f} and calculated net {calculated_net:.2f}."
				)
			)

		import_rows.append({
			"payroll_employee_id": cstr(raw.get("employee_id") or "").strip(),
			"employee": (employee or {}).get("name") or "",
			"employee_name": (employee or {}).get("employee_name") or raw.get("employee_name") or "",
			"workbook_department": cstr(raw.get("department") or "").strip(),
			"department": _resolve_department_link((employee or {}).get("department") or raw.get("department")),
			"nationality": (employee or {}).get("nationality") or "",
			"basic_salary": basic,
			"housing_allowance": housing,
			"transport_allowance": transport,
			"other_allowances": other_allowances,
			"gross_salary": gross,
			"gosi_employee_deduction": gosi,
			"sick_leave_deduction": 0.0,
			"loan_deduction": 0.0,
			"other_deductions": other_deductions,
			"total_deductions": round(gosi + other_deductions, 2),
			"overtime_addition": overtime,
			"loan_installments": "",
			"net_salary": net,
		})

		if not employee:
			warnings.append(
				_(
					f"Row {raw.get('source_row')}: imported from workbook without a linked Employee record. "
					"Use Employee Setup only if you need permanent HR records for this payroll row."
				)
			)
		elif matched_by != "employee_id":
			warnings.append(
				_(f"Row {raw.get('source_row')}: matched employee {employee['name']} by {matched_by}.")
			)

	return import_rows, warnings


def _resolve_department_link(value) -> str:
	department = cstr(value or "").strip()
	if not department:
		return ""
	return department if frappe.db.exists("Department", department) else ""


def _get_company_employee_lookup(company: str) -> dict[str, dict]:
	fields = ["name", "employee_name", "department", "employee_number"]
	meta = frappe.get_meta("Employee")
	for optional_field in ("nationality", "passport_number", "iqama_number"):
		if meta.has_field(optional_field):
			fields.append(optional_field)

	employees = frappe.get_all("Employee", filters={"company": company}, fields=fields)
	lookup = {}

	for employee in employees:
		for source, matched_by in (
			(employee.get("name"), "name"),
			(employee.get("employee_number"), "employee_id"),
			(employee.get("passport_number"), "passport_number"),
			(employee.get("iqama_number"), "iqama_number"),
			(employee.get("employee_name"), "employee_name"),
		):
			_merge_employee_lookup(lookup, employee, source, matched_by)

	contract_rows = frappe.get_all(
		"Saudi Employment Contract",
		filters={"company": company},
		fields=["employee", "iqama_number", "passport_number"],
	)
	for row in contract_rows:
		employee = next((item for item in employees if item["name"] == row.get("employee")), None)
		if not employee:
			continue
		_merge_employee_lookup(lookup, employee, row.get("iqama_number"), "contract_iqama_number")
		_merge_employee_lookup(lookup, employee, row.get("passport_number"), "contract_passport_number")

	if frappe.db.exists("DocType", "Work Permit Iqama"):
		permit_rows = frappe.get_all(
			"Work Permit Iqama",
			filters={"company": company},
			fields=["employee", "iqama_number"],
		)
		for row in permit_rows:
			employee = next((item for item in employees if item["name"] == row.get("employee")), None)
			if not employee:
				continue
			_merge_employee_lookup(lookup, employee, row.get("iqama_number"), "work_permit_iqama_number")

	return lookup


def _merge_employee_lookup(lookup: dict[str, dict], employee: dict, source, matched_by: str):
	key = _normalize_lookup_key(source)
	if not key:
		return
	existing = lookup.get(key)
	if existing and existing["employee"] and existing["employee"]["name"] != employee["name"]:
		lookup[key] = {"employee": None, "matched_by": matched_by}
		return
	lookup[key] = {"employee": employee, "matched_by": matched_by}


def _match_workbook_employee(
	raw: dict,
	lookup: dict[str, dict],
	*,
	allow_related_employee_id: bool = True,
	allow_name_match: bool = True,
):
	for candidate, matched_by, allow_related_key in (
		(raw.get("employee_id"), "employee_id", allow_related_employee_id),
		(raw.get("national_id"), "iqama_number", False),
		(raw.get("employee_name"), "employee_name", False),
	):
		if matched_by == "employee_name" and not allow_name_match:
			continue

		for key in _candidate_lookup_keys(candidate, allow_related_key=allow_related_key):
			match = lookup.get(key)
			if match and match.get("employee"):
				return match["employee"], match.get("matched_by") or matched_by

	return None, None


def _candidate_lookup_keys(value, allow_related_key: bool = True) -> list[str]:
	key = _normalize_lookup_key(value)
	if not key:
		return []

	candidates = [key]
	base_key = key.rstrip("abcdefghijklmnopqrstuvwxyz")
	if allow_related_key and base_key and base_key != key and any(char.isdigit() for char in base_key):
		candidates.append(base_key)

	return candidates


def _normalize_lookup_key(value) -> str:
	if _is_blank(value):
		return ""
	text = cstr(value).strip().replace("\n", " ")
	if text.lower() == "blank":
		return ""
	try:
		number = float(text)
		if number.is_integer():
			return str(int(number))
	except Exception:
		pass
	return " ".join(text.split()).lower()


def _to_currency(value) -> float:
	if _is_blank(value):
		return 0.0
	if isinstance(value, str) and value.strip().lower() == "blank":
		return 0.0
	return round(flt(value), 2)


def _is_blank(value) -> bool:
	return value in (None, "")


def _get_attached_file_content(file_url: str) -> bytes:
	file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not file_name:
		frappe.throw(_("Unable to find the uploaded payroll workbook.<br>تعذّر العثور على ملف الرواتب المرفوع."))
	return frappe.get_doc("File", file_name).get_content()


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


def _get_employee_fetch_fields() -> list[str]:
	fields = ["name", "employee_name", "department"]
	if frappe.get_meta("Employee").has_field("nationality"):
		fields.append("nationality")
	return fields


def _get_payable_account(company: str) -> str:
	"""الحصول على حساب الرواتب المستحقة للشركة."""
	account = frappe.db.get_value(
		"Account",
		{"company": company, "account_type": "Payable", "is_group": 0},
		"name",
	)
	return account or ""
