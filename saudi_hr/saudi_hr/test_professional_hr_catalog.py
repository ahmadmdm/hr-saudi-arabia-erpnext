from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr.professional_hr_catalog import get_professional_hr_catalog, get_professional_hr_feature


class TestProfessionalHrCatalog(FrappeTestCase):
	def test_catalog_contains_full_feature_navigation(self):
		catalog = get_professional_hr_catalog()

		self.assertGreaterEqual(catalog["total_features"], 70)
		self.assertTrue(catalog["version"])
		self.assertGreaterEqual(len(catalog["categories"]), 10)
		self.assertTrue(all(feature.get("detail_route") for feature in catalog["features"]))
		self.assertTrue(all(feature.get("route") for feature in catalog["features"]))
		self.assertTrue(all("?feature=" not in feature.get("detail_route", "") for feature in catalog["features"]))

	def test_doctype_features_have_professional_entry_routes(self):
		catalog = get_professional_hr_catalog()
		doctype_features = [
			feature
			for feature in catalog["features"]
			if feature["target_type"] == "DocType" and feature.get("allow_entry") is not False
		]
		component_features = [feature for feature in catalog["features"] if feature.get("allow_entry") is False]
		report_features = [feature for feature in catalog["features"] if feature["target_type"] == "Report"]

		self.assertTrue(doctype_features)
		self.assertTrue(all(feature.get("entry_route") for feature in doctype_features))
		self.assertTrue(component_features)
		self.assertTrue(all(not feature.get("entry_route") for feature in component_features))
		self.assertTrue(all(feature.get("action_label") for feature in component_features))
		self.assertTrue(all(not feature.get("entry_route") for feature in report_features))
		settings = next(feature for feature in catalog["features"] if feature["id"] == "saudi-hr-settings")
		self.assertFalse(settings.get("entry_route"))
		self.assertEqual(settings.get("action_label"), "Open Settings")

	def test_component_features_route_to_parent_surfaces(self):
		catalog = get_professional_hr_catalog()
		features = {feature["id"]: feature for feature in catalog["features"]}

		self.assertEqual(features["labor-inspection-violation"]["route"], "/app/labor-inspection")
		self.assertEqual(features["employee-loan-installment"]["route"], "/app/employee-loan")
		self.assertEqual(features["saudi-monthly-payroll-employee"]["route"], "/app/saudi-monthly-payroll")
		self.assertEqual(features["branch-employee-directory-row"]["route"], "/app/employee-org-tree")

	def test_feature_detail_returns_related_features(self):
		result = get_professional_hr_feature("saudi-monthly-payroll")

		self.assertEqual(result["feature"]["title"], "Saudi Monthly Payroll")
		self.assertEqual(result["category"]["id"], "time")
		self.assertTrue(result["related"])
		self.assertGreaterEqual(result["catalog_summary"]["total_features"], 70)