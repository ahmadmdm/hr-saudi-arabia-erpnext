import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


# Nitaqat band thresholds — approximate general industry values.
# These should be configured per sector in Saudi HR Settings.
NITAQAT_BANDS = {
	"Platinum":     (40, None),
	"High Green":   (30, 40),
	"Medium Green": (20, 30),
	"Low Green":    (10, 20),
	"Yellow":       (4, 10),
	"Red":          (0, 4),
}


class NitaqatRecord(Document):

	def validate(self):
		self._count_employees()
		self._calculate_saudization()
		self._classify_nitaqat()

	def _count_employees(self):
		"""حساب عدد الموظفين السعوديين وغير السعوديين من جدول الموظفين."""
		saudi_keywords = ("saudi", "سعودي", "sa", "saudi arabia")

		all_employees = frappe.get_all(
			"Employee",
			filters={"company": self.company, "status": "Active"},
			fields=["name", "nationality"],
		)

		saudi = sum(
			1 for e in all_employees
			if (e.nationality or "").lower().strip() in saudi_keywords
		)

		self.total_employees = len(all_employees)
		self.saudi_employees = saudi
		self.non_saudi_employees = self.total_employees - saudi

	def _calculate_saudization(self):
		if self.total_employees > 0:
			self.saudization_percentage = round(
				(self.saudi_employees / self.total_employees) * 100, 2
			)
		else:
			self.saudization_percentage = 0.0

	def _classify_nitaqat(self):
		"""تصنيف النطاق بحسب نسبة السعودة."""
		pct = flt(self.saudization_percentage)
		required = flt(self.required_saudization_percentage) or 0.0

		category = "Red / أحمر"
		color = "Red"

		if pct >= 40:
			category, color = "Platinum / بلاتيني", "Platinum"
		elif pct >= 30:
			category, color = "High Green / أخضر مرتفع", "Green"
		elif pct >= 20:
			category, color = "Medium Green / أخضر متوسط", "Green"
		elif pct >= 10:
			category, color = "Low Green / أخضر منخفض", "Green"
		elif pct >= 4:
			category, color = "Yellow / أصفر", "Yellow"
		else:
			category, color = "Red / أحمر", "Red"

		self.nitaqat_category = category
		self.nitaqat_color = color

		# حالة الامتثال
		if required and pct < required:
			self.compliance_status = "Non-Compliant / غير ممتثل"
		elif required and pct < required * 1.1:
			self.compliance_status = "At Risk / في خطر"
		else:
			self.compliance_status = "Compliant / ممتثل"

		# الفجوة للنطاق التالي
		next_band_threshold = self._next_band_threshold(pct)
		self.gap_to_next_band = round(max(0, next_band_threshold - pct), 2) if next_band_threshold else 0.0

	def _next_band_threshold(self, pct):
		thresholds = sorted([40, 30, 20, 10, 4])
		for t in thresholds:
			if pct < t:
				return t
		return None
