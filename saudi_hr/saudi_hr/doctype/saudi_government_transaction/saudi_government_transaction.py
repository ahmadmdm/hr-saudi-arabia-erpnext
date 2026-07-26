import frappe
from frappe import _
from frappe.model.document import Document


class SaudiGovernmentTransaction(Document):
	PROTECTED_FIELDS = {
		"integration_profile",
		"provider",
		"company",
		"operation",
		"direction",
		"initiated_by",
		"started_on",
		"record_count",
		"payload_schema_version",
		"request_fingerprint",
		"idempotency_key",
		"payload_summary",
	}

	def validate(self):
		self._validate_profile_identity()
		self._protect_audit_identity()

	def _validate_profile_identity(self):
		if not self.integration_profile:
			return
		provider, company = frappe.db.get_value(
			"Saudi Government Integration",
			self.integration_profile,
			["provider", "company"],
		)
		if not provider:
			frappe.throw(_("The selected government integration profile does not exist."))
		self.provider = provider
		self.company = company

	def _protect_audit_identity(self):
		if self.is_new() or getattr(self.flags, "allow_audit_update", False):
			return
		before = self.get_doc_before_save()
		if not before:
			return
		changed = [field for field in self.PROTECTED_FIELDS if self.get(field) != before.get(field)]
		if changed:
			frappe.throw(
				_("Government transaction audit identity cannot be changed after creation: {0}").format(", ".join(sorted(changed))),
				title=_("Protected Audit Record / سجل تدقيق محمي"),
			)
