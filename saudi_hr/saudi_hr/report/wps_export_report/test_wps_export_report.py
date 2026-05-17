from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr.report.wps_export_report.wps_export_report import execute


class TestWpsExportReport(FrappeTestCase):
	def test_report_opens_without_required_filter(self):
		columns, data = execute({})

		self.assertTrue(columns)
		self.assertEqual(data, [])
