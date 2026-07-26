from frappe.tests.utils import FrappeTestCase

from saudi_hr.saudi_hr.doctype.maternity_paternity_leave.maternity_paternity_leave import (
	LEGACY_MATERNITY_LEAVE_TYPE,
	MATERNITY_LEAVE_TYPE,
	get_entitled_days,
	normalize_leave_type,
)


class TestMaternityPaternityLeave(FrappeTestCase):
	def test_current_maternity_entitlement_is_twelve_weeks(self):
		self.assertEqual(get_entitled_days(MATERNITY_LEAVE_TYPE), 84)

	def test_legacy_maternity_value_is_normalized(self):
		self.assertEqual(normalize_leave_type(LEGACY_MATERNITY_LEAVE_TYPE), MATERNITY_LEAVE_TYPE)
		self.assertEqual(get_entitled_days(LEGACY_MATERNITY_LEAVE_TYPE), 84)

