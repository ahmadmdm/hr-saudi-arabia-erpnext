from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from saudi_hr.saudi_hr.doctype.saudi_shift_assignment_tool.saudi_shift_assignment_tool import create_assignments
from saudi_hr.saudi_hr.test_support import make_qa_employee, select_option


class TestComprehensiveTimePayrollCycle(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.workflow_enqueue_patcher = patch("frappe.workflow.doctype.workflow_action.workflow_action.enqueue")
		self.workflow_enqueue_patcher.start()
		frappe.set_user("Administrator")
		self.company = frappe.get_all("Company", pluck="name", limit_page_length=1)[0]
		self.employee = make_qa_employee(self.company, "time-payroll")
		frappe.db.set_value("Employee", self.employee, "date_of_joining", "2023-01-01")
		if frappe.get_meta("Employee").has_field("nationality") and frappe.db.exists("Country", "Saudi Arabia"):
			frappe.db.set_value("Employee", self.employee, "nationality", "Saudi Arabia")

	def tearDown(self):
		frappe.set_user("Administrator")
		self.workflow_enqueue_patcher.stop()
		frappe.db.rollback()
		super().tearDown()

	def test_shift_checkin_daily_and_monthly_attendance_cycle(self):
		location = frappe.get_doc(
			{
				"doctype": "Attendance Location",
				"location_name": "Riyadh QA Office",
				"latitude": 24.7136,
				"longitude": 46.6753,
				"allowed_radius_meters": 120,
			}
		).insert(ignore_permissions=True)
		self.assertAlmostEqual(float(location.latitude), 24.7136, places=4)
		self.assertIn("FeatureCollection", location.geolocation)

		shift = frappe.get_doc(
			{
				"doctype": "Saudi Shift Type",
				"shift_name": f"Saudi QA Day {frappe.generate_hash(length=6)}",
				"start_time": "08:00:00",
				"end_time": "17:00:00",
				"attendance_location": location.name,
			}
		).insert(ignore_permissions=True)

		created = create_assignments(shift.name, "2026-06-01", "2026-06-30", [self.employee])
		self.assertEqual(created["count"], 1)
		assignment = frappe.get_doc("Saudi Shift Assignment", created["created"][0])
		self.assertEqual(assignment.docstatus, 1)

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Saudi Shift Assignment",
					"employee": self.employee,
					"shift_type": shift.name,
					"status": "Active",
					"start_date": "2026-06-15",
					"end_date": "2026-07-15",
				}
			).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			create_assignments(shift.name, "2026-07-01", employees=[])

		for log_type, timestamp in (("IN", "2026-06-02 08:15:00"), ("OUT", "2026-06-02 16:30:00")):
			frappe.get_doc(
				{
					"doctype": "Saudi Employee Checkin",
					"employee": self.employee,
					"log_type": log_type,
					"time": timestamp,
					"attendance_location": location.name,
				}
			).insert(ignore_permissions=True)

		daily = frappe.get_doc(
			{
				"doctype": "Saudi Daily Attendance",
				"employee": self.employee,
				"attendance_date": "2026-06-02",
				"status": select_option("Saudi Daily Attendance", "status", "Present"),
				"in_time": "2026-06-02 08:15:00",
				"out_time": "2026-06-02 16:30:00",
				"expected_start_time": "2026-06-02 08:00:00",
				"expected_end_time": "2026-06-02 17:00:00",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(daily.working_hours, 8.25)
		self.assertEqual(daily.late_minutes, 15)
		self.assertEqual(daily.early_exit_minutes, 30)

		invalid_daily = frappe.copy_doc(daily)
		invalid_daily.in_time = "2026-06-02 17:00:00"
		invalid_daily.out_time = "2026-06-02 08:00:00"
		with self.assertRaises(frappe.ValidationError):
			invalid_daily.insert(ignore_permissions=True)

		monthly = frappe.get_doc(
			{
				"doctype": "Monthly Attendance Record",
				"employee": self.employee,
				"company": self.company,
				"month": select_option("Monthly Attendance Record", "month", "June"),
				"year": 2026,
				"attendance_details": [
					{
						"attendance_date": "2026-06-01",
						"day_type": select_option("Monthly Attendance Detail", "day_type", "Working Day"),
						"status": select_option("Monthly Attendance Detail", "status", "Present"),
						"overtime_hours": 2,
					},
					{
						"attendance_date": "2026-06-02",
						"day_type": select_option("Monthly Attendance Detail", "day_type", "Working Day"),
						"status": select_option("Monthly Attendance Detail", "status", "Late"),
						"late_minutes": 15,
					},
					{
						"attendance_date": "2026-06-03",
						"day_type": select_option("Monthly Attendance Detail", "day_type", "Annual Leave"),
						"status": select_option("Monthly Attendance Detail", "status", "Leave"),
					},
				],
			}
		).insert(ignore_permissions=True)
		self.assertEqual(monthly.total_working_days, 2)
		self.assertEqual(monthly.actual_present_days, 2)
		self.assertEqual(monthly.late_days, 1)
		self.assertEqual(monthly.annual_leave_days, 1)
		self.assertEqual(monthly.overtime_hours_total, 2)

		absence = frappe.get_doc(
			{
				"doctype": "Absence Case",
				"employee": self.employee,
				"company": self.company,
				"absence_type": select_option("Absence Case", "absence_type", "Unauthorised"),
				"absence_start_date": "2026-06-10",
				"absence_end_date": "2026-06-12",
				"description": "No approved leave or attendance record",
				"notice_sent": 1,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(absence.absence_days, 3)
		self.assertIn("Notice Sent", absence.status)

	def test_payroll_gosi_wps_and_nitaqat_cycle(self):
		payroll = frappe.get_doc(
			{
				"doctype": "Saudi Monthly Payroll",
				"company": self.company,
				"month": select_option("Saudi Monthly Payroll", "month", "June"),
				"year": 2026,
				"posting_date": "2026-06-30",
				"employees": [
					{
						"employee": self.employee,
						"basic_salary": 8000,
						"housing_allowance": 2000,
						"transport_allowance": 500,
						"overtime_addition": 250,
						"other_deductions": 100,
					}
				],
			}
		).insert(ignore_permissions=True)
		self.assertEqual(payroll.total_gross, 10500)
		self.assertEqual(payroll.total_net_payable, 10650)
		payroll.flags.ignore_permissions = True
		payroll.submit()
		self.assertEqual(payroll.docstatus, 1)

		gosi = frappe.get_doc(
			{
				"doctype": "GOSI Contribution",
				"employee": self.employee,
				"company": self.company,
				"nationality": "Saudi / سعودي",
				"month": select_option("GOSI Contribution", "month", "June"),
				"year": 2026,
				"contribution_base": 50000,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(gosi.contribution_base, 45000)
		self.assertEqual(
			gosi.employee_contribution,
			round(45000 * (gosi.employee_contribution_rate / 100), 2),
		)
		self.assertEqual(
			gosi.employer_contribution,
			round(45000 * (gosi.employer_contribution_rate / 100), 2),
		)

		wps = frappe.get_doc(
			{
				"doctype": "WPS Submission",
				"payroll_document": payroll.name,
				"company": self.company,
				"status": select_option("WPS Submission", "status", "Rejected"),
				"submission_date": "2026-07-01",
				"rejection_date": "2026-07-02",
				"correction_due_date": "2026-07-05",
				"rejection_reason": "One employee bank identifier failed validation",
				"responsible_user": "Administrator",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(wps.corrective_action_log)
		action = frappe.get_doc("HR Compliance Action Log", wps.corrective_action_log)
		self.assertEqual(str(action.due_date), "2026-07-05")

		wps.status = select_option("WPS Submission", "status", "Accepted")
		wps.accepted_on = "2026-07-04"
		wps.save(ignore_permissions=True)
		action.reload()
		self.assertEqual(str(action.completed_on), "2026-07-04")

		invalid_wps = frappe.get_doc(
			{
				"doctype": "WPS Submission",
				"payroll_document": payroll.name,
				"company": self.company,
				"status": select_option("WPS Submission", "status", "Rejected"),
				"submission_date": "2026-07-05",
				"rejection_date": "2026-07-04",
				"correction_due_date": "2026-07-06",
				"rejection_reason": "Invalid date order",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			invalid_wps.insert(ignore_permissions=True)

		nitaqat = frappe.get_doc(
			{
				"doctype": "Nitaqat Record",
				"company": self.company,
				"period_date": "2026-06-30",
				"activity_sector": "Professional services",
				"required_saudization_percentage": 20,
			}
		).insert(ignore_permissions=True)
		self.assertGreaterEqual(nitaqat.total_employees, 1)
		self.assertGreaterEqual(nitaqat.saudi_employees, 1)
		self.assertTrue(nitaqat.nitaqat_category)
		self.assertTrue(nitaqat.compliance_status)

	def test_leave_entitlements_pay_and_overlap_cycle(self):
		annual = frappe.get_doc({"doctype": "Saudi Annual Leave", "employee": self.employee, "company": self.company, "leave_start_date": "2026-08-02", "leave_end_date": "2026-08-06"}).insert(ignore_permissions=True)
		self.assertEqual(annual.total_leave_days, 5)
		self.assertGreaterEqual(annual.leave_balance_before, 21)
		annual.flags.ignore_permissions = True
		annual.flags.ignore_workflow = True
		annual.submit()
		self.assertIn("Approved", annual.status)
		invalid_annual = frappe.get_doc({"doctype": "Saudi Annual Leave", "employee": self.employee, "company": self.company, "leave_start_date": "2026-09-05", "leave_end_date": "2026-09-04"})
		with self.assertRaises(frappe.ValidationError):
			invalid_annual.insert(ignore_permissions=True)
		sick = frappe.get_doc({"doctype": "Saudi Sick Leave", "employee": self.employee, "company": self.company, "from_date": "2026-09-10", "to_date": "2026-10-10", "medical_certificate_attached": 1}).insert(ignore_permissions=True)
		self.assertEqual(sick.total_days, 31)
		self.assertEqual(sick.full_pay_days, 30)
		self.assertEqual(sick.partial_pay_days, 1)
		self.assertGreater(sick.leave_pay_amount, 0)
		overlapping_sick = frappe.get_doc({"doctype": "Saudi Sick Leave", "employee": self.employee, "company": self.company, "from_date": "2026-10-01", "to_date": "2026-10-03"})
		with self.assertRaises(frappe.ValidationError):
			overlapping_sick.insert(ignore_permissions=True)
		disbursement = frappe.get_doc({"doctype": "Annual Leave Disbursement", "employee": self.employee, "company": self.company, "leave_year": 2026, "leave_from_date": "2026-08-02", "leave_to_date": "2026-08-06", "leave_days_to_pay": 5, "disbursement_type": select_option("Annual Leave Disbursement", "disbursement_type", "Full Salary")}).insert(ignore_permissions=True)
		self.assertEqual(disbursement.leave_days_taken, 5)
		self.assertGreater(disbursement.total_leave_pay, 0)
		special = frappe.get_doc({"doctype": "Special Leave", "employee": self.employee, "company": self.company, "leave_type": select_option("Special Leave", "leave_type", "Marriage"), "leave_start_date": "2026-11-01", "leave_end_date": "2026-11-05", "documentation_attached": 1}).insert(ignore_permissions=True)
		self.assertEqual(special.actual_days, 5)
		self.assertTrue(special.is_eligible)
		self.assertGreater(special.total_special_leave_pay, 0)
		parental = frappe.get_doc({"doctype": "Maternity Paternity Leave", "employee": self.employee, "company": self.company, "leave_type": select_option("Maternity Paternity Leave", "leave_type", "Paternity"), "leave_start_date": "2026-12-01", "medical_certificate_attached": 1}).insert(ignore_permissions=True)
		self.assertEqual(parental.entitled_days, 3)
		self.assertEqual(str(parental.leave_end_date), "2026-12-03")
		self.assertGreater(parental.total_leave_pay, 0)

	def test_overtime_flexible_and_working_limits_cycle(self):
		overtime = frappe.get_doc({"doctype": "Overtime Request", "employee": self.employee, "company": self.company, "date": "2026-08-15", "normal_hours": 8, "overtime_hours": 4, "compensation_method": select_option("Overtime Request", "compensation_method", "Compensatory Leave"), "written_consent_reference": "CONSENT-QA-001", "approval_status": select_option("Overtime Request", "approval_status", "Approved")}).insert(ignore_permissions=True)
		self.assertEqual(overtime.compensatory_leave_hours, 6)
		self.assertEqual(overtime.compensatory_leave_days, 0.75)
		self.assertEqual(str(overtime.compensatory_leave_use_by), "2026-10-14")
		overtime.flags.ignore_permissions = True
		overtime.flags.ignore_workflow = True
		overtime.submit()
		self.assertEqual(overtime.docstatus, 1)
		for values in ({"normal_hours": 8, "overtime_hours": 5, "written_consent_reference": "CONSENT"}, {"normal_hours": 8, "overtime_hours": 2, "written_consent_reference": ""}):
			invalid = frappe.get_doc({"doctype": "Overtime Request", "employee": self.employee, "company": self.company, "date": "2026-08-16", "compensation_method": select_option("Overtime Request", "compensation_method", "Compensatory Leave"), **values})
			with self.assertRaises(frappe.ValidationError):
				invalid.insert(ignore_permissions=True)
		flexible = frappe.get_doc({"doctype": "Work Arrangement Control", "employee": self.employee, "company": self.company, "arrangement_type": select_option("Work Arrangement Control", "arrangement_type", "Flexible Work"), "status": select_option("Work Arrangement Control", "status", "Active"), "start_date": "2026-01-01", "end_date": "2026-12-31", "monthly_hours": 120, "platform_reference": "QIWA-QA-001"}).insert(ignore_permissions=True)
		self.assertEqual(flexible.flexible_overtime_hours, 25)
		self.assertEqual(flexible.flexible_nitaqat_credit, 0)
		self.assertFalse(flexible.paid_leave_entitled)
		self.assertFalse(flexible.eosb_entitled)
		self.assertFalse(flexible.probation_applicable)
		excess_flexible = frappe.copy_doc(flexible)
		excess_flexible.monthly_hours = 161
		excess_flexible.insert(ignore_permissions=True)
		self.assertIn("Needs Review", excess_flexible.status)
		temporary = frappe.get_doc({"doctype": "Work Arrangement Control", "employee": self.employee, "company": self.company, "arrangement_type": select_option("Work Arrangement Control", "arrangement_type", "Temporary Work"), "status": select_option("Work Arrangement Control", "status", "Active"), "start_date": "2026-01-01", "end_date": "2026-04-15"}).insert(ignore_permissions=True)
		self.assertTrue(temporary.conversion_required)
		self.assertIn("Needs Conversion", temporary.status)
		working_time = frappe.get_doc({"doctype": "Working Time Compliance Check", "employee": self.employee, "company": self.company, "check_date": "2026-08-17", "actual_daily_hours": 9, "actual_weekly_hours": 52}).insert(ignore_permissions=True)
		self.assertIn("Needs Review", working_time.status)
		working_time.approval_reference = overtime.name
		working_time.save(ignore_permissions=True)
		self.assertIn("Exception Approved", working_time.status)
		working_time.actual_daily_hours = 11
		working_time.save(ignore_permissions=True)
		self.assertIn("Daily Limit Exceeded", working_time.status)

	def test_expat_permit_expiry_cycle(self):
		expat = make_qa_employee(self.company, "expat")
		if frappe.get_meta("Employee").has_field("nationality") and frappe.db.exists("Country", "India"):
			frappe.db.set_value("Employee", expat, "nationality", "India")
		permit = frappe.get_doc(
			{
				"doctype": "Work Permit Iqama",
				"employee": expat,
				"company": self.company,
				"iqama_number": f"2{str(uuid4().int)[:9]}",
				"iqama_expiry_date": add_days(today(), 30),
				"work_permit_expiry_date": add_days(today(), -1),
			}
		).insert(ignore_permissions=True)
		self.assertIn("Expiring Soon", permit.iqama_status)
		self.assertIn("Expired", permit.work_permit_status)
		self.assertEqual(permit.days_to_permit_expiry, -1)
