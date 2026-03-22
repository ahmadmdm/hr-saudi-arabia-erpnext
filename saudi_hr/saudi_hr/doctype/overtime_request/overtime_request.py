import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class OvertimeRequest(Document):

	OVERTIME_RATE = 1.5  # م.107: 150%
	WORKING_HOURS_PER_MONTH = 240  # 8 h/day × 30 days

	def validate(self):
		self._validate_overtime_hours()
		self._fetch_salary()
		self._calculate_overtime()

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

	def _fetch_salary(self):
		"""جلب الراتب الأساسي من آخر هيكل راتب للموظف."""
		sal_assign = frappe.get_all(
			"Salary Structure Assignment",
			filters={"employee": self.employee, "docstatus": 1},
			fields=["base"],
			order_by="from_date desc",
			limit=1,
		)
		self.monthly_basic = flt(sal_assign[0].base) if sal_assign else 0.0
		self.overtime_rate = self.OVERTIME_RATE
		# الأجر الساعي = الراتب الشهري / 240
		self.hourly_rate = round(self.monthly_basic / self.WORKING_HOURS_PER_MONTH, 4)

	def _calculate_overtime(self):
		"""حساب مبلغ العمل الإضافي = ساعات × الأجر الساعي × 1.5"""
		self.overtime_amount = round(
			flt(self.overtime_hours) * flt(self.hourly_rate) * self.OVERTIME_RATE, 2
		)

	def on_submit(self):
		"""عند الاعتماد: إنشاء قيد يومي بدلاً من Additional Salary."""
		if self.approval_status != "Approved / موافق":
			frappe.throw(
				_("Cannot submit unless Approval Status is 'Approved'.<br>"
				  "لا يمكن الاعتماد إلا إذا كانت حالة الموافقة 'موافق'."),
				title=_("Not Approved / لم يُوافق بعد"),
			)
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
				f"{self.overtime_hours}h × {self.overtime_rate} = {flt(self.overtime_amount):.2f} SAR"
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
		je.flags.ignore_permissions = True
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
	sal = frappe.get_all(
		"Salary Structure Assignment",
		filters={"employee": employee, "docstatus": 1},
		fields=["base"],
		order_by="from_date desc",
		limit=1,
	)
	return flt(sal[0].base) if sal else 0.0
