from urllib.parse import urlparse

import frappe
from frappe import _
from frappe.model.document import Document


FILE_MODE = "File Exchange / تبادل ملفات"
SANDBOX_MODE = "API Sandbox / واجهة تجريبية"
LIVE_MODE = "Live API / واجهة فعلية"


class SaudiGovernmentIntegration(Document):
	def validate(self):
		self._normalize_governance()
		self._validate_unique_provider_company()
		self._validate_connection()
		self._set_configuration_status()

	def _normalize_governance(self):
		self.requires_explicit_confirmation = 1
		self.allowed_operations = "preview, export, reconcile"
		if not self.api_version:
			self.api_version = "2026.1"

	def _validate_unique_provider_company(self):
		if not self.provider or not self.company:
			return
		filters = {"provider": self.provider, "company": self.company}
		existing = frappe.db.exists(self.doctype, filters)
		if existing and existing != self.name:
			frappe.throw(
				_("Only one integration profile is allowed for each provider and company."),
				title=_("Duplicate Government Integration / تكامل حكومي مكرر"),
			)

	def _validate_connection(self):
		if self.mode == FILE_MODE or not self.enabled:
			return
		if not self.base_url:
			frappe.throw(_("An approved Base URL is required for API modes."))
		parsed = urlparse(self.base_url)
		if parsed.scheme != "https" or not parsed.netloc:
			frappe.throw(_("Government API endpoints must use a valid HTTPS URL."))
		if self.mode == LIVE_MODE:
			if not self.client_id:
				frappe.throw(_("Client ID is required before enabling Live API mode."))
			has_secret = bool(self.client_secret or self.credential_reference or self.certificate_file)
			if not has_secret:
				frappe.throw(_("An encrypted secret, vault reference, or private certificate is required for Live API mode."))

	def _set_configuration_status(self):
		if not self.enabled:
			self.configuration_status = "Disabled / معطّل"
		elif self.mode == FILE_MODE:
			self.configuration_status = "Ready for File Exchange / جاهز لتبادل الملفات"
		elif self.mode == SANDBOX_MODE:
			self.configuration_status = "Ready for Test / جاهز للاختبار" if self.base_url else "Credentials Required / يلزم اعتماد"
		elif self.mode == LIVE_MODE:
			self.configuration_status = "Live / فعلي"


def safe_profile_dict(profile):
	"""Return operational metadata without credential fields."""
	return {
		"name": profile.name,
		"provider": profile.provider,
		"company": profile.company,
		"enabled": bool(profile.enabled),
		"mode": profile.mode,
		"configuration_status": profile.configuration_status,
		"api_version": profile.api_version,
		"owner_user": profile.owner_user,
		"last_tested_on": profile.last_tested_on,
		"last_successful_sync_on": profile.last_successful_sync_on,
		"last_error_summary": profile.last_error_summary,
		"has_approved_endpoint": bool(profile.base_url),
		"has_credentials": bool(profile.client_id and (profile.client_secret or profile.credential_reference or profile.certificate_file)),
	}

