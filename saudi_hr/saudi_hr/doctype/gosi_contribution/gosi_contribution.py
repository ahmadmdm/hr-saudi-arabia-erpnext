import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from saudi_hr.saudi_hr.utils import get_employee_basic_salary as get_current_basic_salary

# الحد الأقصى لوعاء الاشتراك في التأمينات
GOSI_MAX_BASE = 45000.0


class GOSIContribution(Document):

	def validate(self):
		self._set_nationality()
		self._apply_gosi_rates()
		self._calculate_contributions()
		self._set_period_label()
		self._cap_contribution_base()

	def _set_nationality(self):
		if not self.nationality:
			self.nationality = frappe.db.get_value("Employee", self.employee, "nationality") or ""

	def _apply_gosi_rates(self):
		"""تحديد معدلات GOSI بحسب الجنسية."""
		settings = frappe.get_single("Saudi HR Settings")
		is_saudi = (self.nationality or "").lower() in ("saudi", "سعودي", "sa", "saudi arabia")

		if is_saudi:
			self.employee_contribution_rate = flt(settings.gosi_saudi_employee_rate) or 10.0
			self.employer_contribution_rate = flt(settings.gosi_saudi_employer_rate) or 12.0
		else:
			self.employee_contribution_rate = flt(settings.gosi_non_saudi_employee_rate) or 0.0
			self.employer_contribution_rate = flt(settings.gosi_non_saudi_employer_rate) or 2.0

	def _cap_contribution_base(self):
		"""وعاء الاشتراك لا يتجاوز 45,000 ريال."""
		if flt(self.contribution_base) > GOSI_MAX_BASE:
			frappe.msgprint(
				_(f"GOSI contribution base capped at {GOSI_MAX_BASE:,.0f} SAR per GOSI regulations.<br>"
				  f"تم تقييد وعاء الاشتراك بـ {GOSI_MAX_BASE:,.0f} ريال وفقاً لأنظمة GOSI."),
				title=_("Base Capped / تقييد الوعاء"),
				indicator="orange",
			)
			self.contribution_base = GOSI_MAX_BASE

	def _calculate_contributions(self):
		base = flt(self.contribution_base)
		self.employee_contribution = round(base * (flt(self.employee_contribution_rate) / 100), 2)
		self.employer_contribution = round(base * (flt(self.employer_contribution_rate) / 100), 2)
		self.total_contribution = round(self.employee_contribution + self.employer_contribution, 2)

	def _set_period_label(self):
		self.period_label = f"{self.month} {self.year}"


@frappe.whitelist()
def create_payroll_entries(doc, method=None):
	"""
	Hook مستدعى عند اعتماد GOSI Contribution.
	يُنشئ قيداً يومياً يُسجّل اشتراك GOSI في دفتر الأستاذ:
	  مدين  : حساب مصاريف التأمينات الاجتماعية
	  دائن  : حساب التأمينات الاجتماعية المستحقة
	"""
	if isinstance(doc, str):
		doc = frappe.get_doc("GOSI Contribution", doc)

	if not flt(doc.total_contribution) > 0:
		return

	# تحقق من عدم إنشاء قيد مسبق
	if doc.journal_entry and frappe.db.exists("Journal Entry", doc.journal_entry):
		return

	company = doc.company

	# ── الحصول على حسابات التأمينات ────────────────────────────────────────
	expense_account = (
		frappe.db.get_value(
			"Account",
			{"company": company, "account_name": ["like", "%Social Insurance%"],
			 "root_type": "Expense", "is_group": 0},
			"name",
		)
		or frappe.db.get_value(
			"Account",
			{"company": company, "account_name": ["like", "%Insurance%"],
			 "root_type": "Expense", "is_group": 0},
			"name",
		)
		or frappe.db.get_value(
			"Account",
			{"company": company, "account_name": ["like", "%Salary%"],
			 "root_type": "Expense", "is_group": 0},
			"name",
		)
	)

	payable_account = (
		frappe.db.get_value(
			"Account",
			{"company": company, "account_name": ["like", "%GOSI%"],
			 "root_type": "Liability", "is_group": 0},
			"name",
		)
		or frappe.db.get_value(
			"Account",
			{"company": company, "account_name": ["like", "%Social Insurance%"],
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
			_("Could not find accounts for GOSI Journal Entry. "
			  "Please configure Social Insurance accounts in the Chart of Accounts.<br>"
			  "تعذّر إيجاد حسابات لقيد GOSI. يرجى إعداد حسابات التأمينات الاجتماعية."),
			title=_("Account Not Found / حساب غير موجود"),
			indicator="orange",
		)
		return

	# ── تحديد تاريخ الترحيل (آخر يوم في الشهر) ────────────────────────────
	import calendar as _cal
	_MONTH_MAP = {
		"January": 1, "February": 2, "March": 3, "April": 4,
		"May": 5, "June": 6, "July": 7, "August": 8,
		"September": 9, "October": 10, "November": 11, "December": 12,
	}
	month_num = _MONTH_MAP.get((doc.month or "").split("/")[0].strip(), 1)
	last_day = _cal.monthrange(int(doc.year), month_num)[1]
	posting_date = f"{doc.year}-{month_num:02d}-{last_day:02d}"

	# ── إنشاء القيد اليومي ─────────────────────────────────────────────────
	je = frappe.get_doc({
		"doctype": "Journal Entry",
		"voucher_type": "Journal Entry",
		"company": company,
		"posting_date": posting_date,
		"user_remark": (
			f"GOSI Contribution — {doc.employee_name} — {doc.period_label} "
			f"(Emp: {flt(doc.employee_contribution):.2f} SAR + "
			f"Employer: {flt(doc.employer_contribution):.2f} SAR)"
		),
		"accounts": [
			{
				"account": expense_account,
				"debit_in_account_currency": flt(doc.total_contribution),
				"party_type": "Employee",
				"party": doc.employee,
				"reference_type": "GOSI Contribution",
				"reference_name": doc.name,
			},
			{
				"account": payable_account,
				"credit_in_account_currency": flt(doc.total_contribution),
				"reference_type": "GOSI Contribution",
				"reference_name": doc.name,
			},
		],
	})
	je.flags.ignore_permissions = True
	je.insert()
	je.submit()

	doc.db_set("journal_entry", je.name)
	frappe.msgprint(
		_("Journal Entry <b>{0}</b> created for GOSI contribution of {1}.<br>"
		  "تم إنشاء القيد اليومي <b>{0}</b> لاشتراك GOSI للموظف {1}.").format(
			je.name, doc.employee_name
		),
		title=_("Journal Entry Created / تم إنشاء القيد"),
		indicator="green",
	)


@frappe.whitelist()
def get_employee_basic_salary(employee):
	"""Return the employee's current basic salary for JS auto-fill."""
	return get_current_basic_salary(employee)


@frappe.whitelist()
def generate_gosi_for_month(company: str, month: str, year: int):
	"""
	إنشاء سجلات GOSI لجميع الموظفين النشطين في الشركة لشهر معين.
	يُستدعى من زر في لوحة التحكم.
	"""
	frappe.has_permission("GOSI Contribution", "create", throw=True)

	employees = frappe.get_all(
		"Employee",
		filters={"company": company, "status": "Active"},
		fields=["name", "employee_name", "nationality"],
	)

	created = 0
	for emp in employees:
		# تجنّب التكرار
		if frappe.db.exists(
			"GOSI Contribution",
			{"employee": emp.name, "month": month, "year": year, "company": company},
		):
			continue

		# الحصول على الراتب الأساسي
		base = get_current_basic_salary(emp.name)

		doc = frappe.get_doc({
			"doctype": "GOSI Contribution",
			"employee": emp.name,
			"company": company,
			"month": month,
			"year": year,
			"contribution_base": min(base, GOSI_MAX_BASE),
		})
		doc.insert(ignore_permissions=True)
		created += 1

	frappe.msgprint(
		_(f"Created {created} GOSI Contribution records for {month} {year}.<br>"
		  f"تم إنشاء {created} سجل اشتراك GOSI لـ {month} {year}."),
		title=_("GOSI Generated / تم إنشاء GOSI"),
		indicator="green",
	)

	return created
