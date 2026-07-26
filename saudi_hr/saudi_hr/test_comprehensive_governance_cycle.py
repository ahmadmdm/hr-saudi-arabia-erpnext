from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from saudi_hr.saudi_hr.doctype.disciplinary_procedure.disciplinary_procedure import create_decision_log
from saudi_hr.saudi_hr.doctype.investigation_record.investigation_record import create_warning_notice
from saudi_hr.saudi_hr.test_support import make_qa_employee, select_option


class TestComprehensiveGovernanceCycle(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.workflow_enqueue_patcher = patch("frappe.workflow.doctype.workflow_action.workflow_action.enqueue")
		self.workflow_enqueue_patcher.start()
		frappe.set_user("Administrator")
		self.company = frappe.get_all("Company", pluck="name", limit_page_length=1)[0]
		self.employee = make_qa_employee(self.company, "governance")
		department_label = f"Saudi Governance QA {frappe.generate_hash(length=8)}"
		self.department = frappe.get_doc({"doctype": "Department", "department_name": department_label, "company": self.company, "is_group": 0}).insert(ignore_permissions=True).name
		frappe.db.set_value("Employee", self.employee, {"department": self.department, "date_of_joining": "2023-01-01"})

	def tearDown(self):
		frappe.set_user("Administrator")
		self.workflow_enqueue_patcher.stop()
		frappe.db.rollback()
		super().tearDown()

	def test_policy_acknowledgement_training_and_regulatory_cycle(self):
		policy = frappe.get_doc({"doctype": "HR Policy Document", "policy_title": "سياسة السلوك المهني وحماية الحقوق", "policy_category": select_option("HR Policy Document", "policy_category", "Conduct"), "company": self.company, "effective_date": add_days(today(), -1), "review_date": add_days(today(), 365), "owner_user": "Administrator", "policy_version": "1.0-QA", "target_scope": select_option("HR Policy Document", "target_scope", "Department Employees"), "target_department": self.department, "acknowledgement_required": 1, "acknowledgement_due_days": 5, "compliance_risk": select_option("HR Policy Document", "compliance_risk", "High"), "summary": "سياسة ثنائية اللغة توضح السلوك والحقوق وقنوات الاعتراض."}).insert(ignore_permissions=True)
		self.assertIn("Active", policy.status)
		self.assertEqual(policy.sync_policy_acknowledgements(), 1)
		ack_name = frappe.db.get_value("Policy Acknowledgement", {"policy_document": policy.name, "employee": self.employee}, "name")
		ack = frappe.get_doc("Policy Acknowledgement", ack_name)
		self.assertIn("Pending", ack.acknowledgement_status)
		ack.acknowledged_on = today()
		ack.acknowledgement_channel = select_option("Policy Acknowledgement", "acknowledgement_channel", "Portal")
		ack.acknowledgement_user = frappe.db.get_value("Employee", self.employee, "user_id")
		ack.acknowledgement_consent_text = "أقر بأنني قرأت السياسة وفهمتها"
		ack.acknowledgement_fingerprint = frappe.generate_hash(length=40)
		ack.acknowledgement_ip = "127.0.0.1"
		ack.save(ignore_permissions=True)
		self.assertIn("Acknowledged", ack.acknowledgement_status)
		policy.reload()
		self.assertEqual(policy.acknowledged_count, 1)
		self.assertEqual(policy.pending_acknowledgement_count, 0)
		ack.acknowledgement_ip = "127.0.0.2"
		with self.assertRaises(frappe.ValidationError):
			ack.save(ignore_permissions=True)
		training = frappe.get_doc({"doctype": "Training Record", "employee": self.employee, "company": self.company, "training_title": "السلامة المهنية والامتثال لنظام العمل", "training_type": select_option("Training Record", "training_type", "Mandatory Safety"), "training_start_date": today(), "training_end_date": today(), "attendance_status": select_option("Training Record", "attendance_status", "Attended"), "result": select_option("Training Record", "result", "Pass"), "training_provider_rating": select_option("Training Record", "training_provider_rating", "5 - Excellent")}).insert(ignore_permissions=True)
		training.flags.ignore_permissions = True
		training.submit()
		self.assertEqual(training.docstatus, 1)
		task = frappe.get_doc({"doctype": "Saudi Regulatory Task", "task_title": "مراجعة تطبيق سياسة السلوك", "company": self.company, "task_date": today(), "due_date": add_days(today(), 7), "assigned_to": "Administrator", "policy_document": policy.name, "priority": select_option("Saudi Regulatory Task", "priority", "High"), "task_category": select_option("Saudi Regulatory Task", "task_category", "Policy"), "progress_percentage": 25}).insert(ignore_permissions=True)
		self.assertIn("In Progress", task.status)
		task.completed_on = add_days(today(), 1)
		task.save(ignore_permissions=True)
		self.assertIn("Completed", task.status)
		self.assertEqual(task.progress_percentage, 100)

	def test_grievance_investigation_discipline_appeal_and_dispute_cycle(self):
		grievance = frappe.get_doc({"doctype": "Employee Grievance", "employee": self.employee, "company": self.company, "grievance_date": "2026-07-01", "grievance_type": select_option("Employee Grievance", "grievance_type", "Manager Conduct"), "grievance_channel": select_option("Employee Grievance", "grievance_channel", "Portal"), "severity": select_option("Employee Grievance", "severity", "High"), "assigned_to": "Administrator", "grievance_summary": "طلب مراجعة إجراء إداري وسماع إفادة الموظف."}).insert(ignore_permissions=True)
		self.assertEqual(str(grievance.response_due_date), "2026-07-06")
		grievance.first_response_date = "2026-07-02"
		grievance.save(ignore_permissions=True)
		self.assertIn("In Review", grievance.status)
		grievance.resolution_date = "2026-07-03"
		grievance.resolution_summary = "تمت مراجعة الإفادات واتخاذ إجراء تصحيحي."
		grievance.save(ignore_permissions=True)
		self.assertIn("Resolved", grievance.status)
		invalid_grievance = frappe.copy_doc(grievance)
		invalid_grievance.response_due_date = "2026-06-30"
		with self.assertRaises(frappe.ValidationError):
			invalid_grievance.insert(ignore_permissions=True)
		investigation = frappe.get_doc({"doctype": "Investigation Record", "subject_employee": self.employee, "company": self.company, "case_type": select_option("Investigation Record", "case_type", "Misconduct"), "allegation_date": "2026-07-01", "investigator": "Administrator", "investigation_start_date": "2026-07-02", "investigation_end_date": "2026-07-03", "allegation_summary": "مخالفة إجرائية تستلزم تحقيقًا موثقًا.", "findings": "ثبتت المخالفة البسيطة بعد سماع الإفادات.", "recommendation": "إنذار كتابي أول وتدريب تصحيحي."}).insert(ignore_permissions=True)
		self.assertIn("Findings Issued", investigation.status)
		warning_result = create_warning_notice(investigation.name)
		warning = frappe.get_doc("Employee Warning Notice", warning_result["warning_notice"])
		self.assertEqual(warning.employee, self.employee)
		self.assertIn("Issued", warning.status)
		procedure = frappe.get_doc({"doctype": "Disciplinary Procedure", "investigation_record": investigation.name, "violation_type": select_option("Disciplinary Procedure", "violation_type", "Misconduct"), "incident_description": "إجراء تأديبي متدرج قائم على التحقيق.", "penalty_type": select_option("Disciplinary Procedure", "penalty_type", "First Written Warning"), "penalty_start_date": "2026-07-04", "decision_notes": "اعتماد إنذار أول مع حق الاستئناف.", "hr_manager_approval": 1, "appeal_date": "2026-07-11"}).insert(ignore_permissions=True)
		procedure.flags.ignore_permissions = True
		procedure.flags.ignore_workflow = True
		procedure.submit()
		self.assertIn("Decision Issued", procedure.status)
		decision_result = create_decision_log(procedure.name)
		decision = frappe.get_doc("Disciplinary Decision Log", decision_result["decision_log"])
		self.assertEqual(decision.employee, self.employee)
		self.assertIn("Issued", decision.decision_status)
		appeal = frappe.get_doc({"doctype": "Disciplinary Appeal", "disciplinary_procedure": procedure.name, "employee": self.employee, "company": self.company, "appeal_date": "2026-07-05", "appeal_type": select_option("Disciplinary Appeal", "appeal_type", "Against Warning"), "assigned_to": "Administrator", "hearing_date": "2026-07-06", "grounds_for_appeal": "طلب مراجعة تناسب الجزاء مع الواقعة.", "decision": select_option("Disciplinary Appeal", "decision", "Modified"), "decision_date": "2026-07-07"}).insert(ignore_permissions=True)
		self.assertIn("Decided", appeal.status)
		dispute = frappe.get_doc({"doctype": "Labor Dispute", "employee": self.employee, "company": self.company, "dispute_date": "2026-07-08", "dispute_type": select_option("Labor Dispute", "dispute_type", "Overtime"), "dispute_description": "نزاع تجريبي لاختبار مسار الوساطة الداخلية."}).insert(ignore_permissions=True)
		dispute.flags.ignore_permissions = True
		dispute.submit()
		self.assertIn("Internal Mediation", dispute.status)

	def test_injury_medical_inspection_and_corrective_action_cycle(self):
		injury = frappe.get_doc({"doctype": "Work Injury", "employee": self.employee, "company": self.company, "injury_date": add_days(today(), -2), "injury_type": select_option("Work Injury", "injury_type", "Industrial Accident"), "severity": select_option("Work Injury", "severity", "Minor"), "injury_description": "إصابة بسيطة أثناء مناولة مواد مكتبية.", "medical_treatment_type": select_option("Work Injury", "medical_treatment_type", "First Aid"), "gosi_form_25_submitted": 1, "gosi_case_number": f"GOSI-QA-{frappe.generate_hash(length=8)}"}).insert(ignore_permissions=True)
		self.assertEqual(str(injury.gosi_submission_date), today())
		injury.flags.ignore_permissions = True
		injury.submit()
		self.assertIn("Reported to GOSI", injury.status)
		medical = frappe.get_doc({"doctype": "Medical Examination", "employee": self.employee, "company": self.company, "examination_type": select_option("Medical Examination", "examination_type", "Post-Injury"), "examination_date": today(), "work_injury_reference": injury.name, "fitness_result": select_option("Medical Examination", "fitness_result", "Fit with Restrictions"), "restrictions_notes": "تجنب حمل الأوزان لمدة يومين."}).insert(ignore_permissions=True)
		medical.flags.ignore_permissions = True
		medical.submit()
		injury.reload()
		self.assertTrue(injury.medical_examination_done)
		invalid_medical = frappe.get_doc({"doctype": "Medical Examination", "employee": self.employee, "company": self.company, "examination_type": select_option("Medical Examination", "examination_type", "Periodic"), "examination_date": today(), "fitness_result": select_option("Medical Examination", "fitness_result", "Temporarily Unfit")})
		with self.assertRaises(frappe.ValidationError):
			invalid_medical.insert(ignore_permissions=True)
		inspection = frappe.get_doc({"doctype": "Labor Inspection", "inspection_title": "تفتيش امتثال تجريبي شامل", "inspection_authority": select_option("Labor Inspection", "inspection_authority", "Internal Audit"), "company": self.company, "inspection_date": today(), "inspection_scope": select_option("Labor Inspection", "inspection_scope", "Routine Inspection"), "internal_owner": "Administrator", "follow_up_due_date": add_days(today(), 7), "findings_summary": "ملاحظة واحدة تتطلب إجراءً تصحيحيًا موثقًا.", "violations": [{"violation_category": select_option("Labor Inspection Violation", "violation_category", "Record Keeping"), "severity": select_option("Labor Inspection Violation", "severity", "High"), "status": select_option("Labor Inspection Violation", "status", "Open"), "violation_description": "سجل واحد بحاجة إلى استكمال دليل الحفظ.", "corrective_action": "إرفاق الدليل وإغلاق الملاحظة.", "fine_amount": 5000, "correction_due_date": add_days(today(), 7)}]}).insert(ignore_permissions=True)
		self.assertEqual(inspection.total_violations, 1)
		self.assertEqual(inspection.open_violations, 1)
		self.assertEqual(inspection.total_fines, 5000)
		inspection.flags.ignore_permissions = True
		inspection.submit()
		inspection.reload()
		self.assertTrue(inspection.violations[0].action_log)
		action = frappe.get_doc("HR Compliance Action Log", inspection.violations[0].action_log)
		self.assertIn("In Progress", action.status)
		action.completed_on = add_days(today(), 1)
		action.save(ignore_permissions=True)
		self.assertIn("Completed", action.status)
		invalid_inspection = frappe.get_doc({"doctype": "Labor Inspection", "inspection_title": "تفتيش بلا مخالفات", "inspection_authority": select_option("Labor Inspection", "inspection_authority", "Internal Audit"), "company": self.company, "inspection_date": today(), "inspection_scope": select_option("Labor Inspection", "inspection_scope", "Routine Inspection"), "findings_summary": "يجب رفض النموذج لأنه بلا صفوف."})
		with self.assertRaises(frappe.ValidationError):
			invalid_inspection.insert(ignore_permissions=True)
