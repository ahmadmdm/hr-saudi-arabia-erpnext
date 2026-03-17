import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import date_diff, getdate


class AnnualLeaveDisbursement(Document):

    def validate(self):
        self._load_salary_data()
        self._calculate_entitlement()
        self._calculate_pay()

    def on_submit(self):
        # م.109: employee must receive leave pay BEFORE starting leave
        self.status = "Approved / موافق عليه"
        self.db_set("status", self.status)

    # ------------------------------------------------------------------

    def _load_salary_data(self):
        if not self.employee:
            return

        # Basic salary from Salary Structure Assignment
        basic = frappe.db.get_value(
            "Salary Structure Assignment",
            {"employee": self.employee, "docstatus": 1},
            "base",
            order_by="from_date desc",
        ) or 0
        if not self.monthly_basic_salary:
            self.monthly_basic_salary = basic

        # Allowances from Saudi Employment Contract
        contract = frappe.db.get_value(
            "Saudi Employment Contract",
            {"employee": self.employee, "contract_status": "Active / نشط"},
            ["housing_allowance", "transport_allowance"],
            as_dict=True,
            order_by="start_date desc",
        ) or {}

        housing = contract.get("housing_allowance") or 0
        transport = contract.get("transport_allowance") or 0
        self.monthly_gross_salary = (self.monthly_basic_salary or 0) + housing + transport
        self.daily_basic_rate = (self.monthly_basic_salary or 0) / 30

    def _calculate_entitlement(self):
        """م.109: 21 days/year for first 5 years, 30 days/year after"""
        if not self.employee or not self.leave_year:
            return

        # Years of service
        join_date = frappe.db.get_value("Employee", self.employee, "date_of_joining")
        if not join_date:
            return

        years_service = (getdate(f"{self.leave_year}-12-31") - getdate(join_date)).days / 365.25
        entitled = 30 if years_service > 5 else 21
        self.leave_days_entitled = entitled

        # Days already taken this year from Leave Applications
        taken = frappe.db.sql("""
            SELECT COALESCE(SUM(total_leave_days), 0)
            FROM `tabLeave Application`
            WHERE employee=%s AND leave_type='Annual Leave'
            AND YEAR(from_date)=%s AND docstatus=1
        """, (self.employee, self.leave_year))[0][0] or 0
        self.leave_days_taken = taken
        self.leave_days_balance = entitled - taken

        if not self.leave_days_to_pay:
            # Default to leave period duration
            if self.leave_from_date and self.leave_to_date:
                self.leave_days_to_pay = date_diff(self.leave_to_date, self.leave_from_date) + 1

    def _calculate_pay(self):
        if not self.daily_basic_rate or not self.leave_days_to_pay:
            return

        days = self.leave_days_to_pay
        basic_pay = self.daily_basic_rate * days
        self.basic_leave_pay = basic_pay

        if self.disbursement_type and "Full" in self.disbursement_type:
            # Pro-rate housing and transport too
            contract = frappe.db.get_value(
                "Saudi Employment Contract",
                {"employee": self.employee, "contract_status": "Active / نشط"},
                ["housing_allowance", "transport_allowance"],
                as_dict=True,
                order_by="start_date desc",
            ) or {}
            housing_daily = (contract.get("housing_allowance") or 0) / 30
            transport_daily = (contract.get("transport_allowance") or 0) / 30
            self.housing_allowance_pay = housing_daily * days
            self.transport_allowance_pay = transport_daily * days
        else:
            self.housing_allowance_pay = 0
            self.transport_allowance_pay = 0

        ticket = self.ticket_amount if self.ticket_entitled else 0
        self.total_leave_pay = (
            (self.basic_leave_pay or 0)
            + (self.housing_allowance_pay or 0)
            + (self.transport_allowance_pay or 0)
            + ticket
        )


@frappe.whitelist()
def get_leave_balance(employee, leave_year):
    """Return leave entitlement, taken and balance for UI"""
    join_date = frappe.db.get_value("Employee", employee, "date_of_joining")
    if not join_date:
        return {}

    years_service = (getdate(f"{leave_year}-12-31") - getdate(join_date)).days / 365.25
    entitled = 30 if years_service > 5 else 21

    taken = frappe.db.sql("""
        SELECT COALESCE(SUM(total_leave_days), 0)
        FROM `tabLeave Application`
        WHERE employee=%s AND leave_type='Annual Leave'
        AND YEAR(from_date)=%s AND docstatus=1
    """, (employee, leave_year))[0][0] or 0

    return {
        "entitled": entitled,
        "taken": taken,
        "balance": entitled - taken,
        "years_service": round(years_service, 1),
    }
