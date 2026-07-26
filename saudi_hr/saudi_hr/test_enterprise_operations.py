import unittest
from unittest.mock import MagicMock, patch

from saudi_hr.saudi_hr.doctype.saudi_government_integration.saudi_government_integration import safe_profile_dict
from saudi_hr.saudi_hr.enterprise_operations import (
	PROVIDER_META,
	_fingerprint,
	_safe_sample,
	normalize_arabic,
	preview_provider_export,
	search_hr_guidance,
)


class TestEnterpriseOperations(unittest.TestCase):
	def test_arabic_normalization_handles_hamza_diacritics_and_ta_marbuta(self):
		self.assertEqual(normalize_arabic("إِجَازَة مَرَضِيَّة"), "اجازه مرضيه")

	def test_payload_fingerprint_is_deterministic_across_key_order(self):
		first = _fingerprint({"provider": "QIWA", "records": [{"b": 2, "a": 1}]})
		second = _fingerprint({"records": [{"a": 1, "b": 2}], "provider": "QIWA"})
		self.assertEqual(first, second)
		self.assertEqual(len(first), 64)

	def test_masked_preview_hides_sensitive_identifiers(self):
		rows = _safe_sample(
			"Mudad / مدد",
			[{"employee_reference": "HR-EMP-0001", "iban": "SA1234567890123456789012", "net_salary_sar": 9000}],
		)
		self.assertNotIn("HR-EMP-0001", str(rows))
		self.assertNotIn("SA1234567890123456789012", str(rows))
		self.assertTrue(rows[0]["iban"].endswith("9012"))

	def test_all_four_provider_adapters_are_registered(self):
		self.assertEqual(set(PROVIDER_META), {"Qiwa / قوى", "GOSI / التأمينات", "Mudad / مدد", "Muqeem / مقيم"})
		self.assertTrue(all(meta["format"] in {"csv", "json"} for meta in PROVIDER_META.values()))

	def test_safe_profile_never_returns_credential_values(self):
		profile = MagicMock()
		profile.name = "SAU-GOV-QIWA-DEMO"
		profile.provider = "Qiwa / قوى"
		profile.company = "Demo"
		profile.enabled = 1
		profile.mode = "Live API / واجهة فعلية"
		profile.configuration_status = "Live / فعلي"
		profile.api_version = "2026.1"
		profile.owner_user = "Administrator"
		profile.last_tested_on = None
		profile.last_successful_sync_on = None
		profile.last_error_summary = None
		profile.base_url = "https://approved.example"
		profile.client_id = "sensitive-client"
		profile.client_secret = "sensitive-secret"
		profile.credential_reference = None
		profile.certificate_file = None
		result = safe_profile_dict(profile)
		self.assertNotIn("client_id", result)
		self.assertNotIn("client_secret", result)
		self.assertNotIn("base_url", result)
		self.assertTrue(result["has_credentials"])

	@patch("saudi_hr.saudi_hr.enterprise_operations._require_enterprise_access")
	@patch("saudi_hr.saudi_hr.enterprise_operations._build_payload")
	@patch("saudi_hr.saudi_hr.enterprise_operations._profile")
	def test_preview_is_masked_and_side_effect_free(self, profile_loader, build_payload, _access):
		profile = MagicMock()
		profile.name = "SAU-GOV-MUDAD-DEMO"
		profile.provider = "Mudad / مدد"
		profile.company = "Demo"
		profile.enabled = 1
		profile.mode = "File Exchange / تبادل ملفات"
		profile.configuration_status = "Ready for File Exchange / جاهز لتبادل الملفات"
		profile.api_version = "2026.1"
		profile.owner_user = "Administrator"
		profile.last_tested_on = None
		profile.last_successful_sync_on = None
		profile.last_error_summary = None
		profile.base_url = None
		profile.client_id = None
		profile.client_secret = None
		profile.credential_reference = None
		profile.certificate_file = None
		profile_loader.return_value = profile
		build_payload.return_value = (
			{"schema_version": "SaudiHR-MUDAD-2026.1", "record_count": 1, "records": [{"employee_reference": "EMP-1", "iban": "SA12345678"}]},
			[],
			[],
		)
		result = preview_provider_export(profile.name)
		self.assertTrue(result["can_confirm"])
		self.assertNotIn("SA12345678", str(result["sample"]))
		self.assertIn("لم تُرسل", result["notice_ar"])

	def test_legal_search_returns_page_citations(self):
		result = search_hr_guidance("إجازة مرضية", 5)
		self.assertTrue(result["results"])
		self.assertIn("مرض", result["results"][0]["title_ar"])
		self.assertTrue(all(item["citation"]["pdf_page"] for item in result["results"]))
		self.assertTrue(all(item["citation"]["source"] for item in result["results"]))

