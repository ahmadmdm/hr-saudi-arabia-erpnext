# Copyright (c) 2026, IdeaOrbit and Contributors
# See license.txt

from frappe.tests.utils import FrappeTestCase

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from saudi_hr.saudi_hr.compliance_controls import (
	calculate_compensatory_leave_exit_payout,
	calculate_final_settlement_dates,
	create_final_settlement_from_termination,
	derive_termination_initiator,
	get_final_settlement_days,
)


class TestFinalSettlementSLA(FrappeTestCase):
	def test_employer_initiated_settlement_is_due_in_seven_days(self):
		self.assertEqual(get_final_settlement_days("Employer / صاحب العمل"), 7)

	def test_employee_initiated_settlement_is_due_in_fourteen_days(self):
		self.assertEqual(get_final_settlement_days("Employee / الموظف"), 14)

	def test_termination_reason_is_classified(self):
		self.assertEqual(
			derive_termination_initiator("Resignation by Employee / استقالة الموظف (م.75)"),
			"Employee / الموظف",
		)

	def test_employee_initiated_document_return_uses_same_fourteen_day_period(self):
		doc = SimpleNamespace(
			termination_initiated_by="Employee / الموظف",
			last_working_day="2026-07-01",
			settlement_due_date=None,
			document_return_due_date=None,
			unused_compensatory_leave_hours=0,
			actual_hourly_wage_for_leave=0,
			compensatory_leave_payout_evidence=None,
			legal_review_required=0,
			status="Open / مفتوح",
		)
		calculate_final_settlement_dates(doc)
		self.assertEqual(str(doc.settlement_due_date), "2026-07-15")
		self.assertEqual(str(doc.document_return_due_date), "2026-07-15")

	def test_unused_compensatory_leave_is_paid_at_actual_hourly_wage(self):
		self.assertEqual(calculate_compensatory_leave_exit_payout(6, 31.25), 187.5)

	@patch("saudi_hr.saudi_hr.compliance_controls.frappe.get_doc")
	@patch("saudi_hr.saudi_hr.compliance_controls.frappe.db.exists", side_effect=[True, False])
	def test_employee_termination_creates_matching_fourteen_day_deadlines(self, _exists, get_doc):
		get_doc.return_value.insert = MagicMock()
		termination = SimpleNamespace(
			doctype="Termination Notice",
			name="TERM-DEMO-001",
			employee="EMP-DEMO-001",
			company="Demo Company",
			notice_end_date="2026-07-01",
			termination_reason="Resignation by Employee / استقالة الموظف",
		)

		create_final_settlement_from_termination(termination)

		payload = get_doc.call_args.args[0]
		self.assertEqual(str(payload["settlement_due_date"]), "2026-07-15")
		self.assertEqual(str(payload["document_return_due_date"]), "2026-07-15")
		self.assertEqual(payload["legal_review_required"], 0)
