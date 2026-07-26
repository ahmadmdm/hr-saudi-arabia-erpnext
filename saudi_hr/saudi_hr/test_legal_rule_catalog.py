import unittest
from unittest.mock import MagicMock, patch

from saudi_hr.saudi_hr.legal_rule_catalog import (
	CATALOG_VERSION,
	LEGAL_RULES,
	sync_legal_rule_catalog,
	validate_catalog,
)


class TestLegalRuleCatalog(unittest.TestCase):
	def test_catalog_is_versioned_and_unique(self):
		self.assertTrue(CATALOG_VERSION)
		self.assertTrue(validate_catalog())
		self.assertEqual(len(LEGAL_RULES), len({rule["rule_id"] for rule in LEGAL_RULES}))

	def test_critical_rules_have_automated_verification(self):
		critical = [rule for rule in LEGAL_RULES if rule["risk_level"] == "Critical / حرج"]
		self.assertTrue(critical)
		for rule in critical:
			self.assertTrue(rule["verification_reference"].startswith("test:"), rule["rule_id"])

	@patch("saudi_hr.saudi_hr.legal_rule_catalog.frappe.get_doc")
	@patch("saudi_hr.saudi_hr.legal_rule_catalog.frappe.db.exists")
	@patch("saudi_hr.saudi_hr.legal_rule_catalog.frappe.get_all", return_value=["Company A", "Company B"])
	def test_catalog_sync_covers_every_company(self, _companies, exists, get_doc):
		exists.side_effect = lambda doctype, filters=None: True if doctype == "DocType" else False
		get_doc.return_value.insert = MagicMock()

		result = sync_legal_rule_catalog()

		self.assertEqual(result["companies"], ["Company A", "Company B"])
		self.assertEqual(result["created"], len(LEGAL_RULES) * 2)
		self.assertEqual(result["updated"], 0)
		self.assertEqual(get_doc.call_count, len(LEGAL_RULES) * 2)
