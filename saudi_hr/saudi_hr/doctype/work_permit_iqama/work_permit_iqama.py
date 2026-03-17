import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, getdate, today


class WorkPermitIqama(Document):

	def validate(self):
		self._calculate_iqama_status()
		self._calculate_permit_status()

	def _calculate_iqama_status(self):
		if not self.iqama_expiry_date:
			return
		days = date_diff(self.iqama_expiry_date, today())
		self.days_to_iqama_expiry = days
		settings = frappe.get_single("Saudi HR Settings")
		alert_days = int(settings.iqama_expiry_alert_days or 90)

		if days < 0:
			self.iqama_status = "Expired / منتهية"
		elif days <= alert_days:
			self.iqama_status = "Expiring Soon / تنتهي قريباً"
		else:
			self.iqama_status = "Active / نشطة"

	def _calculate_permit_status(self):
		if not self.work_permit_expiry_date:
			self.work_permit_status = "N/A"
			return
		days = date_diff(self.work_permit_expiry_date, today())
		self.days_to_permit_expiry = days

		if days < 0:
			self.work_permit_status = "Expired / منتهي"
		elif days <= 90:
			self.work_permit_status = "Expiring Soon / ينتهي قريباً"
		else:
			self.work_permit_status = "Active / نشط"
