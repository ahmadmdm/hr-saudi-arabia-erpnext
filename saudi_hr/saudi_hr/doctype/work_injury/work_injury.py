import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, getdate, today, add_days


class WorkInjury(Document):

	def validate(self):
		self._validate_reporting_deadline()
		self._warn_if_gosi_overdue()

	def _validate_reporting_deadline(self):
		"""م.150: يجب الإبلاغ عن الإصابة لـ GOSI خلال 3 أيام عمل."""
		if not self.injury_date:
			return
		days_elapsed = date_diff(today(), self.injury_date)
		if days_elapsed > 3 and not self.gosi_form_25_submitted:
			frappe.msgprint(
				_(f"⚠ Injury occurred {days_elapsed} days ago. GOSI Form 25 must be submitted within 3 working days per Article 150.<br>"
				  f"⚠ مرّ على الإصابة {days_elapsed} يوماً. يجب تقديم نموذج GOSI 25 خلال 3 أيام عمل وفقاً للمادة 150."),
				title=_("GOSI Reporting Overdue / تأخر الإبلاغ"),
				indicator="red",
			)

	def _warn_if_gosi_overdue(self):
		if self.gosi_form_25_submitted and not self.gosi_submission_date:
			self.gosi_submission_date = today()

	def on_submit(self):
		if not self.gosi_form_25_submitted:
			frappe.throw(
				_("GOSI Form 25 must be submitted before finalising the injury record.<br>"
				  "يجب تقديم نموذج GOSI 25 قبل إتمام سجل الإصابة."),
				title=_("GOSI Form Required / النموذج مطلوب"),
			)
		self.db_set("status", "Reported to GOSI / أُبلغت به GOSI")


@frappe.whitelist()
def get_gosi_deadline(injury_date: str) -> str:
	"""Return the 3-working-day GOSI reporting deadline."""
	return add_days(injury_date, 3)
