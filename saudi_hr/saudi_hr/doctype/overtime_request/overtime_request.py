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
		"""عند الاعتماد: إنشاء Additional Salary في hrms."""
		if self.approval_status != "Approved / موافق":
			frappe.throw(
				_("Cannot submit unless Approval Status is 'Approved'.<br>"
				  "لا يمكن الاعتماد إلا إذا كانت حالة الموافقة 'موافق'."),
				title=_("Not Approved / لم يُوافق بعد"),
			)
		self._create_additional_salary()

	def _create_additional_salary(self):
		"""إنشاء Additional Salary مرتبطة بقسيمة الرواتب."""
		# التحقق من عدم إنشاء راتب إضافي مسبقاً
		if self.additional_salary:
			return

		# البحث عن مكوّن الراتب للعمل الإضافي
		component = self._get_overtime_salary_component()

		addl = frappe.get_doc({
			"doctype": "Additional Salary",
			"employee": self.employee,
			"salary_component": component,
			"amount": self.overtime_amount,
			"payroll_date": self.date,
			"company": self.company,
			"overwrite_salary_structure_amount": 0,
			"deduct_full_tax_on_selected_payroll_date": 0,
		})
		addl.insert(ignore_permissions=True)
		addl.submit()

		self.db_set("additional_salary", addl.name)

	def _get_overtime_salary_component(self) -> str:
		"""الحصول على مكوّن "Overtime" من Salary Component أو إنشاؤه."""
		component_name = "Overtime / عمل إضافي"
		if not frappe.db.exists("Salary Component", component_name):
			sc = frappe.get_doc({
				"doctype": "Salary Component",
				"salary_component": component_name,
				"salary_component_abbr": "OT",
				"type": "Earning",
				"description": "Overtime pay per Saudi Labor Law Art. 107 (150%)",
			})
			sc.insert(ignore_permissions=True)
		return component_name


@frappe.whitelist()
def create_additional_salary(doc, method=None):
	"""Hook called from hooks.py on_submit."""
	pass  # handled inside on_submit


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
