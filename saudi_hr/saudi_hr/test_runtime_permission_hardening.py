from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import get_datetime

from saudi_hr.saudi_hr import api as api_module
from saudi_hr.saudi_hr import voice_verification as voice_module
from saudi_hr.saudi_hr.doctype.disciplinary_procedure import disciplinary_procedure as disciplinary_module
from saudi_hr.saudi_hr.doctype.hr_policy_document import hr_policy_document as policy_module
from saudi_hr.saudi_hr.doctype.investigation_record import investigation_record as investigation_module
from saudi_hr.saudi_hr.doctype.labor_inspection import labor_inspection as labor_module
from saudi_hr.saudi_hr.doctype.legal_reference_matrix import legal_reference_matrix as legal_module
from saudi_hr.saudi_hr.doctype.saudi_hr_settings import saudi_hr_settings as settings_module


class _InsertableDoc:
	def __init__(self, doctype=None, name=None):
		self.doctype = doctype or "Test DocType"
		self.name = name or f"{self.doctype}-0001"
		self.inserted = False
		self.submitted = False

	def update(self, payload):
		for key, value in payload.items():
			setattr(self, key, value)
		return self

	def insert(self):
		self.inserted = True
		return self

	def submit(self):
		self.submitted = True
		return self


class _SettingsDoc:
	def __init__(self):
		self.branch_employee_directory = []
		self.saved = False

	def set(self, fieldname, value):
		setattr(self, fieldname, value)

	def append(self, fieldname, value):
		getattr(self, fieldname).append(value)

	def save(self):
		self.saved = True
		return self


class _VoiceProfileDoc:
	def __init__(self, employee="EMP-0001"):
		self.name = employee
		self.employee = employee
		self.employee_name = "Ali"
		self.voiceprint_embedding = "[0.1, 0.2]"
		self.is_active = 1
		self.enrollment_status = voice_module.VOICE_PROFILE_STATUS_ENROLLED
		self.last_enrolled_on = "2026-04-01 08:00:00"
		self.transcript_preview = "1234"
		self.last_challenge_text = "1234"
		self.last_anti_spoof_score = 0.95
		self.last_speech_match_score = 0.95
		self.last_speaker_match_score = 0.95
		self.flags = SimpleNamespace(ignore_permissions=False)
		self.saved = False

	def save(self):
		self.saved = True
		return self


class TestRuntimePermissionHardening(FrappeTestCase):
	def test_submit_mobile_leave_request_enforces_create_permission(self):
		leave_doc = _InsertableDoc(doctype="Saudi Annual Leave", name="SAL-0001")
		profile = SimpleNamespace(employee_name="Ali", company="amd", department="HR")

		with patch.object(api_module, "_require_employee_context", return_value=("EMP-0001", profile)), patch.object(
			api_module, "_load_json_param", return_value=[]
		), patch.object(api_module, "_build_mobile_leave_doc", return_value=leave_doc), patch.object(
			api_module, "_attach_files", return_value=[]
		), patch.object(api_module, "assert_doctype_permissions") as assert_permissions, patch.object(
			api_module.frappe.db, "commit"
		):
			result = api_module.submit_mobile_leave_request("annual", "2026-04-02")

		assert_permissions.assert_called_once_with("Saudi Annual Leave", "create", doc=leave_doc)
		self.assertTrue(leave_doc.inserted)
		self.assertEqual(result["name"], "SAL-0001")

	def test_do_mobile_checkin_enforces_checkin_and_attendance_permissions(self):
		checkin_doc = _InsertableDoc(doctype="Saudi Employee Checkin", name="CHK-0001")
		attendance_doc = _InsertableDoc(doctype="Saudi Daily Attendance", name="ATT-0001")
		profile = SimpleNamespace(branch="HQ")
		today_checkins = [frappe._dict({"name": "CHK-IN", "log_type": "IN", "time": "2026-04-02 08:00:00"})]

		with patch.object(api_module, "_require_employee_context", return_value=("EMP-0001", profile)), patch.object(
			api_module, "_load_json_param", return_value=[]
		), patch.object(api_module, "_get_location_for_branch", return_value=None), patch.object(
			api_module, "_get_todays_checkins", return_value=today_checkins
		), patch.object(api_module, "now_datetime", return_value=get_datetime("2026-04-02 17:00:00")), patch.object(
			api_module.frappe, "new_doc", side_effect=[checkin_doc, attendance_doc]
		), patch.object(api_module, "_attach_files", return_value=[]), patch.object(
			api_module, "_get_contract_hours_per_day", return_value=8
		), patch.object(api_module.frappe.db, "get_value", return_value=None), patch.object(
			api_module.frappe.db, "commit"
		), patch.object(api_module, "assert_doctype_permissions") as assert_permissions:
			result = api_module.do_mobile_checkin(latitude="24.7", longitude="46.6")

		self.assertEqual(assert_permissions.call_args_list[0].args[:2], ("Saudi Employee Checkin", "create"))
		self.assertEqual(assert_permissions.call_args_list[1].args[:2], ("Saudi Daily Attendance", ("create", "submit")))
		self.assertTrue(checkin_doc.inserted)
		self.assertTrue(attendance_doc.inserted)
		self.assertTrue(attendance_doc.submitted)
		self.assertEqual(result["attendance_name"], "ATT-0001")

	def test_do_mobile_checkin_rejects_attendance_attachments(self):
		profile = SimpleNamespace(branch="HQ")

		with patch.object(api_module, "_require_employee_context", return_value=("EMP-0001", profile)), patch.object(
			api_module, "_load_json_param", side_effect=[[{"filename": "legacy-note.txt", "content": "ZmFrZQ=="}], None]
		):
			with self.assertRaises(frappe.ValidationError):
				api_module.do_mobile_checkin(latitude="24.7", longitude="46.6", attachments_json="[]")

	def test_do_mobile_checkin_requires_voice_when_policy_requires_it(self):
		profile = SimpleNamespace(branch="HQ")

		with patch.object(api_module, "_require_employee_context", return_value=("EMP-0001", profile)), patch.object(
			api_module, "_load_json_param", side_effect=[[], None]
		), patch.object(api_module, "_get_location_for_branch", return_value=None), patch.object(
			api_module, "_get_todays_checkins", return_value=[]
		), patch.object(api_module, "resolve_mobile_attendance_policy", return_value={"voice_policy": "Required / إلزامي"}):
			with self.assertRaises(frappe.PermissionError):
				api_module.do_mobile_checkin(latitude="24.7", longitude="46.6")

	def test_do_mobile_checkin_requires_initial_voice_enrollment_when_enabled(self):
		profile = SimpleNamespace(branch="HQ")

		with patch.object(api_module, "_require_employee_context", return_value=("EMP-0001", profile)), patch.object(
			api_module, "_load_json_param", side_effect=[[], None]
		), patch.object(api_module, "get_voice_runtime_status", return_value={"enabled": True, "runtime_ready": True}), patch.object(
			api_module, "get_employee_voice_profile_status", return_value={"can_self_enroll": True}
		):
			with self.assertRaises(frappe.PermissionError):
				api_module.do_mobile_checkin(latitude="24.7", longitude="46.6")

	def test_enroll_employee_voice_profile_blocks_self_reenrollment(self):
		with patch.object(voice_module, "get_voice_runtime_settings", return_value={"enabled": True}), patch.object(
			voice_module, "get_employee_voice_profile_status", return_value={"profile_exists": True, "can_self_enroll": False}
		):
			with self.assertRaises(frappe.PermissionError):
				voice_module.enroll_employee_voice_profile("EMP-0001", {"content": "ZmFrZQ=="}, "token")

	def test_reset_employee_voice_profile_clears_profile(self):
		profile_doc = _VoiceProfileDoc()

		with patch.object(voice_module.frappe, "only_for") as only_for, patch.object(
			voice_module.frappe.db, "exists", return_value=profile_doc.name
		), patch.object(voice_module.frappe, "get_doc", return_value=profile_doc), patch.object(
			voice_module.frappe.db, "commit"
		):
			result = voice_module.reset_employee_voice_profile(employee="EMP-0001")

		only_for.assert_called_once_with(voice_module.VOICE_PROFILE_RESET_ROLES)
		self.assertEqual(profile_doc.enrollment_status, voice_module.VOICE_PROFILE_STATUS_NOT_ENROLLED)
		self.assertEqual(profile_doc.is_active, 0)
		self.assertIsNone(profile_doc.voiceprint_embedding)
		self.assertTrue(profile_doc.saved)
		self.assertEqual(result["employee"], "EMP-0001")

	def test_sync_directory_table_saves_with_explicit_permission_check(self):
		settings_doc = _SettingsDoc()
		rows = [frappe._dict({"name": "EMP-0001", "employee_name": "Ali", "user_id": "ali@example.com", "branch": "HQ", "department": "HR", "company": "amd"})]

		with patch.object(settings_module.frappe, "get_single", return_value=settings_doc), patch.object(
			settings_module, "_get_employee_directory_rows", return_value=rows
		), patch.object(settings_module, "assert_doctype_permissions") as assert_permissions, patch.object(
			settings_module.frappe.db, "commit"
		):
			result = settings_module._sync_directory_table()

		assert_permissions.assert_called_once_with("Saudi HR Settings", "write", doc=settings_doc)
		self.assertTrue(result.saved)
		self.assertEqual(len(result.branch_employee_directory), 1)

	def test_ensure_branch_checks_create_permission(self):
		branch_doc = _InsertableDoc(doctype="Branch", name="HQ")

		with patch.object(settings_module.frappe.db, "exists", return_value=False), patch.object(
			settings_module.frappe, "get_doc", return_value=branch_doc
		), patch.object(settings_module, "assert_doctype_permissions") as assert_permissions:
			name = settings_module._ensure_branch("HQ")

		assert_permissions.assert_called_once_with("Branch", "create")
		self.assertTrue(branch_doc.inserted)
		self.assertEqual(name, "HQ")

	def test_create_warning_notice_enforces_create_permission(self):
		record = SimpleNamespace(
			employee_warning_notice=None,
			subject_employee="EMP-0001",
			company="amd",
			department="HR",
			investigation_end_date="2026-04-02",
			name="INV-0001",
			legal_reference_matrix="LRM-0001",
			allegation_summary="Issue",
			recommendation="Warn",
			db_set=lambda *args, **kwargs: None,
		)
		warning_doc = _InsertableDoc(doctype="Employee Warning Notice", name="WARN-0001")

		def _get_doc(*args, **kwargs):
			if len(args) == 2:
				return record
			return warning_doc

		with patch.object(investigation_module.frappe, "get_doc", side_effect=_get_doc), patch.object(
			investigation_module.frappe.db, "exists", return_value=False
		), patch.object(investigation_module.frappe, "has_permission"), patch.object(
			investigation_module, "assert_doctype_permissions"
		) as assert_permissions:
			result = investigation_module.create_warning_notice("INV-0001")

		assert_permissions.assert_called_once_with("Employee Warning Notice", "create", doc=warning_doc)
		self.assertTrue(warning_doc.inserted)
		self.assertEqual(result["warning_notice"], "WARN-0001")

	def test_create_decision_log_enforces_create_permission(self):
		doc = SimpleNamespace(
			disciplinary_decision_log=None,
			legal_reference_matrix=None,
			name="DISC-0001",
			employee="EMP-0001",
			company="amd",
			department="HR",
			investigation_record="INV-0001",
			employee_warning_notice="WARN-0001",
			docstatus=1,
			penalty_type="Written Warning",
			penalty_start_date="2026-04-02",
			penalty_end_date=None,
			decision_notes="Decision",
			incident_description="Incident",
			appeal_date=None,
			db_set=lambda *args, **kwargs: None,
		)
		decision_doc = _InsertableDoc(doctype="Disciplinary Decision Log", name="DDL-0001")

		def _get_doc(*args, **kwargs):
			if len(args) == 2:
				return doc
			return decision_doc

		with patch.object(disciplinary_module.frappe, "get_doc", side_effect=_get_doc), patch.object(
			disciplinary_module.frappe.db, "exists", return_value=False
		), patch.object(disciplinary_module.frappe, "has_permission"), patch.object(
			disciplinary_module, "assert_doctype_permissions"
		) as assert_permissions:
			result = disciplinary_module.create_decision_log("DISC-0001")

		assert_permissions.assert_called_once_with("Disciplinary Decision Log", "create", doc=decision_doc)
		self.assertTrue(decision_doc.inserted)
		self.assertEqual(result["decision_log"], "DDL-0001")

	def test_create_regulatory_task_enforces_create_permission(self):
		task_doc = _InsertableDoc(doctype="Saudi Regulatory Task", name="TASK-0001")
		matrix = SimpleNamespace(
			name="LRM-0001",
			db_set=lambda *args, **kwargs: None,
			_get_task_blueprints=lambda: [{"doctype": "Saudi Regulatory Task", "task_title": "Task A"}],
		)

		with patch.object(legal_module.frappe.db, "get_value", return_value=None), patch.object(
			legal_module.frappe, "get_doc", return_value=task_doc
		), patch.object(legal_module.frappe.db, "count", return_value=1), patch.object(
			legal_module, "assert_doctype_permissions"
		) as assert_permissions:
			created_names, created = legal_module.LegalReferenceMatrix.create_regulatory_task(matrix)

		assert_permissions.assert_called_once_with("Saudi Regulatory Task", "create", doc=task_doc)
		self.assertTrue(task_doc.inserted)
		self.assertEqual(created_names, ["TASK-0001"])
		self.assertTrue(created)

	def test_sync_policy_acknowledgements_enforces_create_permission(self):
		ack_doc = _InsertableDoc(doctype="Policy Acknowledgement", name="ACK-0001")
		policy = SimpleNamespace(
			acknowledgement_required=1,
			status="Active / سارية",
			acknowledgement_due_days=7,
			name="POL-0001",
			policy_title="Travel Policy",
			policy_version="1.0",
			article_reference="Art. 1",
			legal_reference="Rule",
			acknowledged_count=0,
			pending_acknowledgement_count=0,
			get_target_employees=lambda: [frappe._dict({"name": "EMP-0001", "employee_name": "Ali", "company": "amd", "department": "HR"})],
			db_set=lambda *args, **kwargs: None,
			reload=lambda: None,
			_update_acknowledgement_summary=lambda: None,
		)

		with patch.object(policy_module.frappe.db, "exists", return_value=False), patch.object(
			policy_module.frappe, "get_doc", return_value=ack_doc
		), patch.object(policy_module, "assert_doctype_permissions") as assert_permissions:
			created = policy_module.HRPolicyDocument.sync_policy_acknowledgements(policy)

		assert_permissions.assert_called_once_with("Policy Acknowledgement", "create", doc=ack_doc)
		self.assertTrue(ack_doc.inserted)
		self.assertEqual(created, 1)

	def test_create_compliance_actions_enforces_create_permission(self):
		action_doc = _InsertableDoc(doctype="HR Compliance Action Log", name="ACT-0001")
		row = frappe._dict({
			"status": "Open / مفتوح",
			"action_log": None,
			"violation_category": "License",
			"correction_due_date": "2026-04-10",
			"violation_description": "Issue",
			"corrective_action": "Fix",
			"name": "ROW-0001",
		})
		doc = SimpleNamespace(
			violations=[row],
			name="LAB-0001",
			company="amd",
			inspection_date="2026-04-02",
			internal_owner="hr@example.com",
			follow_up_due_date="2026-04-15",
		)

		with patch.object(labor_module.frappe.db, "exists", return_value=False), patch.object(
			labor_module.frappe, "get_doc", return_value=action_doc
		), patch.object(labor_module, "assert_doctype_permissions") as assert_permissions, patch.object(
			labor_module.frappe.db, "set_value"
		):
			labor_module.LaborInspection._create_compliance_actions(doc)

		assert_permissions.assert_called_once_with("HR Compliance Action Log", "create", doc=action_doc)
		self.assertTrue(action_doc.inserted)
		self.assertEqual(row.action_log, "ACT-0001")