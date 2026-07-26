from statistics import mean

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate


class PerformanceReview(Document):
	RATING_FIELDS = ("attendance_rating", "compliance_rating", "productivity_rating", "collaboration_rating")

	def validate(self):
		if self.review_period_start and self.review_period_end:
			if getdate(self.review_period_end) < getdate(self.review_period_start):
				frappe.throw("Review period end date cannot be before its start date.")

		ratings = []
		for fieldname in self.RATING_FIELDS:
			raw_rating = self.get(fieldname)
			if raw_rating in (None, "", 0, 0.0):
				continue
			rating = flt(raw_rating)
			if not 1 <= rating <= 5:
				frappe.throw(f"{self.meta.get_label(fieldname)} must be between 1 and 5.")
			ratings.append(rating)
		if ratings:
			self.overall_rating = round(mean(ratings), 2)
		else:
			self.overall_rating = 0

		if self.salary_adjustment and not self.salary_adjustment_recommended:
			self.salary_adjustment_recommended = int(
				frappe.db.exists("Salary Adjustment", self.salary_adjustment)
			)

		if self.promotion_transfer and not self.promotion_recommended:
			self.promotion_recommended = int(
				frappe.db.exists("Promotion Transfer", self.promotion_transfer)
			)

		if not self.status:
			self.status = "Draft / مسودة"

		if self.overall_rating and self.status == "Draft / مسودة":
			self.status = "Completed / مكتمل"
