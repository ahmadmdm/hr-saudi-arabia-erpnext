# Copyright (c) 2026, IdeaOrbit and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from saudi_hr.saudi_hr.compliance_controls import FIRST_AID_CABINET_ITEMS


class TestFirstAidCabinetRegister(FrappeTestCase):
	"""المادة (29) من اللائحة التنفيذية: خزانة الإسعافات الطبية."""

	def _make_cabinet(self, **kwargs):
		values = {
			"doctype": "First Aid Cabinet Register",
			"company": frappe.db.get_value("Company", {}, "name"),
			"cabinet_location": "Test Workshop / ورشة اختبار",
			"responsible_user": "Administrator",
			"inspection_date": today(),
		}
		values.update(kwargs)
		return frappe.get_doc(values).insert(ignore_permissions=True)

	def test_standard_contents_are_loaded_when_table_is_empty(self):
		cabinet = self._make_cabinet()
		self.assertEqual(len(cabinet.items), len(FIRST_AID_CABINET_ITEMS))
		self.assertEqual(cabinet.items[0].required_quantity, 50)

	def test_empty_cabinet_reports_full_shortage(self):
		cabinet = self._make_cabinet()
		self.assertEqual(cabinet.total_shortage_items, len(FIRST_AID_CABINET_ITEMS))
		self.assertEqual(cabinet.compliance_score, 0)
		self.assertEqual(cabinet.status, "Restock Required / يحتاج تعويض")

	def test_partial_stock_is_flagged_as_needs_restock(self):
		cabinet = self._make_cabinet()
		for row in cabinet.items:
			row.available_quantity = row.required_quantity
		cabinet.items[0].available_quantity = cabinet.items[0].required_quantity - 1
		cabinet.save(ignore_permissions=True)

		self.assertEqual(cabinet.items[0].status, "Needs Restock / يحتاج تعويض")
		self.assertEqual(cabinet.items[0].shortage_quantity, 1)
		self.assertEqual(cabinet.total_shortage_items, 1)

	def test_expired_stock_is_flagged_even_when_quantity_is_met(self):
		cabinet = self._make_cabinet()
		for row in cabinet.items:
			row.available_quantity = row.required_quantity
		cabinet.items[2].expiry_date = add_days(today(), -1)
		cabinet.save(ignore_permissions=True)

		self.assertEqual(cabinet.items[2].status, "Expired / منتهي")
		self.assertEqual(cabinet.total_shortage_items, 1)

	def test_full_stock_with_signage_and_storage_is_compliant(self):
		cabinet = self._make_cabinet()
		for row in cabinet.items:
			row.available_quantity = row.required_quantity
		cabinet.storage_conditions_met = 1
		cabinet.red_crescent_marked = 1
		cabinet.location_signage_posted = 1
		cabinet.responsible_name_posted = 1
		cabinet.save(ignore_permissions=True)

		self.assertEqual(cabinet.total_shortage_items, 0)
		self.assertEqual(cabinet.compliance_score, 100)
		self.assertEqual(cabinet.status, "Compliant / ممتثل")

	def test_full_stock_without_signage_is_not_compliant(self):
		cabinet = self._make_cabinet()
		for row in cabinet.items:
			row.available_quantity = row.required_quantity
		cabinet.storage_conditions_met = 1
		cabinet.red_crescent_marked = 1
		cabinet.save(ignore_permissions=True)

		self.assertEqual(cabinet.total_shortage_items, 0)
		self.assertEqual(cabinet.status, "Non-Compliant / غير ممتثل")
		self.assertLess(cabinet.compliance_score, 100)
