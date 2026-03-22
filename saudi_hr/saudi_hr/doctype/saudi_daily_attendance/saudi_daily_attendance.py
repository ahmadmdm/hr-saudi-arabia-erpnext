import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import time_diff_in_hours, get_datetime


class SaudiDailyAttendance(Document):

	def validate(self):
		self._calculate_working_hours()

	def _calculate_working_hours(self):
		if self.in_time and self.out_time:
			self.working_hours = round(
				time_diff_in_hours(get_datetime(self.out_time), get_datetime(self.in_time)), 2
			)
