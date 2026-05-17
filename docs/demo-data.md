# Demo Data Guide

Saudi HR includes a small lifecycle demo seeder for development and staging environments.

Do not run this on production unless you explicitly want sample records in the live site.

## Run

```bash
bench --site <your-site-name> execute saudi_hr.saudi_hr.demo_lifecycle.seed_employee_lifecycle_demo
```

## What It Creates

The seeder is idempotent for its demo users and creates or reuses:

| Record | Purpose |
|--------|---------|
| Demo manager user | Approval and reporting relationship |
| Demo employee user | Employee self-service scenario |
| Employee records | Manager and employee hierarchy |
| Saudi Employment Contract | Contract and salary calculation preview |
| Employee Warning Notice | Employee relations scenario |
| Saudi Annual Leave | Leave approval path |
| Saudi Monthly Payroll | Payroll calculation scenario |
| Saudi HR Settings update | Mobile attendance base URL alignment |

## Expected Output

The command returns a dictionary similar to:

```python
{
    "company": "<company>",
    "manager": "<manager employee id>",
    "employee": "<employee id>",
    "contract": "<contract id>",
    "warning": "<warning id>",
    "leave": "<leave id>",
    "payroll": "<payroll id>",
    "seeded_on": "<date>",
    "next_review_date": "<date>"
}
```

## Suggested Review Flow

1. Open `/app/saudi-hr`.
2. Open `/app/professional-hr-hub`.
3. Search for the returned employee id.
4. Review the contract, warning, leave, and payroll records.
5. Open `/app/employee-org-tree` to inspect the manager relationship.
6. Run the relevant reports from the workspace.

