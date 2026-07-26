from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from saudi_hr.saudi_hr.doctype.saudi_government_integration.saudi_government_integration import safe_profile_dict
from saudi_hr.saudi_hr.enterprise_operations import (
	CONFIRMATION_PHRASE,
	acknowledge_policy,
	confirm_provider_export,
	get_self_service_portal,
	preview_provider_export,
	search_hr_guidance,
	sync_enterprise_defaults,
)
from saudi_hr.saudi_hr.test_support import make_qa_employee, select_option


class TestComprehensiveSecurityIntegrationCycle(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.workflow_enqueue_patcher = patch("frappe.workflow.doctype.workflow_action.workflow_action.enqueue")
		self.workflow_enqueue_patcher.start()
		frappe.set_user("Administrator")
		self.company = frappe.get_all("Company", pluck="name", limit_page_length=1)[0]

	def tearDown(self):
		frappe.set_user("Administrator")
		self.workflow_enqueue_patcher.stop()
		frappe.db.rollback()
		super().tearDown()

	def _profile(self, provider_contains):
		provider = select_option("Saudi Government Integration", "provider", provider_contains)
		name = frappe.db.get_value(
			"Saudi Government Integration",
			{"provider": provider, "company": self.company},
			"name",
		)
		self.assertTrue(name)
		return frappe.get_doc("Saudi Government Integration", name)

	def test_government_export_idempotency_audit_and_failure_cycle(self):
		sync_enterprise_defaults()
		employee = make_qa_employee(self.company, "government")
		if frappe.get_meta("Employee").has_field("nationality") and frappe.db.exists("Country", "Saudi Arabia"):
			frappe.db.set_value("Employee", employee, "nationality", "Saudi Arabia")
		gosi = frappe.get_doc(
			{
				"doctype": "GOSI Contribution",
				"employee": employee,
				"company": self.company,
				"nationality": "Saudi / سعودي",
				"month": select_option("GOSI Contribution", "month", "July"),
				"year": 2026,
				"contribution_base": 12000,
			}
		).insert(ignore_permissions=True)
		self.assertGreater(gosi.total_contribution, 0)

		profile = self._profile("GOSI")
		preview = preview_provider_export(profile.name)
		self.assertGreaterEqual(preview["record_count"], 1)
		self.assertTrue(preview["can_confirm"])
		self.assertEqual(len(preview["fingerprint"]), 64)
		self.assertNotIn("client_secret", safe_profile_dict(profile))

		with self.assertRaises(frappe.ValidationError):
			confirm_provider_export(profile.name, "تأكيد غير صحيح")

		created = confirm_provider_export(profile.name, CONFIRMATION_PHRASE)
		self.assertFalse(created["reused"])
		transaction = frappe.get_doc("Saudi Government Transaction", created["transaction"])
		self.assertIn("Succeeded", transaction.status)
		self.assertEqual(transaction.record_count, created["record_count"])
		self.assertTrue(transaction.evidence_attachment)
		self.assertTrue(frappe.db.get_value("File", {"file_url": transaction.evidence_attachment}, "is_private"))

		reused = confirm_provider_export(profile.name, CONFIRMATION_PHRASE)
		self.assertTrue(reused["reused"])
		self.assertEqual(reused["transaction"], transaction.name)
		transaction.payload_summary = '{"tampered":true}'
		with self.assertRaises(frappe.ValidationError):
			transaction.save(ignore_permissions=True)

		api_profile = self._profile("Qiwa")
		api_profile.mode = select_option("Saudi Government Integration", "mode", "API Sandbox")
		api_profile.base_url = "http://unsafe.example.test"
		with self.assertRaises(frappe.ValidationError):
			api_profile.save(ignore_permissions=True)
		api_profile.reload()
		api_profile.mode = select_option("Saudi Government Integration", "mode", "API Sandbox")
		api_profile.base_url = "https://sandbox.example.test"
		api_profile.save(ignore_permissions=True)
		self.assertIn("Ready for Test", api_profile.configuration_status)
		api_profile.enabled = 0
		api_profile.save(ignore_permissions=True)
		self.assertIn("Disabled", api_profile.configuration_status)
		with self.assertRaises(frappe.ValidationError):
			preview_provider_export(api_profile.name)

	def test_employee_self_service_scope_acknowledgement_and_role_boundaries(self):
		employee = make_qa_employee(self.company, "self-service")
		other_employee = make_qa_employee(self.company, "other-scope")
		user = frappe.db.get_value("Employee", employee, "user_id")
		self.assertTrue(user)

		policy = frappe.get_doc(
			{
				"doctype": "HR Policy Document",
				"policy_title": "سياسة الخدمة الذاتية وحماية الخصوصية",
				"policy_category": select_option("HR Policy Document", "policy_category", "Conduct"),
				"company": self.company,
				"effective_date": add_days(today(), -1),
				"review_date": add_days(today(), 365),
				"policy_version": "SELF-QA-1",
				"acknowledgement_required": 1,
				"summary": "لا يرى الموظف إلا سجله وطلباته وإقراراته.",
			}
		).insert(ignore_permissions=True)
		ack = frappe.get_doc(
			{
				"doctype": "Policy Acknowledgement",
				"policy_document": policy.name,
				"employee": employee,
				"assigned_on": today(),
				"due_date": add_days(today(), 5),
			}
		).insert(ignore_permissions=True)
		other_ack = frappe.get_doc(
			{
				"doctype": "Policy Acknowledgement",
				"policy_document": policy.name,
				"employee": other_employee,
				"assigned_on": today(),
				"due_date": add_days(today(), 5),
			}
		).insert(ignore_permissions=True)

		frappe.set_user(user)
		portal = get_self_service_portal()
		self.assertEqual(portal["mode"], "personal")
		self.assertEqual(portal["employee"].name, employee)
		self.assertEqual(portal["summary"]["pending_acknowledgements"], 1)
		self.assertEqual(portal["pending_acknowledgements"][0].name, ack.name)

		own_grievance = frappe.get_doc(
			{
				"doctype": "Employee Grievance",
				"company": self.company,
				"grievance_date": today(),
				"grievance_type": select_option("Employee Grievance", "grievance_type", "Other"),
				"grievance_summary": "طلب ذاتي تجريبي مرتبط بصاحب الحساب فقط.",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(own_grievance.employee, employee)

		cross_scope = frappe.get_doc(
			{
				"doctype": "Employee Grievance",
				"employee": other_employee,
				"company": self.company,
				"grievance_date": today(),
				"grievance_type": select_option("Employee Grievance", "grievance_type", "Other"),
				"grievance_summary": "يجب منع إنشاء تظلم باسم موظف آخر.",
			}
		)
		with self.assertRaises(frappe.PermissionError):
			cross_scope.insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			acknowledge_policy(ack.name, "صيغة غير صحيحة")
		ack_result = acknowledge_policy(ack.name, "أقر بالاطلاع والفهم")
		self.assertIn("Acknowledged", ack_result["status"])
		self.assertEqual(len(ack_result["fingerprint"]), 64)
		with self.assertRaises(frappe.PermissionError):
			acknowledge_policy(other_ack.name, "أقر بالاطلاع والفهم")

		guidance = search_hr_guidance("الإجازة", 3)
		self.assertGreater(guidance["count"], 0)
		self.assertTrue(guidance["results"][0]["citation"]["pdf_page"])
		sync_enterprise_defaults()
		profile = self._profile("GOSI")
		frappe.set_user(user)
		with self.assertRaises(frappe.PermissionError):
			preview_provider_export(profile.name)

		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			search_hr_guidance("الأجر", 3)
