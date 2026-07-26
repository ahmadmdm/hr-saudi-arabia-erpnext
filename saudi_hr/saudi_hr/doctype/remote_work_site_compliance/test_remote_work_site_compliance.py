# Copyright (c) 2026, IdeaOrbit and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from saudi_hr.saudi_hr.compliance_controls import (
	REMOTE_SITE_OBLIGATION_FIELDS,
	classify_remote_area,
)


class TestRemoteWorkSiteCompliance(FrappeTestCase):
	"""المادة (30) من اللائحة التنفيذية والمادة (146) من النظام: الأماكن البعيدة عن العمران."""

	def _make_site(self, **kwargs):
		values = {
			"doctype": "Remote Work Site Compliance",
			"company": frappe.db.get_value("Company", {}, "name"),
			"site_name": "Test Site / موقع اختبار",
			"assessment_date": today(),
		}
		values.update(kwargs)
		return frappe.get_doc(values).insert(ignore_permissions=True)

	def test_paved_road_threshold_is_fifty_kilometres(self):
		self.assertTrue(classify_remote_area("Paved / معبد", 50.5, 0))
		self.assertFalse(classify_remote_area("Paved / معبد", 50, 0))

	def test_unpaved_road_threshold_is_twenty_five_kilometres(self):
		self.assertTrue(classify_remote_area("Unpaved / غير معبد", 25.5, 0))
		self.assertFalse(classify_remote_area("Unpaved / غير معبد", 25, 0))

	def test_settlement_without_facilities_is_remote_regardless_of_distance(self):
		self.assertTrue(classify_remote_area("Paved / معبد", 1, 1))

	def test_unknown_road_type_is_not_classified_remote(self):
		self.assertFalse(classify_remote_area(None, 999, 0))

	def test_non_remote_site_is_marked_not_applicable(self):
		site = self._make_site(road_type="Paved / معبد", distance_km=10)
		self.assertEqual(site.is_remote_area, 0)
		self.assertEqual(site.status, "Not Applicable / غير منطبق")

	def test_remote_site_without_obligations_is_non_compliant(self):
		site = self._make_site(road_type="Unpaved / غير معبد", distance_km=40)
		self.assertEqual(site.is_remote_area, 1)
		self.assertEqual(site.obligations_met, 0)
		self.assertEqual(site.status, "Non-Compliant / غير ممتثل")

	def test_remote_site_with_some_obligations_is_partially_compliant(self):
		site = self._make_site(
			road_type="Unpaved / غير معبد",
			distance_km=40,
			shops_provided=1,
			mosques_provided=1,
		)
		self.assertEqual(site.obligations_met, 2)
		self.assertEqual(site.compliance_score, 33.33)
		self.assertEqual(site.status, "Partially Compliant / ممتثل جزئياً")

	def test_remote_site_meeting_all_six_obligations_is_compliant(self):
		site = self._make_site(
			road_type="Paved / معبد",
			distance_km=80,
			**{fieldname: 1 for fieldname in REMOTE_SITE_OBLIGATION_FIELDS},
		)
		self.assertEqual(len(REMOTE_SITE_OBLIGATION_FIELDS), 6)
		self.assertEqual(site.obligations_met, 6)
		self.assertEqual(site.compliance_score, 100)
		self.assertEqual(site.status, "Compliant / ممتثل")
