"""
WPS Export Report - نظام حماية الأجور
Generates WPS-compliant CSV for MLSD (Ministry of Human Resources) submission.

MLSD SIF (Salary Information File) Format v2.0
Required monthly submission for businesses with 10+ employees.
"""

import frappe
from frappe import _
from frappe.utils import getdate, formatdate


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": _("Employer ID (رقم صاحب العمل)"),
            "fieldname": "employer_id",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": _("Employee ID / Iqama No (الهوية/الإقامة)"),
            "fieldname": "employee_iqama",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Employee Name"),
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _("IBAN"),
            "fieldname": "iban",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Bank Name"),
            "fieldname": "bank_name",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": _("Payment Date (تاريخ الدفع)"),
            "fieldname": "payment_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": _("Pay Period (فترة الرواتب)"),
            "fieldname": "pay_period",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": _("Net Salary (صافي الراتب)"),
            "fieldname": "net_salary",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Basic Salary"),
            "fieldname": "basic_salary",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": _("Housing Allowance"),
            "fieldname": "housing_allowance",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Nationality"),
            "fieldname": "nationality",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": _("WPS Status"),
            "fieldname": "wps_status",
            "fieldtype": "Data",
            "width": 100,
        },
    ]


def get_data(filters):
    payroll_name = filters.get("payroll_document")
    if not payroll_name:
        frappe.throw(_("Please select a Saudi Monthly Payroll document"))

    payroll = frappe.get_doc("Saudi Monthly Payroll", payroll_name)
    company = payroll.company

    # Get company CR number (used as Employer ID in WPS)
    employer_id = frappe.db.get_value("Company", company, "registration_details") or company

    rows = []
    for emp_row in payroll.employees:
        employee = emp_row.employee

        # Fetch employee details
        emp_data = frappe.db.get_value(
            "Employee",
            employee,
            [
                "employee_name",
                "iban",
                "bank_name",
                "iqama_number",
                "passport_number",
                "nationality",
                "date_of_joining",
            ],
            as_dict=True,
        ) or {}

        # Iqama for non-Saudi, National ID for Saudi
        iqama = emp_data.get("iqama_number") or emp_data.get("passport_number") or employee

        # Net salary = gross - deductions; use emp_row computed values
        basic = emp_row.get("basic_salary") or 0
        housing = emp_row.get("housing_allowance") or 0
        transport = emp_row.get("transport_allowance") or 0
        other = emp_row.get("other_allowances") or 0
        deductions = emp_row.get("total_deductions") or 0
        gross = basic + housing + transport + other
        net = gross - deductions

        pay_period = f"{payroll.month or ''}/{payroll.year or ''}"
        payment_date = payroll.payment_date or payroll.posting_date

        # Validate IBAN - basic check
        iban = emp_data.get("iban") or ""
        wps_status = "Ready" if iban and iqama else "Missing Data"

        rows.append({
            "employer_id": employer_id,
            "employee_iqama": iqama,
            "employee_name": emp_data.get("employee_name") or employee,
            "iban": iban,
            "bank_name": emp_data.get("bank_name") or "",
            "payment_date": payment_date,
            "pay_period": pay_period,
            "net_salary": net,
            "basic_salary": basic,
            "housing_allowance": housing,
            "nationality": emp_data.get("nationality") or "",
            "wps_status": wps_status,
        })

    return rows


@frappe.whitelist()
def download_wps_sif(payroll_document):
    """
    Generate WPS SIF (Salary Information File) as CSV download.
    MLSD format: EDR record + EMP records + EOS record.
    """
    import csv
    import io

    filters = {"payroll_document": payroll_document}
    _, data = execute(filters)

    if not data:
        frappe.throw(_("No employee data found for this payroll document"))

    payroll = frappe.get_doc("Saudi Monthly Payroll", payroll_document)
    company = payroll.company
    employer_id = frappe.db.get_value("Company", company, "registration_details") or company

    output = io.StringIO()
    writer = csv.writer(output)

    # SIF Header (EDR record)
    writer.writerow(["EDR", employer_id, company, f"{payroll.month or '01'}{payroll.year or ''}", len(data)])

    # Employee records (EMP)
    for row in data:
        writer.writerow([
            "EMP",
            row["employee_iqama"],
            row["iban"],
            row["net_salary"],
            row["pay_period"],
            row["payment_date"] or "",
            row["employee_name"],
        ])

    # End of file (EOS)
    writer.writerow(["EOS", len(data), sum(r["net_salary"] for r in data)])

    sif_content = output.getvalue()
    filename = f"WPS_{payroll_document}_{payroll.month}_{payroll.year}.csv"

    frappe.response["filename"] = filename
    frappe.response["filecontent"] = sif_content.encode("utf-8")
    frappe.response["type"] = "download"
