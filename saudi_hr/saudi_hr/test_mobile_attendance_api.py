from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr import api as api_module


class _UserDoc:
	def __init__(self, user="api@example.com", api_key=None):
		self.name = user
		self.enabled = 1
		self.full_name = "API User"
		self.api_key = api_key
		self.api_secret = None
		self.flags = SimpleNamespace(ignore_permissions=False)
		self.saved = False

	def save(self):
		self.saved = True
		return self


class TestMobileAttendanceApi(FrappeTestCase):
	def test_issue_mobile_attendance_api_credentials_allows_current_user(self):
		user_doc = _UserDoc()

		with patch.object(api_module.frappe, "session", SimpleNamespace(user="api@example.com")), patch.object(
			api_module.frappe, "get_doc", return_value=user_doc
		), patch.object(api_module.frappe, "generate_hash", side_effect=["APIKEY123", "SECRET456"]), patch.object(
			api_module.frappe, "get_roles", return_value=["Employee Self Service"]
		), patch.object(api_module.frappe.db, "get_value", side_effect=["EMP-0001", None]), patch.object(
			api_module.frappe.db, "commit"
		), patch.object(api_module, "get_url", return_value="https://example.test"):
			result = api_module.issue_mobile_attendance_api_credentials()

		self.assertEqual(result["user"], "api@example.com")
		self.assertEqual(result["employee"], "EMP-0001")
		self.assertEqual(result["api_key"], "APIKEY123")
		self.assertEqual(result["api_secret"], "SECRET456")
		self.assertEqual(result["authorization_header"], "token APIKEY123:SECRET456")
		self.assertTrue(user_doc.saved)

	def test_issue_mobile_attendance_api_credentials_blocks_other_users_without_system_manager(self):
		with patch.object(api_module.frappe, "session", SimpleNamespace(user="api@example.com")), patch.object(
			api_module.frappe, "get_roles", return_value=["Employee Self Service"]
		):
			with self.assertRaises(frappe.PermissionError):
				api_module.issue_mobile_attendance_api_credentials(user="other@example.com")

	def test_mobile_attendance_api_checkin_delegates_to_existing_logic(self):
		with patch.object(api_module, "do_mobile_checkin", return_value={"success": True, "checkin_name": "CHK-0001"}) as checkin:
			result = api_module.mobile_attendance_api_checkin(
				payload_json={
					"latitude": "24.7",
					"longitude": "46.6",
					"verification_mode": "gps",
				}
			)

		checkin.assert_called_once_with(
			latitude="24.7",
			longitude="46.6",
			verification_mode="gps",
			verification_note=None,
			attachments_json=None,
			challenge_token=None,
			voice_payload_json=None,
		)
		self.assertTrue(result["ok"])
		self.assertEqual(result["data"]["checkin_name"], "CHK-0001")

	def test_mobile_attendance_api_leave_request_delegates_to_existing_logic(self):
		with patch.object(api_module, "submit_mobile_leave_request", return_value={"name": "SAL-0001"}) as submit_leave:
			result = api_module.mobile_attendance_api_leave_request(
				payload_json={
					"request_type": "annual",
					"start_date": "2026-05-01",
					"end_date": "2026-05-03",
				}
			)

		submit_leave.assert_called_once_with(
			request_type="annual",
			start_date="2026-05-01",
			end_date="2026-05-03",
			reason=None,
			leave_subtype=None,
			relationship_to_deceased=None,
			medical_certificate_no=None,
			hospital_name=None,
			expected_delivery_date=None,
			actual_delivery_date=None,
			half_day=0,
			attachments_json=None,
		)
		self.assertTrue(result["ok"])
		self.assertEqual(result["data"]["name"], "SAL-0001")

	def test_get_mobile_attendance_api_contract_returns_reference(self):
		with patch.object(api_module.frappe, "session", SimpleNamespace(user="api@example.com")), patch.object(
			api_module.frappe, "get_roles", return_value=["Employee Self Service"]
		), patch.object(api_module.frappe.db, "get_value", side_effect=["EMP-0001", None]), patch.object(
			api_module, "get_url", return_value="https://example.test"
		):
			result = api_module.get_mobile_attendance_api_contract()

		self.assertEqual(result["actor"]["user"], "api@example.com")
		self.assertEqual(result["actor"]["employee"], "EMP-0001")
		self.assertEqual(result["auth"]["scheme"], "token")
		self.assertGreaterEqual(len(result["endpoints"]), 4)