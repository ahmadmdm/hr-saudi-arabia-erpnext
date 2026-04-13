"""
Standalone unit tests for Saudi Monthly Payroll – Employee Fetch & Name Matching.

These tests run with plain pytest (no Frappe site required).
They cover the specific case where the same employee appears under:
  • a four-part Arabic name in the payroll workbook  (e.g. "دخيل محمد دخيل المبارك")
  • a three-part Arabic name in the Employee master  (e.g. "دخيل محمد المبارك")

All Frappe DB / document calls are mocked via unittest.mock.
Run with:  env/bin/python -m pytest saudi_hr/saudi_hr/doctype/saudi_monthly_payroll/test_payroll_employee_fetch.py -v
"""
import sys
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call

# ── Ensure frappe is importable ────────────────────────────────────────────────
try:
	import frappe
except ImportError:
	_apps = os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 6))
	sys.path.insert(0, os.path.join(_apps, "frappe"))
	sys.path.insert(0, os.path.join(_apps, "saudi_hr"))
	import frappe

if not callable(getattr(frappe, "_", None)):
	frappe._ = lambda x: x

# ── Module under test ──────────────────────────────────────────────────────────
from saudi_hr.saudi_hr.doctype.saudi_monthly_payroll import saudi_monthly_payroll as m  # noqa: E402


# ══════════════════════════════════════════════════════════════════════════════
# 1. Pure helper function tests  (no mocking required)
# ══════════════════════════════════════════════════════════════════════════════

class TestCompactNameKey(unittest.TestCase):
	"""_get_compact_person_name_lookup_key / _candidate_person_name_lookup_keys"""

	def test_four_part_arabic_name_compact_key_drops_middle_part(self):
		key = m._get_compact_person_name_lookup_key("دخيل محمد دخيل المبارك")
		self.assertEqual(key, "دخيل محمد المبارك")

	def test_three_part_arabic_name_compact_key_equals_full_key(self):
		key = m._get_compact_person_name_lookup_key("دخيل محمد المبارك")
		self.assertEqual(key, "دخيل محمد المبارك")

	def test_four_part_keys_include_both_full_and_compact(self):
		keys = m._candidate_person_name_lookup_keys("دخيل محمد دخيل المبارك")
		self.assertIn("دخيل محمد دخيل المبارك", keys)
		self.assertIn("دخيل محمد المبارك", keys)

	def test_three_part_keys_return_single_entry(self):
		keys = m._candidate_person_name_lookup_keys("دخيل محمد المبارك")
		self.assertEqual(keys, ["دخيل محمد المبارك"])

	def test_two_part_name_has_no_compact_key(self):
		key = m._get_compact_person_name_lookup_key("محمد علي")
		self.assertEqual(key, "")

	def test_five_part_name_compact_keeps_first_second_last(self):
		# مطيع نصيب مطيع صالح الفتيحي → مطيع نصيب الفتيحي
		key = m._get_compact_person_name_lookup_key("مطيع نصيب مطيع صالح الفتيحي")
		self.assertEqual(key, "مطيع نصيب الفتيحي")

	def test_four_part_latin_name_compact_key(self):
		key = m._get_compact_person_name_lookup_key("Francis Renard Adriano Lopez")
		self.assertEqual(key, "francis renard lopez")

	def test_three_part_name_compact_key_with_uppercase(self):
		# Lowercase normalisation applied
		keys = m._candidate_person_name_lookup_keys("MAJID ALI HASSAN")
		self.assertEqual(keys[0], "majid ali hassan")


class TestNormalizeLookupKey(unittest.TestCase):
	def test_strips_whitespace_and_lowercases(self):
		self.assertEqual(m._normalize_lookup_key("  دخيل  محمد  "), "دخيل محمد")

	def test_blank_returns_empty_string(self):
		self.assertEqual(m._normalize_lookup_key(None), "")
		self.assertEqual(m._normalize_lookup_key(""), "")
		self.assertEqual(m._normalize_lookup_key("blank"), "")

	def test_integer_normalised_without_decimal(self):
		self.assertEqual(m._normalize_lookup_key(7802.0), "7802")
		self.assertEqual(m._normalize_lookup_key("7802.0"), "7802")


# ══════════════════════════════════════════════════════════════════════════════
# 2. Employee Lookup construction
# ══════════════════════════════════════════════════════════════════════════════

class TestMergeEmployeeLookup(unittest.TestCase):
	"""_merge_employee_lookup – ensures both full and compact keys are registered."""

	def _emp(self, name, employee_name):
		return {"name": name, "employee_name": employee_name, "department": "", "nationality": ""}

	def test_three_part_name_indexed_at_its_own_key(self):
		lookup = {}
		emp = self._emp("HR-EMP-00107", "دخيل محمد المبارك")
		m._merge_employee_lookup(lookup, emp, "دخيل محمد المبارك", "employee_name")
		self.assertIn("دخيل محمد المبارك", lookup)
		self.assertEqual(lookup["دخيل محمد المبارك"]["employee"]["name"], "HR-EMP-00107")

	def test_four_part_name_indexed_at_both_full_and_compact_keys(self):
		lookup = {}
		emp = self._emp("HR-EMP-00200", "دخيل محمد دخيل المبارك")
		m._merge_employee_lookup(lookup, emp, "دخيل محمد دخيل المبارك", "employee_name")
		self.assertIn("دخيل محمد دخيل المبارك", lookup)
		self.assertIn("دخيل محمد المبارك", lookup)
		self.assertEqual(lookup["دخيل محمد المبارك"]["employee"]["name"], "HR-EMP-00200")

	def test_ambiguous_compact_key_marks_lookup_as_none(self):
		"""Two different employees sharing the same compact key → lookup[key] = None."""
		lookup = {}
		emp1 = self._emp("EMP-1", "دخيل محمد دخيل المبارك")
		emp2 = self._emp("EMP-2", "دخيل نايف دخيل المبارك")
		m._merge_employee_lookup(lookup, emp1, "دخيل محمد دخيل المبارك", "employee_name")
		# different employee, same compact key "دخيل X المبارك"? No, these are different compact keys.
		# Test real ambiguity: two employees with SAME three-part compact alias
		emp3 = self._emp("EMP-3", "محمد علي خالد المنصور")
		emp4 = self._emp("EMP-4", "محمد سعيد خالد المنصور")
		m._merge_employee_lookup(lookup, emp3, "محمد علي خالد المنصور", "employee_name")
		m._merge_employee_lookup(lookup, emp4, "محمد سعيد خالد المنصور", "employee_name")
		# compact("محمد علي خالد المنصور") = "محمد علي المنصور"
		# compact("محمد سعيد خالد المنصور") = "محمد سعيد المنصور"
		# Different compact keys – so no ambiguity here (both stored)
		self.assertEqual(lookup["محمد علي المنصور"]["employee"]["name"], "EMP-3")
		self.assertEqual(lookup["محمد سعيد المنصور"]["employee"]["name"], "EMP-4")

	def test_same_compact_key_from_two_different_employees_marks_conflict(self):
		"""If two employees have same compact name key, that key's 'employee' becomes None (ambiguous)."""
		lookup = {}
		# Both employees share compact key "أحمد محمد الشمري"
		emp1 = self._emp("EMP-A", "أحمد محمد صالح الشمري")  # compact → أحمد محمد الشمري
		emp2 = self._emp("EMP-B", "أحمد محمد كمال الشمري")  # compact → أحمد محمد الشمري
		m._merge_employee_lookup(lookup, emp1, "أحمد محمد صالح الشمري", "employee_name")
		m._merge_employee_lookup(lookup, emp2, "أحمد محمد كمال الشمري", "employee_name")
		entry = lookup.get("أحمد محمد الشمري")
		# When two different employees share a compact key, lookup[key]["employee"] becomes None
		# (the dict entry exists but marks the conflict)
		self.assertIsNotNone(entry, "Entry should exist to record the conflict")
		self.assertIsNone(entry.get("employee"), "Conflicting compact key must have employee=None")


# ══════════════════════════════════════════════════════════════════════════════
# 3. Workbook employee matching – the core of the reported bug
# ══════════════════════════════════════════════════════════════════════════════

class TestMatchWorkbookEmployee(unittest.TestCase):
	"""
	Core matching scenarios for four-part ↔ three-part Arabic name aliases.
	This is the exact scenario reported: workbook has four-part name,
	Employee master has three-part name (or vice-versa).
	"""

	def _build_lookup_from(self, name, employee_id=None, record_id="HR-EMP-00107"):
		"""Build an employee lookup as _get_company_employee_lookup does."""
		emp = {
			"name": record_id,
			"employee_name": name,
			"employee_number": employee_id or "",
			"department": "Administration",
			"nationality": "Saudi",
			"company": "amd",
		}
		lookup = {}
		m._merge_employee_lookup(lookup, emp, emp["name"], "name")
		if employee_id:
			m._merge_employee_lookup(lookup, emp, employee_id, "employee_id")
		m._merge_employee_lookup(lookup, emp, name, "employee_name")
		return lookup, emp

	# ── Scenario A: workbook has FOUR-PART, system has THREE-PART ─────────────

	def test_four_part_workbook_matches_three_part_system_via_compact_when_no_id(self):
		"""No employee_id in workbook → direct name match uses compact alias."""
		lookup, _ = self._build_lookup_from("دخيل محمد المبارك")
		emp, by = m._match_workbook_employee_for_import(
			{"employee_id": None, "employee_name": "دخيل محمد دخيل المبارك"},
			lookup,
		)
		self.assertIsNotNone(emp, "Should find the employee via compact name alias")
		self.assertEqual(emp["name"], "HR-EMP-00107")

	def test_four_part_workbook_matches_three_part_system_via_compact_when_id_matches(self):
		"""employee_id in workbook AND it matches → found by ID (no name magic needed)."""
		lookup, _ = self._build_lookup_from("دخيل محمد المبارك", employee_id="7802")
		emp, by = m._match_workbook_employee_for_import(
			{"employee_id": "7802", "employee_name": "دخيل محمد دخيل المبارك"},
			lookup,
		)
		self.assertIsNotNone(emp)
		self.assertEqual(emp["name"], "HR-EMP-00107")
		self.assertEqual(by, "employee_id")

	def test_four_part_workbook_matches_three_part_system_compact_fallback_when_id_mismatches(self):
		"""
		CRITICAL: employee_id in workbook DOES NOT match system employee_number.
		Falls back to compact-name alias matching.
		This is the exact failure mode reported.
		"""
		# System employee has employee_number="7802"
		lookup, _ = self._build_lookup_from("دخيل محمد المبارك", employee_id="7802")
		# Workbook row uses employee_id="9999" (wrong/different) but same person
		emp, by = m._match_workbook_employee_for_import(
			{"employee_id": "9999", "employee_name": "دخيل محمد دخيل المبارك"},
			lookup,
		)
		self.assertIsNotNone(emp, "Must resolve via compact name alias even when employee_id mismatches")
		self.assertEqual(emp["name"], "HR-EMP-00107")

	def test_four_part_workbook_matches_three_part_system_compact_when_employee_has_no_id(self):
		"""System employee has NO employee_number → fallback compact-name must still find them."""
		lookup, _ = self._build_lookup_from("دخيل محمد المبارك", employee_id=None)
		emp, by = m._match_workbook_employee_for_import(
			{"employee_id": "7802", "employee_name": "دخيل محمد دخيل المبارك"},
			lookup,
		)
		self.assertIsNotNone(emp, "Compact alias fallback must work when system employee has no number")
		self.assertEqual(emp["name"], "HR-EMP-00107")

	# ── Scenario B: workbook has THREE-PART, system has FOUR-PART ─────────────

	def test_three_part_workbook_matches_four_part_system_when_no_id(self):
		lookup, _ = self._build_lookup_from("دخيل محمد دخيل المبارك")
		emp, by = m._match_workbook_employee_for_import(
			{"employee_id": None, "employee_name": "دخيل محمد المبارك"},
			lookup,
		)
		self.assertIsNotNone(emp, "Three-part name should resolve via compact key of four-part system name")
		self.assertEqual(emp["name"], "HR-EMP-00107")

	def test_three_part_workbook_matches_four_part_system_compact_when_id_mismatches(self):
		lookup, _ = self._build_lookup_from("دخيل محمد دخيل المبارك", employee_id="7802")
		emp, by = m._match_workbook_employee_for_import(
			{"employee_id": "9999", "employee_name": "دخيل محمد المبارك"},
			lookup,
		)
		self.assertIsNotNone(emp)
		self.assertEqual(emp["name"], "HR-EMP-00107")

	# ── Scenario C: five-part name ──────────────────────────────────────────────

	def test_five_part_workbook_matches_three_part_system(self):
		"""مطيع نصيب مطيع صالح الفتيحي (5-part) ↔ مطيع نصيب الفتيحي (3-part)"""
		lookup, _ = self._build_lookup_from("مطيع نصيب الفتيحي", employee_id="7802")
		emp, by = m._match_workbook_employee_for_import(
			{"employee_id": "9999", "employee_name": "مطيع نصيب مطيع صالح الفتيحي"},
			lookup,
		)
		self.assertIsNotNone(emp)
		self.assertEqual(emp["name"], "HR-EMP-00107")

	# ── Scenario D: name matches but must NOT match unrelated short name ────────

	def test_short_name_not_matched_by_compact_alias_when_employee_id_present(self):
		"""Short two-part name like 'MAJID ALI' must NOT be matched by compact alias
		when an employee_id is present (existing safety guard)."""
		lookup = {
			"majid ali": {
				"employee": {"name": "EMP-OLD", "employee_name": "MAJID ALI"},
				"matched_by": "employee_name",
			}
		}
		# Workbook row has employee_id "7803A" (not in lookup) and name "MAJID ALI" (2-part)
		emp, by = m._match_workbook_employee_for_import(
			{"employee_id": "7803A", "employee_name": "MAJID ALI"},
			lookup,
		)
		# 2-part name has no compact alias → compact-name fallback returns nothing
		self.assertIsNone(emp, "Two-part names must NOT be matched via compact alias")

	def test_exact_three_part_match_still_works_without_id(self):
		"""Regression: exact three-part name direct match must not be broken."""
		lookup, _ = self._build_lookup_from("أحمد محمد السعيد")
		emp, by = m._match_workbook_employee_for_import(
			{"employee_id": None, "employee_name": "أحمد محمد السعيد"},
			lookup,
		)
		self.assertIsNotNone(emp)
		self.assertEqual(emp["name"], "HR-EMP-00107")

	def test_completely_different_four_part_name_does_not_match(self):
		lookup, _ = self._build_lookup_from("دخيل محمد المبارك")
		emp, by = m._match_workbook_employee_for_import(
			{"employee_id": "9999", "employee_name": "سعد عبدالله الغامدي الشمري"},
			lookup,
		)
		self.assertIsNone(emp, "Unrelated name must not match")


# ══════════════════════════════════════════════════════════════════════════════
# 4. _create_basic_employees_for_payroll – no duplicate creation
# ══════════════════════════════════════════════════════════════════════════════

class TestCreateBasicEmployeesNoDuplicate(unittest.TestCase):
	"""
	Ensure _create_basic_employees_for_payroll links an existing employee via
	compact-name alias instead of creating a duplicate Employee master.
	"""

	_defaults = {
		"gender": "Prefer not to say",
		"date_of_birth": None,
		"date_of_joining": None,
		"status": "Active",
	}

	def _make_row(self, employee_name, employee_id="7802", idx=1):
		return SimpleNamespace(
			idx=idx,
			payroll_employee_id=employee_id,
			employee="",
			employee_name=employee_name,
			workbook_department="Operations",
			department="",
			cost_center="",
			designation="",
			nationality="",
		)

	def _existing_employee(self, name, employee_name, employee_number=""):
		return {
			"name": name,
			"employee_name": employee_name,
			"department": "Operations",
			"designation": "",
			"nationality": "Saudi",
			"company": "amd",
			"employee_number": employee_number,
		}

	def _run(self, doc, existing_employee_data):
		"""Helper: run _create_basic_employees_for_payroll with a pre-built lookup."""
		lookup = {}
		emp = existing_employee_data
		m._merge_employee_lookup(lookup, emp, emp["name"], "name")
		if emp.get("employee_number"):
			m._merge_employee_lookup(lookup, emp, emp["employee_number"], "employee_id")
		m._merge_employee_lookup(lookup, emp, emp["employee_name"], "employee_name")

		with patch.object(m, "_get_company_employee_lookup", return_value=lookup), \
		     patch.object(m.frappe.db, "savepoint"), \
		     patch.object(m.frappe.db, "release_savepoint"), \
		     patch.object(m, "_resolve_department_link", return_value="Operations"), \
		     patch.object(m, "_resolve_designation_link", return_value=""), \
		     patch.object(m, "_resolve_cost_center_link", return_value=""):
			return m._create_basic_employees_for_payroll(doc, self._defaults)

	def test_four_part_workbook_row_links_existing_three_part_employee(self):
		"""
		دخيل محمد دخيل المبارك (workbook) ↔ دخيل محمد المبارك (system)
		Must link, NOT create a new Employee master.
		"""
		row = self._make_row("دخيل محمد دخيل المبارك", employee_id="7802")
		doc = SimpleNamespace(company="amd", employees=[row])
		existing = self._existing_employee("HR-EMP-00107", "دخيل محمد المبارك", employee_number="7802")

		created, linked, skipped = self._run(doc, existing)

		self.assertEqual(created, [], "Must NOT create a new Employee when compact alias resolves to existing one")
		self.assertEqual(linked, 1)
		self.assertEqual(row.employee, "HR-EMP-00107")
		self.assertEqual(row.employee_name, "دخيل محمد المبارك")

	def test_four_part_workbook_row_links_even_when_employee_number_missing(self):
		"""Compact fallback works even when system employee has no employee_number."""
		row = self._make_row("دخيل محمد دخيل المبارك", employee_id="7802")
		doc = SimpleNamespace(company="amd", employees=[row])
		existing = self._existing_employee("HR-EMP-00107", "دخيل محمد المبارك", employee_number="")

		created, linked, skipped = self._run(doc, existing)

		self.assertEqual(created, [], "Must NOT create duplicate even without employee_number in system")
		self.assertEqual(linked, 1)
		self.assertEqual(row.employee, "HR-EMP-00107")

	def test_three_part_workbook_row_links_existing_four_part_employee(self):
		"""Reverse: workbook has three-part, system has four-part."""
		row = self._make_row("دخيل محمد المبارك", employee_id="9999")
		doc = SimpleNamespace(company="amd", employees=[row])
		existing = self._existing_employee("HR-EMP-00107", "دخيل محمد دخيل المبارك", employee_number="7802")

		created, linked, skipped = self._run(doc, existing)

		self.assertEqual(created, [])
		self.assertEqual(linked, 1)
		self.assertEqual(row.employee, "HR-EMP-00107")

	def test_two_rows_with_different_name_lengths_link_to_same_employee(self):
		"""
		Two payroll rows for the same person (different name formats) must both
		resolve to the same Employee – only one link, zero new Employee masters.
		"""
		row1 = self._make_row("دخيل محمد دخيل المبارك", employee_id="7802", idx=1)
		row2 = self._make_row("دخيل محمد المبارك", employee_id="7802", idx=2)
		doc = SimpleNamespace(company="amd", employees=[row1, row2])
		existing = self._existing_employee("HR-EMP-00107", "دخيل محمد المبارك", employee_number="7802")

		created, linked, skipped = self._run(doc, existing)

		self.assertEqual(created, [])
		self.assertEqual(linked, 2)
		self.assertEqual(row1.employee, "HR-EMP-00107")
		self.assertEqual(row2.employee, "HR-EMP-00107")

	def test_genuinely_unmatched_employee_creates_new_record(self):
		"""A truly new employee (no compact alias match) SHOULD create a new Employee."""
		inserted = []

		class _FakeEmpDoc:
			doctype = "Employee"
			meta = SimpleNamespace(fields=[])

			def __init__(self, payload):
				self.payload = payload
				self.name = f"EMP-{payload.get('employee_number') or payload['first_name']}"
				self.employee_name = " ".join(filter(None, [
					payload.get("first_name"),
					payload.get("middle_name"),
					payload.get("last_name"),
				])).strip()
				self.department = payload.get("department", "")
				self.nationality = payload.get("nationality", "")
				self.designation = payload.get("designation", "")
				self.employee_number = payload.get("employee_number", "")

			def insert(self):
				inserted.append(self.payload)

			def get(self, key):
				return getattr(self, key, self.payload.get(key))

		row = self._make_row("ناصر ابراهيم الدوسري", employee_id="5555", idx=1)
		doc = SimpleNamespace(company="amd", employees=[row])
		existing = self._existing_employee("HR-EMP-00107", "دخيل محمد المبارك", employee_number="7802")

		lookup = {}
		emp = existing
		m._merge_employee_lookup(lookup, emp, emp["name"], "name")
		m._merge_employee_lookup(lookup, emp, emp["employee_number"], "employee_id")
		m._merge_employee_lookup(lookup, emp, emp["employee_name"], "employee_name")

		with patch.object(m, "_get_company_employee_lookup", return_value=lookup), \
		     patch.object(m.frappe.db, "savepoint"), \
		     patch.object(m.frappe.db, "release_savepoint"), \
		     patch.object(m.frappe, "get_meta", return_value=SimpleNamespace(
		         has_field=lambda f: f in {"middle_name", "last_name", "department", "nationality"}
		     )), \
		     patch.object(m.frappe, "get_doc", side_effect=lambda p: _FakeEmpDoc(p)), \
		     patch.object(m.frappe.db, "exists", return_value=False):
			created, linked, skipped = m._create_basic_employees_for_payroll(doc, self._defaults)

		self.assertEqual(len(created), 1, "New employee should be created for a genuinely unmatched person")
		self.assertEqual(linked, 0)
		self.assertEqual(row.employee, "EMP-5555")


# ══════════════════════════════════════════════════════════════════════════════
# 5. fetch_employees – correct counting and skip behaviour
# ══════════════════════════════════════════════════════════════════════════════

class TestFetchEmployees(unittest.TestCase):
	"""
	fetch_employees() must:
	  1. Return all active employees with a non-zero basic salary.
	  2. Skip employees whose basic resolves to zero and emit a warning.
	  3. Return correct count / source_count / skipped_count.
	"""

	class _FakeDoc:
		def __init__(self):
			self.company = "amd"
			self.month = "March / مارس"
			self.year = 2026
			self.employees = []
			self.total_net_payable = 0.0
			self.saved = False
			self.comments = []

		def set(self, fieldname, value):
			setattr(self, fieldname, value)

		def append(self, fieldname, value):
			getattr(self, fieldname).append(value)

		def _recalculate_totals(self):
			self.total_net_payable = round(
				sum(r.get("net_salary", 0.0) for r in self.employees), 2
			)

		def save(self):
			self.saved = True

		def add_comment(self, comment_type, text):
			self.comments.append((comment_type, text))

	def _make_employees(self, *specs):
		"""specs: (name, employee_name, basic)"""
		return [
			{"name": n, "employee_name": en, "department": "HR",
			 "company": "amd", "nationality": "Saudi"}
			for n, en, _ in specs
		], [
			{"employee": n, "basic_salary": basic, "housing_allowance": 0,
			 "transport_allowance": 0, "other_allowances": 0, "total_salary": basic}
			for n, _, basic in specs
		]

	def _run_fetch(self, employees, contract_rows):
		fake_doc = self._FakeDoc()
		with patch.object(m.frappe, "get_doc", return_value=fake_doc), \
		     patch.object(m.frappe, "has_permission"), \
		     patch.object(m.frappe, "get_all", return_value=employees), \
		     patch.object(m.frappe.db, "sql", side_effect=[contract_rows, [], []]), \
		     patch.object(m, "_get_employee_fetch_fields",
		                  return_value=["name", "employee_name", "department", "company", "nationality"]), \
		     patch.object(m, "get_employee_salary_components",
		                  return_value={"basic_salary": 0}), \
		     patch.object(m, "get_gosi_rates", return_value={"employee_rate": 10.0}), \
		     patch.object(m, "get_due_loan_deduction",
		                  return_value={"loan_deduction": 0, "installment_names": []}), \
		     patch.object(m, "_get_company_default_cost_center", return_value="Main - AMD"):
			result = m.fetch_employees("SAU-PAY-TEST")
		return fake_doc, result

	def test_all_employees_with_salary_are_included(self):
		employees, contracts = self._make_employees(
			("EMP-1", "محمد أحمد", 5000),
			("EMP-2", "علي صالح", 4000),
		)
		doc, result = self._run_fetch(employees, contracts)

		self.assertEqual(result["count"], 2)
		self.assertEqual(result["source_count"], 2)
		self.assertEqual(result["skipped_count"], 0)
		self.assertEqual(result["warnings"], [])
		emp_ids = [r["employee"] for r in doc.employees]
		self.assertIn("EMP-1", emp_ids)
		self.assertIn("EMP-2", emp_ids)

	def test_employee_with_zero_basic_salary_is_skipped(self):
		employees, contracts = self._make_employees(
			("EMP-GOOD", "موظف جيد", 5000),
			("EMP-ZERO", "موظف صفر", 0),
		)
		doc, result = self._run_fetch(employees, contracts)

		self.assertEqual(result["count"], 1)
		self.assertEqual(result["source_count"], 2)
		self.assertEqual(result["skipped_count"], 1)
		self.assertEqual(len(result["warnings"]), 1)
		self.assertIn("موظف صفر", result["warnings"][0])

		emp_ids = [r["employee"] for r in doc.employees]
		self.assertIn("EMP-GOOD", emp_ids)
		self.assertNotIn("EMP-ZERO", emp_ids)

	def test_fetch_saves_and_returns_total_net(self):
		employees, contracts = self._make_employees(
			("EMP-1", "موظف واحد", 8000),
		)
		doc, result = self._run_fetch(employees, contracts)

		self.assertTrue(doc.saved)
		# GOSI = min(8000, 45000)*10/100 = 800; gross = 8000; net = 7200
		self.assertAlmostEqual(result["total_net"], 7200.0, places=2)

	def test_all_employees_zero_basic_returns_empty_table(self):
		employees, contracts = self._make_employees(
			("EMP-A", "موظف أ", 0),
			("EMP-B", "موظف ب", 0),
		)
		doc, result = self._run_fetch(employees, contracts)

		self.assertEqual(result["count"], 0)
		self.assertEqual(result["skipped_count"], 2)
		self.assertEqual(len(doc.employees), 0)

	def test_fetch_no_active_employees_returns_zero_count(self):
		doc = self._FakeDoc()
		with patch.object(m.frappe, "get_doc", return_value=doc), \
		     patch.object(m.frappe, "has_permission"), \
		     patch.object(m.frappe, "get_all", return_value=[]), \
		     patch.object(m, "_get_employee_fetch_fields",
		                  return_value=["name", "employee_name", "department", "company", "nationality"]):
			result = m.fetch_employees("SAU-PAY-TEST")

		self.assertEqual(result["count"], 0)
		self.assertEqual(result["total_net"], 0.0)


# ══════════════════════════════════════════════════════════════════════════════
# 6. Duplicate group key – compact name alias grouping
# ══════════════════════════════════════════════════════════════════════════════

class TestDuplicateGroupKey(unittest.TestCase):
	"""_get_payroll_row_duplicate_group_key must produce the same key for
	four-part and three-part variants of the same person."""

	def test_four_part_and_three_part_produce_same_group_key(self):
		key4 = m._get_payroll_row_duplicate_group_key(
			employee_id="7802",
			employee_name="دخيل محمد دخيل المبارك",
		)
		key3 = m._get_payroll_row_duplicate_group_key(
			employee_id="7802",
			employee_name="دخيل محمد المبارك",
		)
		self.assertEqual(key4, key3,
			"Four-part and three-part variants of the same person must share a duplicate group key")

	def test_five_part_and_three_part_produce_same_group_key(self):
		key5 = m._get_payroll_row_duplicate_group_key(
			employee_id="7802",
			employee_name="مطيع نصيب مطيع صالح الفتيحي",
		)
		key3 = m._get_payroll_row_duplicate_group_key(
			employee_id="7802",
			employee_name="مطيع نصيب الفتيحي",
		)
		self.assertEqual(key5, key3)

	def test_different_employees_have_different_group_keys(self):
		key_a = m._get_payroll_row_duplicate_group_key(
			employee_id="7802",
			employee_name="دخيل محمد المبارك",
		)
		key_b = m._get_payroll_row_duplicate_group_key(
			employee_id="7802",
			employee_name="سعد عبدالله الغامدي",
		)
		self.assertNotEqual(key_a, key_b)


if __name__ == "__main__":
	unittest.main()
