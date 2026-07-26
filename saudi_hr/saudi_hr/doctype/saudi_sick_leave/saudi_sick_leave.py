import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_years, date_diff, flt, getdate, nowdate

from saudi_hr.saudi_hr.utils import get_employee_basic_salary


def _row_value(row, fieldname):
	return row.get(fieldname) if isinstance(row, dict) else getattr(row, fieldname, None)


def calculate_sick_leave_cycle(request_date, prior_leaves=None):
	"""Return the active one-year benefit cycle beginning with its first sick leave."""
	request_day = getdate(request_date)
	cycle_start = cycle_end = None
	used_days = 0

	rows = sorted(
		prior_leaves or [],
		key=lambda row: getdate(_row_value(row, "from_date")),
	)
	for row in rows:
		row_start = getdate(_row_value(row, "from_date"))
		if row_start > request_day:
			continue
		if cycle_start is None or row_start > cycle_end:
			cycle_start = row_start
			cycle_end = add_days(add_years(cycle_start, 1), -1)
			used_days = 0

		row_end = getdate(_row_value(row, "to_date") or row_start)
		overlap_start = max(row_start, cycle_start)
		overlap_end = min(row_end, cycle_end)
		if overlap_end >= overlap_start:
			used_days += date_diff(overlap_end, overlap_start) + 1

	if cycle_start is None or request_day > cycle_end:
		cycle_start = request_day
		cycle_end = add_days(add_years(cycle_start, 1), -1)
		used_days = 0

	return {
		"cycle_start": cycle_start,
		"cycle_end": cycle_end,
		"used_days": flt(used_days),
	}


def calculate_sick_leave_pay_breakdown(
	used_before,
	new_days,
	daily_salary,
	full_pay_days=30,
	partial_pay_days=60,
	partial_pay_percentage=75,
):
	"""Allocate a request across the full, partial, and unpaid statutory tiers."""
	used = max(0, flt(used_before))
	requested = max(0, flt(new_days))
	daily = max(0, flt(daily_salary))
	full_limit = max(0, flt(full_pay_days))
	partial_limit = max(0, flt(partial_pay_days))
	partial_rate = max(0, flt(partial_pay_percentage)) / 100

	full_quota = min(requested, max(0, full_limit - used))
	remaining = requested - full_quota
	partial_consumed = max(0, min(partial_limit, used - full_limit))
	partial_quota = min(remaining, max(0, partial_limit - partial_consumed))
	unpaid_quota = max(0, remaining - partial_quota)
	amount = daily * (full_quota + partial_quota * partial_rate)
	effective_rate = (amount / (requested * daily) * 100) if requested and daily else 0

	if full_quota == requested:
		label = "Full Pay / أجر كامل (100%)"
	elif partial_quota == requested:
		label = f"Partial Pay / أجر جزئي ({partial_rate * 100:.0f}%)"
	elif unpaid_quota == requested:
		label = "No Pay / بدون أجر"
	else:
		label = "Mixed Statutory Tiers / شرائح نظامية مختلطة"

	return {
		"full_pay_days": flt(full_quota),
		"partial_pay_days": flt(partial_quota),
		"unpaid_days": flt(unpaid_quota),
		"amount": round(amount, 2),
		"effective_rate": round(effective_rate, 2),
		"label": label,
	}


class SaudiSickLeave(Document):

	def validate(self):
		self._calculate_total_days()
		self._validate_no_overlap()
		self._calculate_cumulative_days()
		self._validate_max_sick_days()
		self._calculate_pay()
		self._set_alerts()

	def _calculate_total_days(self):
		if self.from_date and self.to_date:
			self.total_days = date_diff(self.to_date, self.from_date) + 1
			if self.total_days <= 0:
				frappe.throw(_("To Date must be after From Date / يجب أن يكون تاريخ الانتهاء بعد تاريخ البدء"))

	def _validate_no_overlap(self):
		if not (self.employee and self.from_date and self.to_date):
			return
		filters = {
			"employee": self.employee,
			"docstatus": ["<", 2],
			"from_date": ["<=", self.to_date],
			"to_date": [">=", self.from_date],
		}
		if self.name:
			filters["name"] = ["!=", self.name]
		overlap = frappe.db.exists("Saudi Sick Leave", filters)
		if overlap:
			frappe.throw(
				_("This period overlaps sick-leave request {0}. Adjust the dates before continuing.<br>"
				  "تتداخل هذه المدة مع طلب الإجازة المرضية {0}. عدّل التواريخ قبل المتابعة.").format(overlap),
				title=_("Overlapping Sick Leave / تداخل إجازة مرضية"),
			)

	def _get_sick_leave_cycle(self, exclude_current=True):
		"""الدورة النظامية سنة تبدأ من تاريخ أول إجازة مرضية، وليست سنة تقويمية."""
		filters = {
			"employee": self.employee,
			"docstatus": 1,
			"from_date": ["<=", self.from_date],
		}
		if exclude_current and self.name:
			filters["name"] = ["!=", self.name]

		rows = frappe.get_all(
			"Saudi Sick Leave",
			filters=filters,
			fields=["name", "from_date", "to_date", "total_days"],
			order_by="from_date asc, creation asc",
		)
		return calculate_sick_leave_cycle(self.from_date, rows)

	def _calculate_cumulative_days(self):
		cycle = self._get_sick_leave_cycle()
		self.benefit_cycle_start = cycle["cycle_start"]
		self.benefit_cycle_end = cycle["cycle_end"]
		self.sick_days_this_year_before = cycle["used_days"]
		self.sick_days_this_year_after = self.sick_days_this_year_before + (self.total_days or 0)
		self.cycle_boundary_review_required = int(
			bool(self.to_date and getdate(self.to_date) > getdate(self.benefit_cycle_end))
		)
		self.cycle_boundary_note = (
			"The request crosses the current benefit-year boundary; review allocation across cycles. / "
			"تتجاوز الإجازة نهاية دورة الاستحقاق الحالية؛ راجع توزيع الأيام بين الدورتين."
			if self.cycle_boundary_review_required
			else ""
		)

	def _validate_max_sick_days(self):
		"""الحد الأقصى للإجازة المرضية 120 يوماً في السنة (م.117)."""
		if self.sick_days_this_year_after > 120:
			frappe.throw(
				_("Total sick days in the year cannot exceed 120 per Saudi Labor Law Art. 117.<br>"
				  "لا يجوز أن يتجاوز مجموع أيام الإجازة المرضية في السنة 120 يوماً وفقاً للمادة 117."),
				title=_("Sick Leave Limit Exceeded / تجاوز حد الإجازة المرضية"),
			)

	def _calculate_pay(self):
		"""حساب أجر الإجازة المرضية بحسب الشرائح."""
		settings = frappe.get_single("Saudi HR Settings")
		full_days = int(settings.sick_leave_full_pay_days or 30)
		partial_days = int(settings.sick_leave_partial_pay_days or 60)
		partial_pct = flt(settings.sick_leave_partial_pay_percentage or 75)

		# حساب الأجر اليومي
		monthly = get_employee_basic_salary(self.employee)
		self.daily_salary = round(monthly / 30, 2)

		breakdown = calculate_sick_leave_pay_breakdown(
			self.sick_days_this_year_before,
			self.total_days,
			self.daily_salary,
			full_days,
			partial_days,
			partial_pct,
		)
		self.full_pay_days = breakdown["full_pay_days"]
		self.partial_pay_days = breakdown["partial_pay_days"]
		self.unpaid_days = breakdown["unpaid_days"]
		self.leave_pay_amount = breakdown["amount"]
		self.pay_rate = breakdown["effective_rate"]
		self.pay_label = breakdown["label"]

	def _set_alerts(self):
		after = self.sick_days_this_year_after or 0
		settings = frappe.get_single("Saudi HR Settings")
		full_days = int(settings.sick_leave_full_pay_days or 30)
		partial_days = int(settings.sick_leave_partial_pay_days or 60)

		self.alert_30_days = 1 if after > full_days else 0
		self.alert_90_days = 1 if after > full_days + partial_days else 0

		if self.alert_90_days:
			frappe.msgprint(
				_("The employee has entered the unpaid tier after 90 cumulative days. Continue tracking the 120-day benefit; do not initiate termination automatically.<br>"
				  "دخل الموظف شريحة الإجازة دون أجر بعد 90 يوماً تراكمياً. استمر في متابعة استحقاق 120 يوماً ولا تبدأ الإنهاء تلقائياً."),
				title=_("Unpaid Sick-Leave Tier / شريحة الإجازة المرضية دون أجر"),
				indicator="orange",
			)


@frappe.whitelist()
def get_sick_leave_cycle(employee, from_date=None, exclude_doc=""):
	"""Return the active statutory cycle and used days for a client-side preview."""
	request_date = from_date or nowdate()
	filters = {
		"employee": employee,
		"docstatus": 1,
		"from_date": ["<=", request_date],
	}
	if exclude_doc:
		filters["name"] = ["!=", exclude_doc]

	rows = frappe.get_all(
		"Saudi Sick Leave",
		filters=filters,
		fields=["name", "from_date", "to_date", "total_days"],
		order_by="from_date asc, creation asc",
	)
	return calculate_sick_leave_cycle(request_date, rows)


@frappe.whitelist()
def get_sick_days_this_year(employee, exclude_doc=""):
	"""Backward-compatible alias returning used days in the active statutory cycle."""
	return get_sick_leave_cycle(employee, nowdate(), exclude_doc)["used_days"]


@frappe.whitelist()
def get_daily_salary(employee):
	"""Return daily salary (monthly_basic / 30) for the employee."""
	monthly = get_employee_basic_salary(employee)
	return round(monthly / 30, 2)
