import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days


# النصوص الخاصة بكل مادة قانونية
ARTICLE_MAP = {
	"Resignation by Employee / استقالة الموظف (م.75)": (
		"م.75 — استقالة الموظف",
		"يجب أن يُخطر الموظف صاحبَ العمل قبل ترك العمل وفقاً لنوع الأجر: "
		"60 يوماً للشهري، 30 يوماً لغيره.\n"
		"Art. 75 — The employee must notify the employer before leaving based on pay type: "
		"60 days for monthly, 30 days for others.",
	),
	"Termination by Employer / إنهاء من صاحب العمل (م.76)": (
		"م.76 — إنهاء من صاحب العمل",
		"يجب أن يُخطر صاحبُ العمل الموظفَ قبل إنهاء الخدمة: "
		"60 يوماً للشهري، 30 يوماً لغيره.\n"
		"Art. 76 — The employer must notify the employee before termination: "
		"60 days for monthly, 30 days for others.",
	),
	"End of Fixed Term / انتهاء عقد محدد المدة": (
		"م.84 — مكافأة نهاية الخدمة",
		"انتهاء العقد المحدد المدة — مكافأة كاملة مستحقة وفق م.84.",
	),
	"Mutual Agreement / اتفاق مشترك": (
		"م.75 / م.76 — اتفاق مشترك",
		"إنهاء الخدمة بالتراضي — تُحدد حقوق الطرفين بالاتفاق.",
	),
	"Dismissal Without Notice / فصل فوري (م.80)": (
		"م.80 — فسخ العقد بدون إشعار",
		"يحق لصاحب العمل فسخ العقد دون إشعار ودون مكافأة في الحالات الواردة في م.80.\n"
		"Art. 80 — Employer may terminate without notice or EOSB in cases listed under Art. 80.",
	),
}


class TerminationNotice(Document):

	def validate(self):
		self._calculate_notice_period()
		self._set_legal_reference()

	def _calculate_notice_period(self):
		"""
		م.75/م.76: 60 يوماً للأجر الشهري، 30 يوماً لغيره.
		خلال فترة التجربة أو (م.80): 0 أيام.
		"""
		reason = self.termination_reason or ""
		settings = frappe.get_single("Saudi HR Settings")

		# فسخ فوري: لا إشعار
		if "م.80" in reason or "Dismissal" in reason or self.during_probation:
			self.notice_required_days = 0
		elif self.salary_payment_type == "Monthly / شهري":
			self.notice_required_days = int(settings.notice_period_monthly_days or 60)
		else:
			self.notice_required_days = int(settings.notice_period_non_monthly_days or 30)

		# تاريخ نهاية فترة الإشعار
		if self.notice_start_date and self.notice_required_days is not None:
			self.notice_end_date = add_days(self.notice_start_date, self.notice_required_days)

	def _set_legal_reference(self):
		"""تحديد المادة القانونية ووصفها وأحقية المكافأة."""
		reason = self.termination_reason or ""
		article, description = ARTICLE_MAP.get(reason, ("—", ""))

		self.termination_article = article
		self.article_description = description

		# تحديد أحقية المكافأة
		no_eosb_reasons = {
			"Dismissal Without Notice / فصل فوري (م.80)",
		}
		self.eosb_applicable = 0 if reason in no_eosb_reasons else 1

	def on_submit(self):
		"""عند الاعتماد: تحديث حالة الموظف."""
		if self.eosb_applicable:
			frappe.msgprint(
				_("Don't forget to create an End of Service Benefit document for this employee.<br>"
				  "لا تنسَ إنشاء وثيقة مكافأة نهاية الخدمة لهذا الموظف."),
				title=_("EOSB Required / المكافأة مستحقة"),
				indicator="blue",
			)
