import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

# الحد الأقصى لوعاء الاشتراك في التأمينات
GOSI_MAX_BASE = 45000.0


class GosiContribution(Document):

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
	"""Hook — يمكن توسيعها لإنشاء قيود يومية."""
	pass


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
		sal = frappe.get_all(
			"Salary Structure Assignment",
			filters={"employee": emp.name, "docstatus": 1},
			fields=["base"],
			order_by="from_date desc",
			limit=1,
		)
		base = flt(sal[0].base) if sal else 0.0

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
