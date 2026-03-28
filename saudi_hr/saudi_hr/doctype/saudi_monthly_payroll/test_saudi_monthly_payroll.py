from io import BytesIO
from unittest.mock import patch
from types import SimpleNamespace

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate
from openpyxl import Workbook, load_workbook

from saudi_hr.saudi_hr.doctype.saudi_monthly_payroll import saudi_monthly_payroll as payroll_module


class TestSaudiMonthlyPayroll(FrappeTestCase):
	def test_build_employee_row_includes_loan_in_total_deductions(self):
		emp = {"name": "EMP-0001", "employee_name": "Demo Employee", "department": "HR", "nationality": "Saudi"}
		with patch.object(
			payroll_module, "get_employee_salary_components", return_value={
				"basic_salary": 1000,
				"housing_allowance": 200,
				"transport_allowance": 100,
				"other_allowances": 50,
			}
		), patch.object(payroll_module.frappe, "get_all", side_effect=[[], []]), patch.object(
			payroll_module, "get_due_loan_deduction", return_value={"loan_deduction": 125, "installment_names": ["INST-1"]}
		):
			row = payroll_module._build_employee_row(emp, "March / مارس", 2026)

		self.assertEqual(row["gross_salary"], 1350)
		self.assertEqual(row["gosi_employee_deduction"], 100)
		self.assertEqual(row["loan_deduction"], 125)
		self.assertEqual(row["total_deductions"], 225)
		self.assertEqual(row["net_salary"], 1125)
		self.assertEqual(row["loan_installments"], "INST-1")

	def test_recalculate_totals_includes_loan_and_sick_deductions(self):
		doc = frappe.get_doc({
			"doctype": "Saudi Monthly Payroll",
			"company": "amd",
			"month": "March / مارس",
			"year": 2026,
			"posting_date": "2026-03-31",
			"employees": [
				{"employee": "EMP-1", "gross_salary": 1000, "gosi_employee_deduction": 100, "sick_leave_deduction": 20, "loan_deduction": 50, "other_deductions": 30, "overtime_addition": 10, "net_salary": 810},
				{"employee": "EMP-2", "gross_salary": 1200, "gosi_employee_deduction": 120, "sick_leave_deduction": 0, "loan_deduction": 80, "other_deductions": 25, "overtime_addition": 0, "net_salary": 975},
			],
		})

		doc._recalculate_totals()

		self.assertEqual(doc.total_employees, 2)
		self.assertEqual(doc.total_gross, 2200)
		self.assertEqual(doc.total_gosi_deductions, 220)
		self.assertEqual(doc.total_sick_deductions, 20)
		self.assertEqual(doc.total_loan_deductions, 130)
		self.assertEqual(doc.total_other_deductions, 55)
		self.assertEqual(doc.total_overtime, 10)
		self.assertEqual(doc.total_net_payable, 1785)

	def test_extract_source_workbook_rows_maps_expected_headers(self):
		workbook = Workbook()
		worksheet = workbook.active
		worksheet.title = "كشف المصدر"
		worksheet.append([None])
		worksheet.append([None])
		worksheet.append([None])
		worksheet.append(["شركة اختبار"])
		worksheet.append([
			"التسلسل",
			"الرقم الوظيفي",
			"الاسم",
			"الوظيفة",
			"مكان العمل",
			"الإدارة",
			"بنك كاش",
			"الاساسي",
			"بدل السكن",
			"بدل المواصلات",
			"بدلات اخرى",
			"الاجمالي",
			"خصم التأمينات",
			"إضافات",
			"اجمالي الخصم",
			"صافى الراتب",
			"رقم الهوية",
		])
		worksheet.append([1, 2960, "موظف تجريبي", "محاسب", "الرياض", "الإدارة", "بنك", 5000, 1000, 500, 250, 6750, 500, 100, 900, 5950, "2089300780"])

		output = BytesIO()
		workbook.save(output)

		rows = payroll_module._extract_source_workbook_rows(output.getvalue())

		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["employee_id"], 2960)
		self.assertEqual(rows[0]["employee_name"], "موظف تجريبي")
		self.assertEqual(rows[0]["basic_salary"], 5000)
		self.assertEqual(rows[0]["gross_salary"], 6750)
		self.assertEqual(rows[0]["net_salary"], 5950)

	def test_extract_source_workbook_rows_prefers_payroll_print_sheet(self):
		workbook = Workbook()
		worksheet = workbook.active
		worksheet.title = "كشف الرواتب طباعة"
		for _ in range(6):
			worksheet.append([None])
		worksheet.append([
			"التسلسل",
			"الرقم الوظيفي",
			"الاسم",
			"التحويل",
			"مكان العمل",
			"الإدارة",
			"بنك / كاش",
			"الاساسي",
			"بدل السكن",
			"بدل المواصلات",
			"بدلات اخرى",
			"الإضافي",
			"إجمالي البدلات",
			"ايام العمل",
			"ايام الغياب",
			"قيمة ايام الغياب",
			"ساعات التأخير",
			"قيمة التأخير",
			"خصم الجزاءات",
			"خصم التأمينات",
			"خصم السلف والاستقطاعات",
			"اجمالي الخصم",
			"صافى الراتب",
		])
		worksheet.append([
			1,
			2960,
			"موظف تجريبي",
			"شركة",
			"الرياض",
			"الإدارة",
			"بنك",
			5000,
			1000,
			500,
			250,
			100,
			6750,
			30,
			0,
			0,
			0,
			0,
			0,
			500,
			400,
			900,
			5950,
		])

		output = BytesIO()
		workbook.save(output)

		rows = payroll_module._extract_source_workbook_rows(output.getvalue())

		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["employee_id"], 2960)
		self.assertEqual(rows[0]["employee_name"], "موظف تجريبي")
		self.assertEqual(rows[0]["additions"], 100)
		self.assertEqual(rows[0]["gross_salary"], 6750)
		self.assertEqual(rows[0]["gosi_deduction"], 500)
		self.assertEqual(rows[0]["total_deductions"], 900)
		self.assertEqual(rows[0]["net_salary"], 5950)

	def test_map_workbook_rows_to_payroll_preserves_other_deductions(self):
		raw_rows = [{
			"source_row": 6,
			"employee_id": 2960,
			"employee_name": "موظف تجريبي",
			"basic_salary": 5000,
			"housing_allowance": 1000,
			"transport_allowance": 500,
			"other_allowances": 250,
			"gross_salary": 6750,
			"gosi_deduction": 500,
			"additions": 100,
			"total_deductions": 900,
			"net_salary": 5950,
			"national_id": "2089300780",
		}]

		lookup = {
			"2960": {"employee": {"name": "EMP-2960", "employee_name": "موظف تجريبي", "department": "الإدارة", "nationality": "Saudi"}, "matched_by": "employee_id"}
		}

		with patch.object(payroll_module, "_get_company_employee_lookup", return_value=lookup), patch.object(
			payroll_module.frappe.db, "exists", return_value=True
		):
			rows, warnings = payroll_module._map_workbook_rows_to_payroll("amd", raw_rows)

		self.assertEqual(len(rows), 1)
		self.assertEqual(warnings, [])
		self.assertEqual(rows[0]["employee"], "EMP-2960")
		self.assertEqual(rows[0]["gosi_employee_deduction"], 500)
		self.assertEqual(rows[0]["other_deductions"], 400)
		self.assertEqual(rows[0]["total_deductions"], 900)
		self.assertEqual(rows[0]["net_salary"], 5950)
		self.assertEqual(rows[0]["payroll_employee_id"], "2960")
		self.assertEqual(rows[0]["workbook_department"], "")

	def test_map_workbook_rows_to_payroll_keeps_unmatched_workbook_rows(self):
		raw_rows = [{
			"source_row": 8,
			"employee_id": "7803A",
			"employee_name": "MAJID ALI",
			"department": "الإدارة",
			"basic_salary": 750,
			"gross_salary": 750,
			"gosi_deduction": 0,
			"total_deductions": 0,
			"net_salary": 750,
		}]

		with patch.object(payroll_module, "_get_company_employee_lookup", return_value={}), patch.object(
			payroll_module.frappe.db, "exists", return_value=False
		):
			rows, warnings = payroll_module._map_workbook_rows_to_payroll("amd", raw_rows)

		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["employee"], "")
		self.assertEqual(rows[0]["payroll_employee_id"], "7803A")
		self.assertEqual(rows[0]["employee_name"], "MAJID ALI")
		self.assertEqual(rows[0]["workbook_department"], "الإدارة")
		self.assertEqual(rows[0]["department"], "")
		self.assertIn("could not match employee 7803A", warnings[0])
		self.assertIn("without a linked Employee record", warnings[1])

	def test_match_workbook_employee_allows_trailing_letter_suffix(self):
		lookup = {
			"1090": {"employee": {"name": "EMP-1090", "employee_name": "Demo Employee"}, "matched_by": "employee_id"}
		}

		employee, matched_by = payroll_module._match_workbook_employee(
			{"employee_id": "1090A", "employee_name": "Demo Employee"},
			lookup,
		)

		self.assertEqual(employee["name"], "EMP-1090")
		self.assertEqual(matched_by, "employee_id")

	def test_preview_payroll_workbook_summarizes_matching_gap(self):
		with patch.object(payroll_module, "_extract_source_workbook_rows", return_value=[
			{"source_row": 6, "employee_id": 2960, "employee_name": "Missing Employee"}
		]), patch.object(payroll_module, "_get_attached_file_content", return_value=b"xlsx"), patch.object(payroll_module, "_map_workbook_rows_to_payroll", return_value=([{"employee_name": "Missing Employee"}], ["Row 6: could not match employee 2960."])), patch.object(
			payroll_module, "_collect_unmatched_workbook_rows", return_value=[{"source_row": 6, "employee_id": 2960, "employee_name": "Missing Employee"}]
		), patch.object(
			payroll_module.frappe.db, "count", return_value=1
		):
			summary = payroll_module._preview_payroll_workbook("amd", "/private/files/sample.xlsx")

		self.assertEqual(summary["total_rows"], 1)
		self.assertEqual(summary["importable_rows"], 1)
		self.assertEqual(summary["unmatched_rows"], 1)
		self.assertEqual(summary["company_employee_count"], 1)
		self.assertEqual(summary["sample_unmatched"], ["Row 6: could not match employee 2960."])
		self.assertEqual(summary["unmatched_details"][0]["employee_id"], 2960)

	def test_is_empty_source_row_skips_rows_without_employee_identity(self):
		self.assertTrue(payroll_module._is_empty_source_row({
			"employee_id": None,
			"employee_name": None,
			"gross_salary": 1500,
			"net_salary": 1200,
		}))

	def test_resolve_department_link_returns_only_existing_departments(self):
		with patch.object(payroll_module.frappe.db, "exists", side_effect=[True, False]):
			self.assertEqual(payroll_module._resolve_department_link("Finance"), "Finance")
			self.assertEqual(payroll_module._resolve_department_link("Unknown Department"), "")

	def test_build_basic_employee_payload_from_payroll_row_uses_defaults(self):
		row = SimpleNamespace(
			payroll_employee_id="7803A",
			employee_name="MAJID ALI",
			department="",
			workbook_department="Finance",
		)
		defaults = {
			"gender": "Prefer not to say",
			"date_of_birth": getdate("1990-01-01"),
			"date_of_joining": getdate("2026-03-28"),
			"status": "Active",
		}

		with patch.object(payroll_module.frappe, "get_meta", return_value=SimpleNamespace(has_field=lambda field: field in {"middle_name", "last_name", "department"})), patch.object(
			payroll_module.frappe.db, "exists", return_value=True
		):
			payload = payroll_module._build_basic_employee_payload_from_payroll_row("amd", row, defaults)

		self.assertEqual(payload["employee_number"], "7803A")
		self.assertEqual(payload["first_name"], "MAJID")
		self.assertEqual(payload["last_name"], "ALI")
		self.assertEqual(payload["department"], "Finance")
		self.assertEqual(payload["gender"], "Prefer not to say")

	def test_create_basic_employees_for_payroll_creates_and_links_rows(self):
		inserted = []

		class _EmployeeDoc:
			def __init__(self, payload):
				self.payload = payload
				self.flags = SimpleNamespace(ignore_permissions=False)
				self.name = f"EMP-{payload.get('employee_number') or payload['first_name']}"
				self.employee_name = " ".join(filter(None, [payload.get("first_name"), payload.get("middle_name"), payload.get("last_name")])).strip()
				self.department = payload.get("department")
				self.nationality = payload.get("nationality")
				self.employee_number = payload.get("employee_number")

			def insert(self):
				inserted.append(self.payload)
				return self

			def get(self, key):
				return getattr(self, key, self.payload.get(key))

		row_one = SimpleNamespace(idx=1, payroll_employee_id="7803A", employee="", employee_name="MAJID ALI", workbook_department="Finance", department="", nationality="")
		row_two = SimpleNamespace(idx=2, payroll_employee_id="7803A", employee="", employee_name="MAJID ALI", workbook_department="Finance", department="", nationality="")
		doc = SimpleNamespace(company="amd", employees=[row_one, row_two])
		defaults = {
			"gender": "Prefer not to say",
			"date_of_birth": getdate("1990-01-01"),
			"date_of_joining": getdate("2026-03-28"),
			"status": "Active",
		}

		with patch.object(payroll_module, "_get_company_employee_lookup", return_value={}), patch.object(
			payroll_module.frappe, "get_meta", return_value=SimpleNamespace(has_field=lambda field: field in {"middle_name", "last_name", "department"})
		), patch.object(
			payroll_module.frappe, "get_doc", side_effect=lambda payload: _EmployeeDoc(payload)
		), patch.object(
			payroll_module.frappe.db, "exists", side_effect=lambda doctype, name=None: True if doctype == "Department" and name == "Finance" else False
		):
			created, linked, skipped = payroll_module._create_basic_employees_for_payroll(doc, defaults)

		self.assertEqual(created, ["EMP-7803A"])
		self.assertEqual(linked, 1)
		self.assertEqual(skipped, [])
		self.assertEqual(len(inserted), 1)
		self.assertEqual(row_one.employee, "EMP-7803A")
		self.assertEqual(row_two.employee, "EMP-7803A")
		self.assertEqual(row_one.department, "Finance")

	def test_create_basic_employees_for_payroll_keeps_suffix_variants_separate(self):
		inserted = []

		class _EmployeeDoc:
			def __init__(self, payload):
				self.payload = payload
				self.flags = SimpleNamespace(ignore_permissions=False)
				self.name = f"EMP-{payload.get('employee_number') or payload['first_name']}"
				self.employee_name = " ".join(filter(None, [payload.get("first_name"), payload.get("middle_name"), payload.get("last_name")])).strip()
				self.department = payload.get("department")
				self.nationality = payload.get("nationality")
				self.employee_number = payload.get("employee_number")

			def insert(self):
				inserted.append(self.payload)
				return self

			def get(self, key):
				return getattr(self, key, self.payload.get(key))

		row_one = SimpleNamespace(idx=1, payroll_employee_id="7803", employee="", employee_name="MAJID ALI", workbook_department="Finance", department="", nationality="")
		row_two = SimpleNamespace(idx=2, payroll_employee_id="7803A", employee="", employee_name="MAJID ALI", workbook_department="Finance", department="", nationality="")
		doc = SimpleNamespace(company="amd", employees=[row_one, row_two])
		defaults = {
			"gender": "Prefer not to say",
			"date_of_birth": getdate("1990-01-01"),
			"date_of_joining": getdate("2026-03-28"),
			"status": "Active",
		}

		with patch.object(payroll_module, "_get_company_employee_lookup", return_value={}), patch.object(
			payroll_module.frappe, "get_meta", return_value=SimpleNamespace(has_field=lambda field: field in {"middle_name", "last_name", "department"})
		), patch.object(
			payroll_module.frappe, "get_doc", side_effect=lambda payload: _EmployeeDoc(payload)
		), patch.object(
			payroll_module.frappe.db, "exists", side_effect=lambda doctype, name=None: True if doctype == "Department" and name == "Finance" else False
		):
			created, linked, skipped = payroll_module._create_basic_employees_for_payroll(doc, defaults)

		self.assertEqual(created, ["EMP-7803", "EMP-7803A"])
		self.assertEqual(linked, 0)
		self.assertEqual(skipped, [])
		self.assertEqual(len(inserted), 2)
		self.assertEqual(row_one.employee, "EMP-7803")
		self.assertEqual(row_two.employee, "EMP-7803A")

	def test_normalize_basic_employee_creation_defaults_validates_gender_and_dates(self):
		with patch.object(payroll_module.frappe.db, "exists", side_effect=lambda doctype, name=None: True):
			defaults = payroll_module._normalize_basic_employee_creation_defaults(
				"Prefer not to say",
				"1990-01-01",
				"2026-03-28",
				"Active",
			)

		self.assertEqual(defaults["gender"], "Prefer not to say")
		self.assertEqual(str(defaults["date_of_birth"]), "1990-01-01")
		self.assertEqual(str(defaults["date_of_joining"]), "2026-03-28")

	def test_get_payroll_payable_account_prefers_named_non_party_account(self):
		accounts = [
			{"name": "Creditors - A", "account_name": "Creditors", "account_type": "Payable"},
			{"name": "Payroll Payable - A", "account_name": "Payroll Payable", "account_type": ""},
		]

		with patch.object(payroll_module.frappe, "get_all", return_value=accounts):
			account = payroll_module._get_payroll_payable_account("amd")

		self.assertEqual(account, "Payroll Payable - A")

	def test_build_gap_report_rows_formats_unmatched_payload(self):
		rows = payroll_module._build_gap_report_rows([{
			"source_row": 6,
			"employee_id": 2960,
			"employee_name": "Missing Employee",
			"national_id": "2089300780",
			"department": "مدار الفكرة",
			"work_location": "الإدارة العامة",
			"designation": "مندوب مبيعات",
			"gross_salary": 7000,
			"net_salary": 7000,
		}])

		self.assertEqual(rows[0][0], "source_row")
		self.assertEqual(rows[1][1], 2960)
		self.assertEqual(rows[1][2], "Missing Employee")
		self.assertEqual(rows[1][9], "No matching Employee record in selected company")

	def test_employee_lookup_includes_related_saudi_identity_sources(self):
		employees = [{"name": "EMP-1", "employee_name": "Ali", "department": "HR", "employee_number": None}]
		contracts = [{"employee": "EMP-1", "iqama_number": "2089300780", "passport_number": "P123"}]
		permits = [{"employee": "EMP-1", "iqama_number": "2089300780"}]

		with patch.object(payroll_module.frappe, "get_meta", return_value=SimpleNamespace(has_field=lambda field: False)), patch.object(
			payroll_module.frappe, "get_all", side_effect=[employees, contracts, permits]
		), patch.object(payroll_module.frappe.db, "exists", return_value=True):
			lookup = payroll_module._get_company_employee_lookup("amd")

		self.assertEqual(lookup["2089300780"]["employee"]["name"], "EMP-1")
		self.assertIn(lookup["2089300780"]["matched_by"], {"contract_iqama_number", "work_permit_iqama_number"})
		self.assertEqual(lookup["p123"]["employee"]["name"], "EMP-1")

	def test_build_employee_setup_template_prefills_gap_context(self):
		rows = payroll_module._build_employee_setup_template_rows("amd", [{
			"source_row": 6,
			"employee_id": 2960,
			"employee_name": "Missing Employee",
			"national_id": "2089300780",
			"department": "Finance",
			"designation": "Accountant",
		}])

		self.assertEqual(rows[0], payroll_module.EMPLOYEE_SETUP_TEMPLATE_HEADERS)
		self.assertEqual(rows[1][0], 6)
		self.assertEqual(rows[1][1], "2960")
		self.assertEqual(rows[1][4], "amd")
		self.assertEqual(rows[1][7], "2960")
		self.assertEqual(rows[1][8], "Missing")
		self.assertEqual(rows[1][9], "")
		self.assertEqual(rows[1][10], "Employee")
		self.assertEqual(rows[1][14], "Active")

	def test_split_payroll_employee_name_handles_multi_part_names(self):
		first_name, middle_name, last_name = payroll_module._split_payroll_employee_name("  Ahmad\nMohamed   Ali  Salem ")

		self.assertEqual(first_name, "Ahmad")
		self.assertEqual(middle_name, "Mohamed Ali")
		self.assertEqual(last_name, "Salem")

	def test_autofill_employee_setup_names_fills_missing_name_columns(self):
		rows, updated_count = payroll_module._autofill_employee_setup_names([{
			"payroll_employee_name": "Ahmad Mohamed Ali Salem",
			"first_name": "",
			"middle_name": None,
			"last_name": "",
		}])

		self.assertEqual(updated_count, 1)
		self.assertEqual(rows[0]["first_name"], "Ahmad")
		self.assertEqual(rows[0]["middle_name"], "Mohamed Ali")
		self.assertEqual(rows[0]["last_name"], "Salem")

	def test_extract_employee_setup_rows_reads_generated_workbook(self):
		content = payroll_module.make_xlsx([
			payroll_module.EMPLOYEE_SETUP_TEMPLATE_HEADERS,
			[6, "2960", "Missing Employee", "2089300780", "amd", "Finance", "Accountant", "2960", "Ali", "", "", "Male", "1990-01-01", "2024-01-01", "Active", "ok"],
		], "Employee Setup").getvalue()

		rows = payroll_module._extract_employee_setup_rows(content)

		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["employee_number"], "2960")
		self.assertEqual(rows[0]["first_name"], "Ali")

	def test_prepare_employee_setup_row_validates_required_fields(self):
		with patch.object(payroll_module.frappe, "get_meta", return_value=SimpleNamespace(has_field=lambda field: True)), patch.object(
			payroll_module.frappe.db, "exists", return_value=False
		):
			payload = payroll_module._prepare_employee_setup_row("amd", {
				"source_row": 6,
				"employee_number": "2960",
				"payroll_employee_name": "Ali Ahmed Saleh",
				"company": "amd",
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2024-01-01",
				"status": "Active",
				"department": "Finance",
				"designation": "Accountant",
			})

		self.assertEqual(payload["employee_number"], "2960")
		self.assertEqual(payload["first_name"], "Ali")
		self.assertEqual(payload["middle_name"], "Ahmed")
		self.assertEqual(payload["last_name"], "Saleh")
		self.assertEqual(payload["department"], "Finance")

	def test_import_employee_setup_rows_creates_missing_employees_only(self):
		inserted = []

		class _EmployeeDoc:
			def __init__(self, payload):
				self.payload = payload
				self.flags = SimpleNamespace(ignore_permissions=False)
				self.name = f"EMP-{payload['employee_number']}"

			def insert(self):
				inserted.append(self.payload)
				return self

		with patch.object(payroll_module.frappe, "get_meta", return_value=SimpleNamespace(has_field=lambda field: True)), patch.object(
			payroll_module.frappe.db, "exists", side_effect=[False, True]
		), patch.object(payroll_module.frappe, "get_doc", side_effect=lambda payload: _EmployeeDoc(payload)):
			created, skipped = payroll_module._import_employee_setup_rows("amd", [
				{
					"source_row": 6,
					"employee_number": "2960",
					"company": "amd",
					"first_name": "Ali",
					"gender": "Male",
					"date_of_birth": "1990-01-01",
					"date_of_joining": "2024-01-01",
					"status": "Active",
				},
				{
					"source_row": 7,
					"employee_number": "2961",
					"company": "amd",
					"first_name": "Omar",
					"gender": "Male",
					"date_of_birth": "1991-01-01",
					"date_of_joining": "2024-01-01",
					"status": "Active",
				},
			])

		self.assertEqual(created, ["EMP-2960"])
		self.assertEqual(len(inserted), 1)
		self.assertEqual(len(skipped), 1)