from statistics import mean

from frappe.model.document import Document


class PerformanceReview(Document):
	RATING_FIELDS = ("attendance_rating", "compliance_rating", "productivity_rating", "collaboration_rating")

	def validate(self):
		ratings = [float(self.get(fieldname) or 0) for fieldname in self.RATING_FIELDS if self.get(fieldname) is not None]
		if ratings:
			self.overall_rating = round(mean(ratings), 2)

		if not self.status:
			self.status = "Draft / مسودة"

		if self.overall_rating and self.status == "Draft / مسودة":
			self.status = "Completed / مكتمل"
