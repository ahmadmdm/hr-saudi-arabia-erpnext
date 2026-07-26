import unittest
from unittest.mock import patch

from saudi_hr.saudi_hr.compliance_command_center import (
	_count,
	calculate_compliance_health,
	get_compliance_command_center,
)
from saudi_hr.saudi_hr.legal_rule_catalog import LEGAL_RULES


class TestComplianceCommandCenter(unittest.TestCase):
	def test_health_is_one_hundred_without_open_risks(self):
		self.assertEqual(calculate_compliance_health(), 100)

	def test_overdue_settlements_have_high_weight(self):
		self.assertEqual(calculate_compliance_health(overdue_settlements=2), 84)

	def test_health_never_drops_below_zero(self):
		self.assertEqual(calculate_compliance_health(100, 100, 100, 100), 0)

	@patch("saudi_hr.saudi_hr.compliance_command_center.frappe.get_list", return_value=[{"name": "A"}, {"name": "B"}])
	@patch("saudi_hr.saudi_hr.compliance_command_center._can_read", return_value=True)
	def test_permission_filtered_count_uses_cross_version_query(self, _can_read, get_list):
		self.assertEqual(_count("Saudi Regulatory Task", {"status": "Open / مفتوح"}), 2)
		self.assertEqual(get_list.call_args.kwargs["fields"], ["name"])
		self.assertEqual(get_list.call_args.kwargs["limit_page_length"], 0)

	@patch("saudi_hr.saudi_hr.compliance_command_center.frappe.throw", side_effect=PermissionError)
	@patch("saudi_hr.saudi_hr.compliance_command_center.frappe.get_roles", return_value=["Employee"])
	def test_command_center_rejects_non_hr_roles(self, _roles, _throw):
		with self.assertRaises(PermissionError):
			get_compliance_command_center()

	@patch("saudi_hr.saudi_hr.compliance_command_center._settlement_actions", return_value=[])
	@patch(
		"saudi_hr.saudi_hr.compliance_command_center._task_actions",
		return_value=[{"severity": "critical", "due_date": "2026-07-01", "title": "Demo"}],
	)
	@patch("saudi_hr.saudi_hr.compliance_command_center._count", side_effect=[9, 4, 2, 1, 1, 3, 2])
	@patch("saudi_hr.saudi_hr.compliance_command_center.frappe.get_roles", return_value=["HR Manager"])
	def test_command_center_returns_permission_aware_operating_snapshot(self, _roles, _count, _tasks, _settlements):
		result = get_compliance_command_center()

		self.assertEqual(result["metrics"]["legal_rules"], len(LEGAL_RULES))
		self.assertEqual(result["metrics"]["open_tasks"], 9)
		self.assertEqual(result["metrics"]["overdue_tasks"], 4)
		self.assertEqual(result["metrics"]["health_score"], 74)
		self.assertEqual(result["actions"][0]["title"], "Demo")
		self.assertEqual(len(result["journeys"]), 4)
		self.assertTrue(result["catalog_version"])
