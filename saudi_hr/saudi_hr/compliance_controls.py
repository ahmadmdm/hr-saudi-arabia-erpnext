import json

import frappe
from frappe import _
from frappe.utils import add_days, add_months, cint, date_diff, flt, getdate, today

from saudi_hr.saudi_hr.utils import get_employee_nationality, is_saudi_nationality


HR_PERMISSIONS = [
	{
		"role": "HR Manager",
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"print": 1,
		"email": 1,
		"report": 1,
		"export": 1,
		"share": 1,
	},
	{
		"role": "HR User",
		"read": 1,
		"write": 1,
		"create": 1,
		"print": 1,
		"email": 1,
		"report": 1,
		"export": 1,
	},
	{
		"role": "System Manager",
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"print": 1,
		"email": 1,
		"report": 1,
		"export": 1,
		"share": 1,
	},
]


READ_ONLY_PERMISSIONS = [
	{"role": "HR Manager", "read": 1, "report": 1, "export": 1, "print": 1},
	{"role": "HR User", "read": 1, "report": 1, "export": 1, "print": 1},
	{"role": "System Manager", "read": 1, "report": 1, "export": 1, "print": 1},
]


PERMISSION_FLAGS = [
	"read",
	"write",
	"create",
	"delete",
	"submit",
	"cancel",
	"amend",
	"report",
	"export",
	"import",
	"share",
	"print",
	"email",
	"if_owner",
	"select",
]


OPEN_STATUSES = {
	"Draft / مسودة",
	"Open / مفتوح",
	"In Progress / قيد التنفيذ",
	"Under Review / قيد المراجعة",
	"Pending Submission / بانتظار الرفع",
	"Submitted / مرسل",
	"Rejected / مرفوض",
	"Corrective Action Required / يحتاج تصحيح",
	"Pending / معلق",
	"Overdue / متأخر",
}


def field(fieldname, fieldtype, label=None, **kwargs):
	docfield = {"fieldname": fieldname, "fieldtype": fieldtype}
	if label:
		docfield["label"] = label
	docfield.update(kwargs)
	return docfield


def section(fieldname, label, description=None, **kwargs):
	docfield = field(fieldname, "Section Break", label, **kwargs)
	if description:
		docfield["description"] = description
	return docfield


def column(fieldname):
	return field(fieldname, "Column Break")


def make_doctype(name, fields, **kwargs):
	definition = {
		"doctype": "DocType",
		"name": name,
		"module": "Saudi HR",
		"custom": 0,
		"engine": "InnoDB",
		"field_order": [row["fieldname"] for row in fields],
		"fields": fields,
		"permissions": kwargs.pop("permissions", HR_PERMISSIONS),
		"allow_import": kwargs.pop("allow_import", 1),
		"track_changes": kwargs.pop("track_changes", 1),
		"sort_field": kwargs.pop("sort_field", "modified"),
		"sort_order": kwargs.pop("sort_order", "DESC"),
	}
	definition.update(kwargs)
	return definition


def make_child_doctype(name, fields):
	return make_doctype(
		name,
		fields,
		istable=1,
		permissions=[],
		allow_import=0,
		track_changes=0,
		sort_field="idx",
		sort_order="ASC",
	)


COMPLIANCE_DOCTYPES = [
	make_child_doctype(
		"Statutory HR Record Row",
		[
			field("record_type", "Select", "Record Type / نوع السجل", reqd=1, in_list_view=1, options="\nEmployee Names Register / كشف أسماء العمال\nWage Register / كشف الأجور والحسميات\nFine Register / سجل الغرامات\nAttendance Register / سجل الحضور والانصراف\nSaudi Training Register / سجل تدريب السعوديين\nMedical Examination Register / سجل الفحص الطبي\nEmployee File / ملف العامل\nWork Schedule Posting / جدول مواعيد العمل\nOther / أخرى"),
			field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Art.17 / Reg. Art.5"),
			column("column_break_1"),
			field("required", "Check", "Required / إلزامي", default=1),
			field("status", "Select", "Status / الحالة", in_list_view=1, options="Missing / ناقص\nAvailable / متوفر\nNeeds Update / يحتاج تحديث\nNot Applicable / غير منطبق", default="Missing / ناقص"),
			section("ownership_section", "Ownership & Evidence / المسؤولية والإثبات"),
			field("owner_user", "Link", "Owner / المسؤول", options="User"),
			field("last_verified_on", "Date", "Last Verified On / آخر تحقق"),
			field("next_review_date", "Date", "Next Review Date / تاريخ المراجعة القادم"),
			column("column_break_2"),
			field("linked_doctype", "Link", "Linked DocType / نوع المستند المرتبط", options="DocType"),
			field("linked_report", "Data", "Linked Report / التقرير المرتبط"),
			field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
			field("gap_description", "Small Text", "Gap Description / وصف الفجوة"),
			field("action_log", "Link", "Compliance Action / إجراء الامتثال", options="HR Compliance Action Log"),
		],
	),
	make_child_doctype(
		"Disability Accommodation Row",
		[
			field("employee", "Link", "Employee / الموظف", options="Employee", reqd=1, in_list_view=1),
			field("employee_name", "Data", "Employee Name / اسم الموظف", fetch_from="employee.employee_name", read_only=1),
			column("column_break_1"),
			field("certificate_reference", "Data", "Certificate Reference / مرجع شهادة الإعاقة"),
			field("certificate_expiry", "Date", "Certificate Expiry / انتهاء الشهادة"),
			section("accommodation_section", "Accommodation / التسهيلات"),
			field("accommodation_type", "Select", "Accommodation Type / نوع التسهيل", options="\nWorkspace Adjustment / تهيئة مكان العمل\nAssistive Tool / أداة مساعدة\nWorking Hours Adjustment / تعديل ساعات العمل\nJob Duty Adjustment / تعديل مهام الوظيفة\nTransportation Support / دعم النقل\nOther / أخرى"),
			field("accommodation_status", "Select", "Accommodation Status / حالة التسهيل", in_list_view=1, options="Required / مطلوب\nProvided / منفذ\nUnder Review / قيد المراجعة\nNot Required / غير مطلوب", default="Required / مطلوب"),
			field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
			field("notes", "Small Text", "Notes / ملاحظات"),
		],
	),
	make_child_doctype(
		"Safety Risk Control Item",
		[
			field("hazard", "Data", "Hazard / الخطر", reqd=1, in_list_view=1),
			field("severity", "Select", "Severity / الشدة", in_list_view=1, options="\nLow / منخفض\nMedium / متوسط\nHigh / مرتفع\nCritical / حرج", reqd=1),
			column("column_break_1"),
			field("required_control", "Small Text", "Required Control / الإجراء الوقائي المطلوب"),
			field("status", "Select", "Status / الحالة", in_list_view=1, options="Open / مفتوح\nIn Progress / قيد التنفيذ\nControlled / تمت السيطرة\nAccepted Risk / خطر مقبول\nClosed / مغلق", default="Open / مفتوح"),
			field("owner_user", "Link", "Owner / المسؤول", options="User"),
			field("due_date", "Date", "Due Date / تاريخ الاستحقاق"),
			field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
		],
	),
	make_doctype(
		"Work Regulation",
		[
			field("naming_series", "Select", "Naming Series", options="SAU-WR-.YYYY.-.####", reqd=1),
			field("regulation_title", "Data", "Regulation Title / عنوان لائحة تنظيم العمل", reqd=1, in_list_view=1),
			field("company", "Link", "Company / الشركة", options="Company", reqd=1, in_list_view=1),
			column("column_break_1"),
			field("status", "Select", "Status / الحالة", options="Draft / مسودة\nUnder Legal Review / قيد المراجعة القانونية\nApproved / معتمدة\nPublished / منشورة\nArchived / مؤرشفة", default="Draft / مسودة", in_list_view=1),
			field("regulation_type", "Select", "Regulation Type / نوع اللائحة", options="Unified Model / النموذج الموحد\nCustom Regulation / لائحة خاصة\nAmendment / تعديل", default="Unified Model / النموذج الموحد"),
			section("approval_section", "Approval & Publication / الاعتماد والنشر", "Tracks the approved work regulation required by Labor Law Art.12-13 and Executive Regulations Art.3-4."),
			field("version", "Data", "Version / الإصدار", default="1.0", reqd=1),
			field("effective_date", "Date", "Effective Date / تاريخ السريان", reqd=1),
			field("approval_date", "Date", "Approval Date / تاريخ الاعتماد"),
			column("column_break_2"),
			field("next_review_date", "Date", "Next Review Date / تاريخ المراجعة القادم"),
			field("lawyer_or_approver", "Data", "Lawyer or Approver / المحامي أو جهة الاعتماد"),
			field("ministry_certificate_reference", "Data", "Ministry Certificate Reference / مرجع شهادة الوزارة"),
			field("ministry_certificate_attachment", "Attach", "Ministry Certificate / شهادة الاعتماد"),
			section("announcement_section", "Announcement & Acknowledgement / الإعلان والإقرار"),
			field("announcement_date", "Date", "Announcement Date / تاريخ الإعلان"),
			field("published_location", "Small Text", "Published Location / مكان أو وسيلة الإعلان"),
			column("column_break_3"),
			field("acknowledgement_required", "Check", "Acknowledgement Required / يتطلب إقراراً", default=1),
			field("acknowledgement_due_days", "Int", "Acknowledgement Due Days / مهلة الإقرار", default=7),
			field("linked_policy", "Link", "Linked Policy / السياسة المرتبطة", options="HR Policy Document"),
			section("legal_section", "Legal Basis / الأساس النظامي"),
			field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Labor Law Art.12-13; Executive Regulations Art.3-4; Annex 1"),
			field("approved_attachment", "Attach", "Approved Regulation / اللائحة المعتمدة"),
			field("notes", "Text Editor", "Notes / ملاحظات"),
		],
		autoname="naming_series:",
		title_field="regulation_title",
		search_fields="regulation_title,company,ministry_certificate_reference",
		icon="fa fa-balance-scale",
	),
	make_doctype(
		"Statutory HR Records Register",
		[
			field("naming_series", "Select", "Naming Series", options="SAU-SHRR-.YYYY.-.####", reqd=1),
			field("register_title", "Data", "Register Title / عنوان سجل الامتثال", reqd=1, in_list_view=1),
			field("company", "Link", "Company / الشركة", options="Company", reqd=1, in_list_view=1),
			column("column_break_1"),
			field("status", "Select", "Status / الحالة", options="Draft / مسودة\nIn Review / قيد المراجعة\nCompliant / ممتثل\nGaps Found / توجد فجوات\nArchived / مؤرشف", default="Draft / مسودة", in_list_view=1),
			field("responsible_user", "Link", "Responsible User / المسؤول", options="User"),
			section("period_section", "Audit Period / فترة المراجعة"),
			field("period_start", "Date", "Period Start / بداية الفترة", reqd=1),
			field("period_end", "Date", "Period End / نهاية الفترة", reqd=1),
			column("column_break_2"),
			field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Labor Law Art.17; Executive Regulations Art.5"),
			field("total_required", "Int", "Required Records / السجلات المطلوبة", read_only=1),
			field("completed_count", "Int", "Available Records / السجلات المتوفرة", read_only=1),
			field("gap_count", "Int", "Gaps / الفجوات", read_only=1),
			section("records_section", "Records Checklist / قائمة السجلات"),
			field("records", "Table", "Records / السجلات", options="Statutory HR Record Row"),
			field("report_attachment", "Attach", "Audit Evidence / مرفق التدقيق"),
			field("notes", "Text Editor", "Notes / ملاحظات"),
		],
		autoname="naming_series:",
		title_field="register_title",
		search_fields="register_title,company,status",
		icon="fa fa-archive",
	),
	make_doctype(
		"Ministry Filing Tracker",
		[
			field("naming_series", "Select", "Naming Series", options="SAU-MFT-.YYYY.-.####", reqd=1),
			field("filing_title", "Data", "Filing Title / عنوان الإفصاح أو البلاغ", reqd=1, in_list_view=1),
			field("filing_type", "Select", "Filing Type / نوع البلاغ", reqd=1, in_list_view=1, options="\nEstablishment Data Update / تحديث بيانات المنشأة\nJob Vacancy Disclosure / بلاغ وظيفة شاغرة\nSaudi Candidate Response / الرد على مرشح سعودي\nAnnual Workforce Disclosure / الإفصاح السنوي عن القوى العاملة\nTraining Disclosure / الإفصاح السنوي عن التدريب\nWPS Submission / رفع حماية الأجور\nGOSI Submission / التأمينات الاجتماعية\nOther / أخرى"),
			field("company", "Link", "Company / الشركة", options="Company", reqd=1, in_list_view=1),
			column("column_break_1"),
			field("status", "Select", "Status / الحالة", options="Pending Submission / بانتظار الرفع\nSubmitted / مرسل\nAccepted / مقبول\nRejected / مرفوض\nCancelled / ملغى\nOverdue / متأخر", default="Pending Submission / بانتظار الرفع", in_list_view=1),
			field("priority", "Select", "Priority / الأولوية", options="\nP0 / حرج\nP1 / مهم\nP2 / تحسين", default="P0 / حرج"),
			section("deadline_section", "Deadlines / المهل"),
			field("trigger_date", "Date", "Trigger Date / تاريخ بداية المهلة", reqd=1),
			field("due_date", "Date", "Due Date / تاريخ الاستحقاق", reqd=1, in_list_view=1),
			column("column_break_2"),
			field("submitted_on", "Date", "Submitted On / تاريخ الرفع"),
			field("accepted_on", "Date", "Accepted On / تاريخ القبول"),
			field("responsible_user", "Link", "Responsible User / المسؤول", options="User"),
			section("evidence_section", "Platform Evidence / إثبات المنصة"),
			field("platform_name", "Data", "Platform / المنصة", default="MHRSD / وزارة الموارد البشرية"),
			field("platform_reference", "Data", "Platform Reference / مرجع المنصة"),
			field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
			field("legal_reference", "Data", "Legal Reference / المرجع النظامي"),
			field("action_log", "Link", "Compliance Action / إجراء الامتثال", options="HR Compliance Action Log"),
			field("notes", "Text Editor", "Notes / ملاحظات"),
		],
		autoname="naming_series:",
		title_field="filing_title",
		search_fields="filing_title,filing_type,platform_reference",
		icon="fa fa-upload",
	),
	make_doctype(
		"Employee Document Custody Log",
		[
			field("naming_series", "Select", "Naming Series", options="SAU-DOC-CUS-.YYYY.-.####", reqd=1),
			field("employee", "Link", "Employee / الموظف", options="Employee", reqd=1, in_list_view=1),
			field("employee_name", "Data", "Employee Name / اسم الموظف", fetch_from="employee.employee_name", read_only=1),
			column("column_break_1"),
			field("company", "Link", "Company / الشركة", options="Company", fetch_from="employee.company", in_list_view=1),
			field("document_type", "Select", "Document Type / نوع المستند", reqd=1, in_list_view=1, options="\nPassport / جواز السفر\nIqama / الإقامة\nMedical Insurance Card / بطاقة التأمين الطبي\nWork Permit / رخصة العمل\nCertificate / شهادة\nOther / أخرى"),
			field("custody_status", "Select", "Custody Status / حالة العهدة", options="Not Held / غير محتفظ به\nTemporary Custody / عهدة مؤقتة\nReturned / أعيد للموظف\nException Under Legal Review / استثناء تحت المراجعة القانونية", default="Not Held / غير محتفظ به", in_list_view=1),
			section("custody_section", "Custody & Return / العهدة والإرجاع"),
			field("original_document_held", "Check", "Original Document Held / الأصل محتفظ به", default=0),
			field("custody_start_date", "Date", "Custody Start Date / تاريخ استلام العهدة"),
			field("return_due_date", "Date", "Return Due Date / مهلة الإرجاع"),
			column("column_break_2"),
			field("returned_on", "Date", "Returned On / تاريخ الإرجاع"),
			field("authorized_by", "Link", "Authorized By / معتمد من", options="User"),
			field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations Art.6"),
			field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
			field("notes", "Text Editor", "Notes / ملاحظات"),
		],
		autoname="naming_series:",
		title_field="employee_name",
		search_fields="employee,employee_name,document_type",
		icon="fa fa-id-card",
	),
	make_doctype(
		"Disability Employment Compliance",
		[
			field("naming_series", "Select", "Naming Series", options="SAU-DIS-.YYYY.-.####", reqd=1),
			field("company", "Link", "Company / الشركة", options="Company", reqd=1, in_list_view=1),
			field("period_start", "Date", "Period Start / بداية الفترة", reqd=1),
			column("column_break_1"),
			field("period_end", "Date", "Period End / نهاية الفترة", reqd=1),
			field("status", "Select", "Status / الحالة", options="Draft / مسودة\nCompliant / ممتثل\nBelow Required Ratio / أقل من النسبة المطلوبة\nNeeds Accommodation Review / يحتاج مراجعة التسهيلات\nNot Applicable / غير منطبق", default="Draft / مسودة", in_list_view=1),
			section("ratio_section", "Ratio / النسبة"),
			field("total_employees", "Int", "Total Employees / إجمالي العاملين", reqd=1),
			field("disabled_employees", "Int", "Qualified Disabled Employees / العاملون ذوو الإعاقة", reqd=1),
			field("required_ratio", "Percent", "Required Ratio / النسبة المطلوبة", default=4),
			column("column_break_2"),
			field("compliance_ratio", "Percent", "Compliance Ratio / نسبة الامتثال", read_only=1),
			field("gap_to_required", "Float", "Gap to Required / الفجوة عن المطلوب", read_only=1),
			field("responsible_user", "Link", "Responsible User / المسؤول", options="User"),
			section("accommodation_section", "Employees & Accommodations / العاملون والتسهيلات"),
			field("accommodations", "Table", "Accommodations / التسهيلات", options="Disability Accommodation Row"),
			field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations Art.9"),
			field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
			field("notes", "Text Editor", "Notes / ملاحظات"),
		],
		autoname="naming_series:",
		title_field="company",
		search_fields="company,status",
		icon="fa fa-universal-access",
	),
	make_doctype(
		"Final Settlement SLA",
		[
			field("naming_series", "Select", "Naming Series", options="SAU-FSLA-.YYYY.-.####", reqd=1),
			field("termination_notice", "Link", "Termination Notice / إشعار الإنهاء", options="Termination Notice", in_list_view=1),
			field("employee", "Link", "Employee / الموظف", options="Employee", reqd=1, in_list_view=1),
			field("employee_name", "Data", "Employee Name / اسم الموظف", fetch_from="employee.employee_name", read_only=1),
			column("column_break_1"),
			field("company", "Link", "Company / الشركة", options="Company", fetch_from="employee.company", in_list_view=1),
			field("status", "Select", "Status / الحالة", options="Open / مفتوح\nIn Progress / قيد التنفيذ\nSettled / تمت التسوية\nOverdue / متأخر\nLegal Review / مراجعة قانونية\nCancelled / ملغى", default="Open / مفتوح", in_list_view=1),
			section("sla_section", "Settlement Deadlines / مهَل التسوية"),
			field("last_working_day", "Date", "Last Working Day / آخر يوم عمل", reqd=1),
			field("termination_initiated_by", "Select", "Termination Initiated By / جهة إنهاء العلاقة", reqd=1, options="Employer / صاحب العمل\nEmployee / الموظف\nNeeds Review / يحتاج مراجعة", default="Needs Review / يحتاج مراجعة"),
			field("settlement_due_date", "Date", "Settlement Due Date / مهلة المخالصة", reqd=1, in_list_view=1),
			column("column_break_2"),
			field("document_return_due_date", "Date", "Document Return Due Date / مهلة إعادة المستندات"),
			field("responsible_user", "Link", "Responsible User / المسؤول", options="User"),
			section("completion_section", "Completion Evidence / إثبات الإغلاق"),
			field("eosb_document", "Link", "EOSB Document / مكافأة نهاية الخدمة", options="End of Service Benefit"),
			field("exit_clearance", "Link", "Exit Clearance / إخلاء الطرف", options="Exit Clearance"),
			field("payment_status", "Select", "Payment Status / حالة الدفع", options="Pending / معلق\nPaid / مدفوع\nNot Applicable / غير منطبق", default="Pending / معلق"),
			field("settlement_paid_on", "Date", "Settlement Paid On / تاريخ دفع المخالصة"),
			column("column_break_3"),
			field("documents_returned_on", "Date", "Documents Returned On / تاريخ إعادة المستندات"),
			section("compensatory_leave_exit_section", "Unused Compensatory Leave / رصيد الإجازة التعويضية", "Unused compensatory leave is paid at the worker's actual hourly wage when employment ends / يعوض رصيد الإجازة التعويضية غير المستخدم وفق أجر الساعة الفعلي عند انتهاء العلاقة"),
			field("unused_compensatory_leave_hours", "Float", "Unused Leave Hours / ساعات التعويض غير المستخدمة"),
			field("actual_hourly_wage_for_leave", "Currency", "Actual Hourly Wage / أجر الساعة الفعلي"),
			field("compensatory_leave_payout_amount", "Currency", "Leave Payout Amount / مبلغ تعويض الإجازة", read_only=1),
			column("compensatory_leave_exit_column"),
			field("compensatory_leave_payout_evidence", "Attach", "Leave Payout Evidence / إثبات دفع تعويض الإجازة"),
			field("compensatory_leave_review_required", "Check", "Leave Balance Review Required / يلزم مراجعة رصيد التعويض", default=0, read_only=1),
			field("legal_review_required", "Check", "Legal Review Required / يحتاج مراجعة قانونية", default=1),
			field("risk_level", "Select", "Risk Level / مستوى المخاطر", options="\nLow / منخفض\nMedium / متوسط\nHigh / مرتفع\nCritical / حرج", default="High / مرتفع"),
			field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
			field("notes", "Text Editor", "Notes / ملاحظات"),
		],
		autoname="naming_series:",
		title_field="employee_name",
		search_fields="employee,employee_name,status",
		icon="fa fa-hourglass-end",
	),
	make_doctype(
		"Work Arrangement Control",
		[
			field("naming_series", "Select", "Naming Series", options="SAU-WAC-.YYYY.-.####", reqd=1),
			field("employee", "Link", "Employee / الموظف", options="Employee", reqd=1, in_list_view=1),
			field("employee_name", "Data", "Employee Name / اسم الموظف", fetch_from="employee.employee_name", read_only=1),
			column("column_break_1"),
			field("company", "Link", "Company / الشركة", options="Company", fetch_from="employee.company", in_list_view=1),
			field("contract", "Link", "Saudi Employment Contract / عقد العمل", options="Saudi Employment Contract"),
			field("arrangement_type", "Select", "Arrangement Type / نوع الترتيب", reqd=1, in_list_view=1, options="\nFlexible Work / العمل المرن\nPart-time Work / العمل لبعض الوقت\nRemote Work / العمل عن بعد\nTemporary Work / العمل المؤقت\nCasual Work / العمل العرضي\nSeasonal Work / العمل الموسمي"),
			field("status", "Select", "Status / الحالة", options="Draft / مسودة\nActive / نشط\nNeeds Review / يحتاج مراجعة\nNeeds Conversion / يحتاج تحويل\nExpired / منتهي\nClosed / مغلق\nCancelled / ملغى", default="Draft / مسودة", in_list_view=1),
			section("period_section", "Period & Limits / المدة والحدود"),
			field("start_date", "Date", "Start Date / تاريخ البداية", reqd=1),
			field("end_date", "Date", "End Date / تاريخ النهاية"),
			field("actual_days", "Int", "Actual Days / الأيام الفعلية", read_only=1),
			column("column_break_2"),
			field("conversion_due_date", "Date", "Conversion Due Date / تاريخ التحول المحتمل"),
			field("conversion_required", "Check", "Conversion Required / يتطلب تحويل", read_only=1),
			field("daily_hours_limit", "Float", "Daily Hours Limit / حد الساعات اليومي"),
			field("weekly_hours_limit", "Float", "Weekly Hours Limit / حد الساعات الأسبوعي"),
			field("monthly_hours", "Float", "Monthly Hours / الساعات الشهرية"),
			field("flexible_overtime_threshold", "Float", "Flexible Overtime Threshold / حد بدء الإضافي للمرن", default=95, read_only=1),
			field("flexible_monthly_maximum", "Float", "Flexible Monthly Maximum / الحد الشهري الأعلى للمرن", default=160, read_only=1),
			field("flexible_overtime_hours", "Float", "Flexible Overtime Hours / ساعات إضافي العمل المرن", read_only=1),
			field("flexible_overtime_at_base_rate", "Check", "Overtime at Base Hourly Rate / الإضافي بأجر الساعة الأساسي", default=1, read_only=1, description="Hours above 95 are paid at the base hourly rate unless otherwise agreed / الساعات فوق 95 تدفع بأجر الساعة الأساسي ما لم يتفق على خلاف ذلك"),
			field("flexible_nitaqat_credit", "Float", "Nitaqat Credit / رصيد نطاقات", read_only=1, description="One Nitaqat point is earned at 160 hours / تحتسب نقطة واحدة في نطاقات عند إكمال 160 ساعة"),
			section("flexible_entitlements_section", "Flexible Work Entitlements / استحقاقات العمل المرن", "Flexible-work statutory exclusions and contract controls / الاستثناءات النظامية وضوابط عقد العمل المرن"),
			field("paid_leave_entitled", "Check", "Paid Leave Entitled / يستحق إجازة مدفوعة", default=0, read_only=1),
			field("eosb_entitled", "Check", "EOSB Entitled / يستحق مكافأة نهاية الخدمة", default=0, read_only=1),
			field("probation_applicable", "Check", "Probation Applies / تخضع لفترة التجربة", default=0, read_only=1),
			field("flexible_contract_max_end_date", "Date", "Maximum Contract End Date / أقصى تاريخ لنهاية العقد", read_only=1),
			field("is_renewal_or_extension", "Check", "Renewal or Extension / تجديد أو تمديد", default=0),
			field("renewal_requires_worker_consent", "Check", "Worker Consent Required / موافقة العامل مطلوبة", default=0, read_only=1),
			field("worker_renewal_consent_reference", "Small Text", "Worker Renewal Consent / موافقة العامل على التجديد", depends_on="eval:doc.is_renewal_or_extension", description="Renewal or extension requires the worker's approval / يتطلب التجديد أو التمديد موافقة العامل"),
			field("regular_contract_conversion_required", "Check", "Regular Contract Conversion Required / يلزم التحويل إلى عقد عادي", default=0, read_only=1),
			section("portal_section", "Portal Evidence / إثبات المنصة"),
			field("saudi_only_applicable", "Check", "Saudi-only Rule Applies / ينطبق شرط السعودي", default=0),
			field("platform_reference", "Data", "Platform Reference / مرجع المنصة"),
			field("compensatory_leave_allowed", "Check", "Compensatory Leave Allowed / يسمح بإجازة تعويضية", default=0),
			field("legal_reference", "Data", "Legal Reference / المرجع النظامي"),
			field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
			field("notes", "Text Editor", "Notes / ملاحظات"),
		],
		autoname="naming_series:",
		title_field="employee_name",
		search_fields="employee,employee_name,arrangement_type,status",
		icon="fa fa-random",
	),
	make_doctype(
		"Working Time Compliance Check",
		[
			field("naming_series", "Select", "Naming Series", options="SAU-WTC-.YYYY.-.####", reqd=1),
			field("employee", "Link", "Employee / الموظف", options="Employee", reqd=1, in_list_view=1),
			field("employee_name", "Data", "Employee Name / اسم الموظف", fetch_from="employee.employee_name", read_only=1),
			column("column_break_1"),
			field("company", "Link", "Company / الشركة", options="Company", fetch_from="employee.company", in_list_view=1),
			field("check_date", "Date", "Check Date / تاريخ الفحص", reqd=1, in_list_view=1),
			field("week_start_date", "Date", "Week Start / بداية الأسبوع"),
			section("category_section", "Work Category / فئة العمل", "المادة (23): تحدد ساعات العمل الفعلية للفئات المستثناة من المادتين (98) و(101) من النظام."),
			field("work_category", "Select", "Work Category / فئة العمل", in_list_view=1, default="Standard / عمل اعتيادي", options="Standard / عمل اعتيادي\nSenior Management / مناصب عالية ذات مسؤولية\nPreparatory or Complementary / أعمال تجهيزية أو تكميلية\nIntermittent by Necessity / عمل متقطع بالضرورة\nGuarding / عمال الحراسة\nCleaning / عمال النظافة"),
			field("is_civil_or_industrial_security", "Check", "Civil or Industrial Security / حراسة أمنية مدنية أو صناعية", default=0, depends_on="eval:doc.work_category=='Guarding / عمال الحراسة'"),
			column("column_break_cat"),
			field("is_ramadan", "Check", "Ramadan Period / خلال شهر رمضان", default=0),
			field("worker_is_muslim", "Check", "Muslim Worker / عامل مسلم", default=1),
			field("prayer_time_enabled", "Check", "Prayer Times Enabled / تمكين أداء الصلوات في أوقاتها", default=1),
			section("hours_section", "Hours / الساعات"),
			field("actual_daily_hours", "Float", "Actual Daily Hours / ساعات اليوم الفعلية"),
			field("actual_weekly_hours", "Float", "Actual Weekly Hours / ساعات الأسبوع الفعلية"),
			field("continuous_rest_hours", "Float", "Continuous Rest per 24h / الراحة المتواصلة خلال 24 ساعة", depends_on="eval:doc.work_category=='Intermittent by Necessity / عمل متقطع بالضرورة'"),
			field("max_consecutive_hours", "Float", "Max Consecutive Hours / أطول فترة عمل متوالية", depends_on="eval:doc.work_category=='Cleaning / عمال النظافة'"),
			column("column_break_2"),
			field("standard_daily_hours", "Float", "Daily Hours Limit / الحد اليومي للساعات", default=8, read_only=1),
			field("standard_weekly_hours", "Float", "Weekly Hours Limit / الحد الأسبوعي للساعات", default=48, read_only=1),
			field("overtime_hours", "Float", "Overtime Hours / ساعات العمل الإضافي", read_only=1),
			section("preparatory_section", "Preparatory and Complementary Work / الأعمال التجهيزية والتكميلية", "المادة (23/6): لا يتجاوز مجموعها ثلاثين دقيقة تضاف إلى ساعات العمل، بحد أقصى خمس عشرة دقيقة لكل منهما."),
			field("preparatory_minutes", "Float", "Preparatory Minutes / دقائق الأعمال التجهيزية"),
			field("complementary_minutes", "Float", "Complementary Minutes / دقائق الأعمال التكميلية"),
			column("column_break_prep"),
			field("total_added_minutes", "Float", "Total Added Minutes / مجموع الدقائق المضافة", read_only=1),
			section("result_section", "Result / النتيجة"),
			field("status", "Select", "Status / الحالة", options="Compliant / ممتثل\nDaily Limit Exceeded / تجاوز الحد اليومي\nWeekly Limit Exceeded / تجاوز الحد الأسبوعي\nCategory Control Breach / مخالفة ضوابط الفئة\nExempt Category / فئة مستثناة\nException Approved / استثناء معتمد\nNeeds Review / يحتاج مراجعة", default="Needs Review / يحتاج مراجعة", in_list_view=1),
			field("breach_summary", "Small Text", "Breach Summary / ملخص المخالفات", read_only=1),
			column("column_break_result"),
			field("approval_reference", "Link", "Approval Reference / مرجع الاعتماد", options="Overtime Request"),
			field("exception_reason", "Small Text", "Exception Reason / سبب الاستثناء"),
			field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations Art.23 (Labor Law Art.108)"),
			field("notes", "Text Editor", "Notes / ملاحظات"),
		],
		autoname="naming_series:",
		title_field="employee_name",
		search_fields="employee,employee_name,status",
		icon="fa fa-clock-o",
	),
	make_doctype(
		"Safety Inspection and Risk Control",
		[
			field("naming_series", "Select", "Naming Series", options="SAU-SAFE-.YYYY.-.####", reqd=1),
			field("inspection_title", "Data", "Inspection Title / عنوان فحص السلامة", reqd=1, in_list_view=1),
			field("company", "Link", "Company / الشركة", options="Company", reqd=1, in_list_view=1),
			column("column_break_1"),
			field("location", "Data", "Location / الموقع"),
			field("inspection_date", "Date", "Inspection Date / تاريخ الفحص", reqd=1, in_list_view=1),
			field("status", "Select", "Status / الحالة", options="Draft / مسودة\nOpen Findings / ملاحظات مفتوحة\nIn Progress / قيد التنفيذ\nControlled / تمت السيطرة\nClosed / مغلق", default="Draft / مسودة", in_list_view=1),
			section("control_section", "Preventive Controls / الضوابط الوقائية"),
			field("inspector_user", "Link", "Inspector / المفتش الداخلي", options="User"),
			field("risk_level", "Select", "Risk Level / مستوى الخطر", options="\nLow / منخفض\nMedium / متوسط\nHigh / مرتفع\nCritical / حرج", default="Medium / متوسط"),
			field("first_aid_available", "Check", "First Aid Available / الإسعافات الأولية متوفرة", default=0),
			column("column_break_2"),
			field("remote_site_controls_required", "Check", "Remote Site Controls Required / يتطلب ضوابط موقع ناء", default=0),
			field("next_inspection_date", "Date", "Next Inspection Date / موعد الفحص القادم"),
			field("action_log", "Link", "Compliance Action / إجراء الامتثال", options="HR Compliance Action Log"),
			section("risk_items_section", "Risk Items / بنود المخاطر"),
			field("risk_items", "Table", "Risk Items / بنود المخاطر", options="Safety Risk Control Item"),
			field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations occupational safety controls"),
			field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
			field("notes", "Text Editor", "Notes / ملاحظات"),
		],
		autoname="naming_series:",
		title_field="inspection_title",
		search_fields="inspection_title,company,location,status",
		icon="fa fa-shield",
	),
	make_doctype(
		"Inspection Fine SLA",
		[
			field("naming_series", "Select", "Naming Series", options="SAU-FINE-.YYYY.-.####", reqd=1),
			field("labor_inspection", "Link", "Labor Inspection / التفتيش العمالي", options="Labor Inspection", in_list_view=1),
			field("company", "Link", "Company / الشركة", options="Company", reqd=1, in_list_view=1),
			column("column_break_1"),
			field("fine_reference", "Data", "Fine Reference / مرجع الغرامة", in_list_view=1),
			field("fine_amount", "Currency", "Fine Amount / مبلغ الغرامة"),
			field("status", "Select", "Status / الحالة", options="Open / مفتوح\nObjected / تم الاعتراض\nPaid / مدفوعة\nWaived / معفاة\nOverdue / متأخرة\nClosed / مغلقة", default="Open / مفتوح", in_list_view=1),
			section("deadline_section", "Deadlines / المهل"),
			field("notification_date", "Date", "Notification Date / تاريخ التبليغ", reqd=1),
			field("payment_due_date", "Date", "Payment Due Date / مهلة السداد", reqd=1, in_list_view=1),
			column("column_break_2"),
			field("paid_on", "Date", "Paid On / تاريخ السداد"),
			field("objection_status", "Select", "Objection Status / حالة الاعتراض", options="Not Filed / لم يقدم\nFiled / مقدم\nAccepted / مقبول\nRejected / مرفوض\nNot Applicable / غير منطبق", default="Not Filed / لم يقدم"),
			field("objection_deadline", "Date", "Objection Deadline / مهلة الاعتراض"),
			field("responsible_user", "Link", "Responsible User / المسؤول", options="User"),
			section("evidence_section", "Evidence / الإثبات"),
			field("action_log", "Link", "Compliance Action / إجراء الامتثال", options="HR Compliance Action Log"),
			field("payment_reference", "Data", "Payment Reference / مرجع السداد"),
			field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
			field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations penalty collection; 60-day payment tracking"),
			field("notes", "Text Editor", "Notes / ملاحظات"),
		],
		autoname="naming_series:",
		title_field="fine_reference",
		search_fields="fine_reference,company,status",
		icon="fa fa-money",
	),
	make_doctype(
		"Contract Portal Evidence",
		[
			field("naming_series", "Select", "Naming Series", options="SAU-CPE-.YYYY.-.####", reqd=1),
			field("contract", "Link", "Saudi Employment Contract / عقد العمل", options="Saudi Employment Contract", reqd=1, in_list_view=1),
			field("employee", "Link", "Employee / الموظف", options="Employee", reqd=1, in_list_view=1),
			field("employee_name", "Data", "Employee Name / اسم الموظف", fetch_from="employee.employee_name", read_only=1),
			column("column_break_1"),
			field("company", "Link", "Company / الشركة", options="Company", fetch_from="employee.company", in_list_view=1),
			field("portal_name", "Data", "Portal / المنصة", default="Qiwa / قوى"),
			field("submission_reference", "Data", "Submission Reference / مرجع التوثيق", in_list_view=1),
			section("status_section", "Portal Status / حالة المنصة"),
			field("status", "Select", "Status / الحالة", options="Draft / مسودة\nSubmitted / مرسل\nEmployee Acknowledged / أقره العامل\nAccepted / مقبول\nRejected / مرفوض\nCancelled / ملغى", default="Draft / مسودة", in_list_view=1),
			field("submitted_on", "Date", "Submitted On / تاريخ الإرسال"),
			column("column_break_2"),
			field("employee_acknowledged_on", "Date", "Employee Acknowledged On / تاريخ إقرار العامل"),
			field("accepted_on", "Date", "Accepted On / تاريخ القبول"),
			field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
			field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations contract models and platform evidence"),
			field("notes", "Text Editor", "Notes / ملاحظات"),
		],
		autoname="naming_series:",
		title_field="submission_reference",
		search_fields="contract,employee,submission_reference",
		icon="fa fa-file-contract",
	),
]


COMPLIANCE_DOCTYPES.extend(
	[
		make_doctype(
			"Disciplinary Violation Catalog",
			[
				field("naming_series", "Select", "Naming Series", options="SAU-DVC-.YYYY.-.####", reqd=1),
				field("violation_code", "Data", "Violation Code / رمز المخالفة", reqd=1, unique=1, in_list_view=1),
				field("violation_name", "Data", "Violation Name / وصف المخالفة", reqd=1, in_list_view=1),
				column("column_break_1"),
				field("category", "Select", "Category / التصنيف", reqd=1, in_list_view=1, options="\nAttendance / مواعيد العمل\nWork Organization / تنظيم العمل\nConduct / سلوك العامل\nSafety / السلامة\nIntegrity / الأمانة\nOther / أخرى"),
				field("status", "Select", "Status / الحالة", in_list_view=1, options="Active / نشط\nNeeds Legal Review / يحتاج مراجعة قانونية\nInactive / غير نشط", default="Active / نشط"),
				section("penalty_section", "Progressive Penalties / الجزاءات حسب التكرار"),
				field("penalty_first", "Small Text", "First Time / أول مرة", reqd=1),
				field("penalty_second", "Small Text", "Second Time / ثاني مرة"),
				column("column_break_2"),
				field("penalty_third", "Small Text", "Third Time / ثالث مرة"),
				field("penalty_fourth", "Small Text", "Fourth Time / رابع مرة"),
				section("control_section", "Legal Controls / الضوابط النظامية"),
				field("max_deduction_days", "Int", "Max Deduction Days / الحد الأعلى لأيام الحسم"),
				field("requires_termination_review", "Check", "Requires Termination Review / يتطلب مراجعة فصل"),
				column("column_break_3"),
				field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Annex 1 - Unified Work Regulation Violation Table"),
				field("source_page", "Data", "PDF Page / صفحة اللائحة"),
				field("notes", "Text Editor", "Notes / ملاحظات"),
			],
			autoname="naming_series:",
			title_field="violation_name",
			search_fields="violation_code,violation_name,category",
			icon="fa fa-list-ol",
		),
		make_doctype(
			"Disability Accommodation Catalog",
			[
				field("naming_series", "Select", "Naming Series", options="SAU-DAC-.YYYY.-.####", reqd=1),
				field("accommodation_code", "Data", "Accommodation Code / رمز التسهيل", reqd=1, unique=1, in_list_view=1),
				field("disability_type", "Select", "Disability Type / نوع الإعاقة", reqd=1, in_list_view=1, options="\nPhysical / جسدية أو حركية\nVisual / بصرية\nHearing / سمعية\nPsychological / نفسية\nMedical Condition / حالة صحية\nGeneral / عام"),
				field("job_family", "Select", "Job Family / طبيعة الوظيفة", reqd=1, in_list_view=1, options="\nOffice / مكتبية\nTechnical / فنية\nTeaching / تعليمية\nManual / يدوية أو عضلية\nAll Jobs / جميع الوظائف"),
				column("column_break_1"),
				field("accommodation_title", "Data", "Accommodation / التسهيل", reqd=1, in_list_view=1),
				field("priority", "Select", "Priority / الأولوية", options="Mandatory Review / مراجعة إلزامية\nRecommended / موصى به\nOptional / اختياري", default="Recommended / موصى به"),
				section("requirement_section", "Checklist Requirement / متطلب القائمة"),
				field("requirement_details", "Text Editor", "Requirement Details / تفاصيل المتطلب", reqd=1),
				field("evidence_required", "Small Text", "Evidence Required / الإثبات المطلوب"),
				column("column_break_2"),
				field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Annex 2 - Accommodation and Facilitation Table"),
				field("source_page", "Data", "PDF Page / صفحة اللائحة"),
				field("active", "Check", "Active / نشط", default=1),
			],
			autoname="naming_series:",
			title_field="accommodation_title",
			search_fields="accommodation_code,disability_type,job_family,accommodation_title",
			icon="fa fa-universal-access",
		),
		make_child_doctype(
			"Recruitment Provider Branch Row",
			[
				field("branch_name", "Data", "Branch Name / اسم الفرع", reqd=1, in_list_view=1),
				field("city", "Data", "City / المدينة", in_list_view=1),
				column("column_break_1"),
				field("approval_reference", "Data", "Ministry Approval Reference / مرجع موافقة الوزارة"),
				field("status", "Select", "Status / الحالة", options="Pending Approval / بانتظار الموافقة\nApproved / معتمد\nClosed / مغلق\nViolation / مخالفة", default="Pending Approval / بانتظار الموافقة", in_list_view=1),
				field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
			],
		),
		make_child_doctype(
			"Recruitment Provider Violation Row",
			[
				field("violation_date", "Date", "Violation Date / تاريخ المخالفة", reqd=1, in_list_view=1),
				field("violation_type", "Select", "Violation Type / نوع المخالفة", reqd=1, in_list_view=1, options="\nLicense Breach / مخالفة الترخيص\nFalse Documents / وثائق غير صحيحة\nUnauthorized Branch / فرع غير مرخص\nComplaint Handling Breach / مخالفة معالجة الشكاوى\nHuman Trafficking Risk / خطر اتجار بالأشخاص\nFinancial or Insurance Breach / مخالفة مالية أو تأمينية\nOther / أخرى"),
				column("column_break_1"),
				field("severity", "Select", "Severity / الخطورة", options="Low / منخفضة\nMedium / متوسطة\nHigh / عالية\nCritical / حرجة", default="Medium / متوسطة"),
				field("status", "Select", "Status / الحالة", options="Open / مفتوحة\nCorrective Action / إجراء تصحيحي\nReported / مبلغة\nClosed / مغلقة", default="Open / مفتوحة", in_list_view=1),
				section("details_section", "Details / التفاصيل"),
				field("description", "Small Text", "Description / الوصف"),
				field("corrective_action", "Small Text", "Corrective Action / الإجراء التصحيحي"),
				field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
			],
		),
		make_doctype(
			"Recruitment Service Provider Compliance",
			[
				field("naming_series", "Select", "Naming Series", options="SAU-RSP-.YYYY.-.####", reqd=1),
				field("provider_name", "Data", "Provider Name / اسم المرخص له", reqd=1, in_list_view=1),
				field("company", "Link", "Internal Company / الشركة الداخلية", options="Company", in_list_view=1),
				column("column_break_1"),
				field("provider_type", "Select", "Provider Type / نوع النشاط", reqd=1, in_list_view=1, options="\nSaudi Recruitment Mediation / التوسط في توظيف السعوديين\nRecruitment and Labor Services / الاستقدام والخدمات العمالية\nSpecialized Labor Services / خدمات عمالية متخصصة\nSupport Labor Services / خدمات العمالة المساندة"),
				field("status", "Select", "Status / الحالة", options="Draft / مسودة\nActive / نشط\nRenewal Due / يستحق التجديد\nUnder Ministry Review / قيد مراجعة الوزارة\nSuspended / موقوف\nExpired / منتهي\nClosed / مغلق", default="Draft / مسودة", in_list_view=1),
				section("license_section", "License / الترخيص"),
				field("license_number", "Data", "License Number / رقم الترخيص", reqd=1, in_list_view=1),
				field("license_issue_date", "Date", "License Issue Date / تاريخ الإصدار"),
				field("license_expiry_date", "Date", "License Expiry Date / تاريخ انتهاء الترخيص", in_list_view=1),
				column("column_break_2"),
				field("renewal_due_date", "Date", "Renewal Due Date / تاريخ بدء التجديد", read_only=1),
				field("ministry_reference", "Data", "Ministry Reference / مرجع الوزارة"),
				field("license_attachment", "Attach", "License Attachment / مرفق الترخيص"),
				section("controls_section", "Mandatory Controls / الضوابط الإلزامية"),
				field("insurance_policy_reference", "Data", "Insurance Policy Reference / مرجع التغطية التأمينية"),
				field("insurance_expiry_date", "Date", "Insurance Expiry Date / انتهاء التأمين"),
				field("bank_account_documented", "Check", "Bank Account Documented / توثيق الحساب البنكي"),
				field("complaint_channel_available", "Check", "Complaint Channel Available / قناة الشكاوى متاحة", default=1),
				column("column_break_3"),
				field("hr_unit_available", "Check", "Independent HR Unit / وحدة موارد بشرية مستقلة"),
				field("compliance_unit_available", "Check", "Independent Compliance Unit / إدارة امتثال مستقلة"),
				field("policy_manual_attachment", "Attach", "Policy Manual / دليل السياسات"),
				field("last_ministry_visit_date", "Date", "Last Ministry Visit / آخر زيارة ترخيصية"),
				section("branches_section", "Branches & Violations / الفروع والمخالفات"),
				field("branches", "Table", "Branches / الفروع", options="Recruitment Provider Branch Row"),
				field("violations", "Table", "Violations / المخالفات", options="Recruitment Provider Violation Row"),
				field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Annex 3 and Annex 4 - Recruitment and Labor Services Controls"),
				field("notes", "Text Editor", "Notes / ملاحظات"),
			],
			autoname="naming_series:",
			title_field="provider_name",
			search_fields="provider_name,license_number,provider_type,status",
			icon="fa fa-briefcase",
		),
		make_doctype(
			"Recruitment Provider Complaint",
			[
				field("naming_series", "Select", "Naming Series", options="SAU-RPC-.YYYY.-.####", reqd=1),
				field("provider_compliance", "Link", "Provider Compliance / سجل المرخص له", options="Recruitment Service Provider Compliance", in_list_view=1),
				field("complainant_type", "Select", "Complainant Type / مقدم الشكوى", options="\nWorker / عامل\nEmployer / صاحب عمل\nCustomer / عميل\nMinistry / الوزارة\nOther / أخرى", reqd=1),
				field("complaint_subject", "Data", "Complaint Subject / موضوع الشكوى", reqd=1, in_list_view=1),
				column("column_break_1"),
				field("received_on", "Date", "Received On / تاريخ الاستلام", reqd=1, in_list_view=1),
				field("response_due_date", "Date", "Response Due Date / مهلة الرد"),
				field("status", "Select", "Status / الحالة", options="Open / مفتوحة\nIn Review / قيد المراجعة\nCorrective Action / إجراء تصحيحي\nResolved / معالجة\nEscalated / مصعدة\nOverdue / متأخرة\nClosed / مغلقة", default="Open / مفتوحة", in_list_view=1),
				section("resolution_section", "Resolution / المعالجة"),
				field("complaint_details", "Text Editor", "Complaint Details / تفاصيل الشكوى"),
				field("resolution_summary", "Text Editor", "Resolution Summary / ملخص المعالجة"),
				field("platform_reference", "Data", "Platform Reference / مرجع المنصة"),
				field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
				field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Annex 4 complaint channel and platform handling controls"),
			],
			autoname="naming_series:",
			title_field="complaint_subject",
			search_fields="complaint_subject,provider_compliance,status",
			icon="fa fa-comments",
		),
		make_doctype(
			"Training Agreement",
			[
				field("naming_series", "Select", "Naming Series", options="SAU-TRAGR-.YYYY.-.####", reqd=1),
				field("employee", "Link", "Employee / الموظف", options="Employee", reqd=1, in_list_view=1),
				field("employee_name", "Data", "Employee Name / اسم الموظف", fetch_from="employee.employee_name", read_only=1),
				column("column_break_1"),
				field("company", "Link", "Company / الشركة", options="Company", fetch_from="employee.company", in_list_view=1),
				field("training_record", "Link", "Training Record / سجل التدريب", options="Training Record"),
				field("status", "Select", "Status / الحالة", options="Draft / مسودة\nActive / ساري\nCompleted / مكتمل\nRecovery Due / يستحق استرداد\nWaived / متنازل عنه\nCancelled / ملغى", default="Draft / مسودة", in_list_view=1),
				section("agreement_section", "Agreement Terms / شروط الاتفاق"),
				field("program_name", "Data", "Program Name / اسم البرنامج", reqd=1, in_list_view=1),
				field("agreement_date", "Date", "Agreement Date / تاريخ الاتفاق", reqd=1),
				field("training_start_date", "Date", "Training Start / بداية التدريب"),
				field("training_end_date", "Date", "Training End / نهاية التدريب"),
				column("column_break_2"),
				field("training_cost", "Currency", "Training Cost / تكلفة التدريب"),
				field("employer_paid_cost", "Currency", "Employer Paid Cost / ما تحمله صاحب العمل"),
				field("commitment_months", "Int", "Commitment Months / مدة الالتزام بالأشهر"),
				field("commitment_end_date", "Date", "Commitment End Date / نهاية مدة الالتزام"),
				section("recovery_section", "Recovery Controls / ضوابط الاسترداد"),
				field("recovery_applicable", "Check", "Recovery Applicable / ينطبق الاسترداد"),
				field("recovery_amount", "Currency", "Recovery Amount / مبلغ الاسترداد"),
				field("recovery_reason", "Small Text", "Recovery Reason / سبب الاسترداد"),
				column("column_break_3"),
				field("employee_acknowledgement", "Check", "Employee Acknowledgement / إقرار الموظف"),
				field("agreement_attachment", "Attach", "Agreement Attachment / مرفق الاتفاق"),
				field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations training and qualification controls"),
				field("notes", "Text Editor", "Notes / ملاحظات"),
			],
			autoname="naming_series:",
			title_field="program_name",
			search_fields="employee,employee_name,program_name,status",
			icon="fa fa-graduation-cap",
		),
		make_doctype(
			"Special Employment Category Control",
			[
				field("naming_series", "Select", "Naming Series", options="SAU-SECC-.YYYY.-.####", reqd=1),
				field("employee", "Link", "Employee / الموظف", options="Employee", reqd=1, in_list_view=1),
				field("employee_name", "Data", "Employee Name / اسم الموظف", fetch_from="employee.employee_name", read_only=1),
				column("column_break_1"),
				field("company", "Link", "Company / الشركة", options="Company", fetch_from="employee.company", in_list_view=1),
				field("category", "Select", "Category / الفئة", reqd=1, in_list_view=1, options="\nYoung Worker / عامل حدث\nWoman Worker / عاملة\nDisabled Worker / عامل من ذوي الإعاقة\nPregnancy or Nursing / حمل أو رضاعة\nOther Protected Category / فئة خاصة أخرى"),
				field("status", "Select", "Status / الحالة", in_list_view=1, options="Draft / مسودة\nCompliant / ممتثل\nNeeds Review / يحتاج مراجعة\nRestriction Breach / مخالفة قيد\nClosed / مغلق", default="Needs Review / يحتاج مراجعة"),
				section("controls_section", "Controls / الضوابط"),
				field("job_risk_review_required", "Check", "Job Risk Review Required / يتطلب مراجعة مخاطر الوظيفة", default=1),
				field("prohibited_job_review", "Small Text", "Prohibited Job Review / مراجعة الأعمال المحظورة"),
				field("training_or_medical_requirement", "Small Text", "Training or Medical Requirement / متطلبات التدريب أو الفحص"),
				column("column_break_2"),
				field("daily_hours_limit", "Float", "Daily Hours Limit / حد الساعات اليومي"),
				field("night_work_restriction", "Check", "Night Work Restriction / قيد العمل الليلي", default=0),
				field("responsible_user", "Link", "Responsible User / المسؤول", options="User"),
				field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
				section("juvenile_section", "Juvenile Controls / ضوابط تشغيل الأحداث", "المادة (32): يحظر تشغيل من أتم الخامسة عشرة ولم يبلغ الثامنة عشرة في الأعمال التي تعرض صحته أو سلامته أو أخلاقه للخطر. المادة (33): لا يجوز تشغيل من لم يتم الخامسة عشرة. المادة (34): يحظر التشغيل ليلاً مدة لا تقل عن اثنتي عشرة ساعة متتالية.", depends_on="eval:doc.category=='Young Worker / عامل حدث'"),
				field("date_of_birth", "Date", "Date of Birth / تاريخ الميلاد", fetch_from="employee.date_of_birth", read_only=1),
				field("age_years", "Float", "Age (Years) / العمر بالسنوات", read_only=1),
				field("assigned_work_description", "Small Text", "Assigned Work / العمل المسند"),
				field("night_shift_assigned", "Check", "Night Shift Assigned / مكلف بعمل ليلي", default=0),
				column("column_break_juv"),
				field("night_work_exception", "Select", "Night Work Exception / استثناء العمل الليلي", options="\nNone / لا يوجد\nFamily-Only Establishment / منشأة يقتصر العمل فيها على أفراد الأسرة\nVocational School or Training Centre / مدارس مهنية ومراكز تدريب\nBakery outside 9pm-4am / مخابز خارج الفترة 9 مساءً - 4 صباحاً\nForce Majeure or Emergency / قوة قاهرة أو طوارئ"),
				field("education_exception_applies", "Check", "Education/Training Exception (Art.167) / استثناء التعليم والتدريب", default=0),
				field("matched_prohibited_work", "Small Text", "Matched Prohibited Work / العمل المحظور المطابق", read_only=1),
				section("education_exception_section", "Education and Training Exception Conditions / شروط استثناء التعليم والتدريب", "المادة (35): لا يسري الاستثناء إلا باستيفاء الشروط الخمسة كاملةً ولمن أتم الرابعة عشرة من عمره.", depends_on="eval:doc.category=='Young Worker / عامل حدث' && doc.education_exception_applies"),
				field("edu_direct_supervision", "Check", "Direct Supervision by Responsible Body / إشراف مباشر من الجهة المسؤولة عن النشاط", default=0),
				field("edu_gradual_method", "Check", "Gradual Training Method / التعليم أو التدريب بأسلوب متدرج لا يشكل صعوبة", default=0),
				field("edu_no_academic_impact", "Check", "No Impact on Academic Achievement / لا يعوق التحصيل الدراسي", default=0),
				column("column_break_edu"),
				field("edu_not_hazardous", "Check", "Not Hazardous Work (Art.161) / ليست من الأعمال الخطرة", default=0),
				field("edu_authority_approval", "Check", "Ministry and Licensing Authority Approval / موافقة الوزارة والجهة المرخِّصة", default=0),
				field("education_exception_valid", "Check", "Exception Conditions Met / الشروط مستوفاة", read_only=1),
				section("juvenile_result_section", "Juvenile Breaches / مخالفات تشغيل الأحداث", depends_on="eval:doc.category=='Young Worker / عامل حدث'"),
				field("minimum_age_breach", "Check", "Below Minimum Age / دون الحد الأدنى للسن", read_only=1),
				field("prohibited_work_breach", "Check", "Prohibited Work Breach / مخالفة عمل محظور", read_only=1),
				column("column_break_juv_result"),
				field("night_work_breach", "Check", "Night Work Breach / مخالفة العمل الليلي", read_only=1),
				field("juvenile_breach_summary", "Small Text", "Breach Summary / ملخص المخالفات", read_only=1),
				field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations Art.32-35 (Labor Law Art.161-167)"),
				field("notes", "Text Editor", "Notes / ملاحظات"),
			],
			autoname="naming_series:",
			title_field="employee_name",
			search_fields="employee,employee_name,category,status",
			icon="fa fa-users",
		),
		make_doctype(
			"Holiday Leave Overlap Rule",
			[
				field("naming_series", "Select", "Naming Series", options="SAU-HOL-.YYYY.-.####", reqd=1),
				field("company", "Link", "Company / الشركة", options="Company", reqd=1, in_list_view=1),
				field("employee", "Link", "Employee / الموظف", options="Employee", in_list_view=1),
				field("employee_name", "Data", "Employee Name / اسم الموظف", fetch_from="employee.employee_name", read_only=1),
				column("column_break_1"),
				field("holiday_name", "Data", "Holiday / العطلة", reqd=1, in_list_view=1),
				field("holiday_date", "Date", "Holiday Date / تاريخ العطلة", reqd=1),
				field("overlap_type", "Select", "Overlap Type / نوع التداخل", reqd=1, options="\nWeekly Rest / راحة أسبوعية\nAnnual Leave / إجازة سنوية\nSick Leave / إجازة مرضية\nOfficial Holiday / عطلة رسمية\nNational or Foundation Day / اليوم الوطني أو يوم التأسيس"),
				section("action_section", "Required Action / الإجراء المطلوب"),
				field("required_action", "Select", "Required Action / الإجراء", options="Extend Leave / تمديد الإجازة\nCompensate Rest Day / تعويض يوم راحة\nApply Sick Leave Pay Rule / تطبيق أجر المرضية\nNo Action / لا إجراء\nLegal Review / مراجعة قانونية", default="Legal Review / مراجعة قانونية", in_list_view=1),
				field("status", "Select", "Status / الحالة", options="Open / مفتوح\nApplied / مطبق\nNot Applicable / غير منطبق\nLegal Review / مراجعة قانونية\nClosed / مغلق", default="Open / مفتوح", in_list_view=1),
				column("column_break_2"),
				field("leave_reference", "Dynamic Link", "Leave Reference / مرجع الإجازة", options="leave_reference_doctype"),
				field("leave_reference_doctype", "Link", "Leave Reference Type / نوع مرجع الإجازة", options="DocType"),
				field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
				field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations official holiday overlap controls"),
				field("notes", "Text Editor", "Notes / ملاحظات"),
			],
			autoname="naming_series:",
			title_field="holiday_name",
			search_fields="holiday_name,employee,status",
			icon="fa fa-calendar",
		),
		make_doctype(
			"Expat Work Authorization Control",
			[
				field("naming_series", "Select", "Naming Series", options="SAU-EWAC-.YYYY.-.####", reqd=1),
				field("employee", "Link", "Employee / الموظف", options="Employee", reqd=1, in_list_view=1),
				field("employee_name", "Data", "Employee Name / اسم الموظف", fetch_from="employee.employee_name", read_only=1),
				column("column_break_1"),
				field("company", "Link", "Company / الشركة", options="Company", fetch_from="employee.company", in_list_view=1),
				field("authorization_type", "Select", "Authorization Type / نوع الإجراء", reqd=1, in_list_view=1, options="\nWork Permit Renewal / تجديد رخصة العمل\nIqama Renewal / تجديد الإقامة\nProfession Change / تغيير المهنة\nService Transfer / نقل الخدمات\nRestricted Occupation Review / مراجعة مهنة مقصورة\nExit/Re-entry Evidence / إثبات خروج وعودة"),
				field("status", "Select", "Status / الحالة", in_list_view=1, options="Draft / مسودة\nPending Platform Action / بانتظار إجراء المنصة\nSubmitted / مرسل\nApproved / معتمد\nRejected / مرفوض\nExpired / منتهي\nClosed / مغلق", default="Draft / مسودة"),
				section("deadline_section", "Deadline & Evidence / المهلة والإثبات"),
				field("request_date", "Date", "Request Date / تاريخ الطلب"),
				field("due_date", "Date", "Due Date / تاريخ الاستحقاق"),
				field("approved_on", "Date", "Approved On / تاريخ الاعتماد"),
				column("column_break_2"),
				field("platform_reference", "Data", "Platform Reference / مرجع المنصة"),
				field("linked_work_permit", "Link", "Work Permit/Iqama / رخصة العمل والإقامة", options="Work Permit Iqama"),
				section("restricted_profession_section", "Restricted Occupation Check / فحص المهن المقصورة", "المادة (11): لا يجوز توظيف غير السعودي في المهن المقصورة على السعوديين، ولا إسناد مهامها إليه بأي مسمى وظيفي آخر."),
				field("target_profession", "Data", "Target Profession / المهنة المستهدفة"),
				field("matched_saudi_only_profession", "Data", "Matched Restricted Profession / المهنة المقصورة المطابقة", read_only=1),
				column("column_break_4"),
				field("restricted_profession_breach", "Check", "Restricted Occupation Breach / مخالفة مهنة مقصورة", read_only=1, in_list_view=1),
				field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
				field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations non-Saudi work authorization controls"),
				field("notes", "Text Editor", "Notes / ملاحظات"),
			],
			autoname="naming_series:",
			title_field="employee_name",
			search_fields="employee,employee_name,authorization_type,status",
			icon="fa fa-id-badge",
		),
		make_doctype(
			"Training Disclosure Register",
			[
				field("naming_series", "Select", "Naming Series", options="SAU-TDR-.YYYY.-.####", reqd=1),
				field("company", "Link", "Company / الشركة", options="Company", reqd=1, in_list_view=1),
				field("disclosure_year", "Int", "Disclosure Year / سنة الإفصاح", reqd=1, in_list_view=1),
				column("column_break_1"),
				field("status", "Select", "Status / الحالة", in_list_view=1, options="Draft / مسودة\nReady / جاهز\nSubmitted / مرسل\nAccepted / مقبول\nNeeds Correction / يحتاج تصحيح\nClosed / مغلق", default="Draft / مسودة"),
				field("responsible_user", "Link", "Responsible User / المسؤول", options="User"),
				section("training_section", "Training Summary / ملخص التدريب"),
				field("total_employees", "Int", "Total Employees / إجمالي العاملين"),
				field("trained_saudi_employees", "Int", "Trained Saudi Employees / السعوديون المدربون"),
				field("training_programs_count", "Int", "Training Programs / عدد البرامج"),
				column("column_break_2"),
				field("disclosure_due_date", "Date", "Disclosure Due Date / مهلة الإفصاح"),
				field("submitted_on", "Date", "Submitted On / تاريخ الرفع"),
				field("platform_reference", "Data", "Platform Reference / مرجع المنصة"),
				field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
				field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations Art.43 training disclosure controls"),
				field("notes", "Text Editor", "Notes / ملاحظات"),
			],
			autoname="naming_series:",
			title_field="company",
			search_fields="company,disclosure_year,status",
			icon="fa fa-graduation-cap",
		),
	]
)


# ---------------------------------------------------------------------------
# المادة (11): المهن المقصورة على السعوديين
# المادة (29): خزانة الإسعافات الطبية
# المادة (30): الأماكن البعيدة عن العمران
# ---------------------------------------------------------------------------
COMPLIANCE_DOCTYPES.extend(
	[
		make_doctype(
			"Saudi Only Profession",
			[
				field("naming_series", "Select", "Naming Series", options="SAU-SOP-.YYYY.-.####", reqd=1),
				field("profession_code", "Data", "Profession Code / رمز المهنة", reqd=1, unique=1, in_list_view=1),
				field("profession_name_ar", "Data", "Profession (Arabic) / المهنة بالعربية", reqd=1, in_list_view=1),
				field("profession_name_en", "Data", "Profession (English) / المهنة بالإنجليزية", in_list_view=1),
				column("column_break_1"),
				field("profession_group", "Select", "Group / المجموعة", options="\nHuman Resources / الموارد البشرية\nReception and Front Office / الاستقبال\nAdministrative Support / الدعم الإداري\nSecurity and Guarding / الأمن والحراسة\nOther Restricted / مهن مقصورة أخرى"),
				field("active", "Check", "Active / نشط", default=1, in_list_view=1),
				section("control_section", "Controls / الضوابط"),
				field("blocks_expat_assignment", "Check", "Blocks Non-Saudi Assignment / يمنع إسناد غير السعودي", default=1),
				field("includes_indirect_assignment", "Check", "Covers Indirect Assignment / يشمل الإسناد غير المباشر", default=1),
				column("column_break_2"),
				field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations Art.11 (Labor Law Art.36)"),
				field("source_page", "Data", "Source Page / صفحة المصدر"),
				field("notes", "Text Editor", "Notes / ملاحظات"),
			],
			autoname="naming_series:",
			title_field="profession_name_ar",
			search_fields="profession_code,profession_name_ar,profession_name_en",
			icon="fa fa-id-badge",
		),
		make_child_doctype(
			"First Aid Cabinet Item",
			[
				field("item_name", "Data", "Item / الصنف", reqd=1, in_list_view=1),
				field("required_quantity", "Float", "Required Qty / الكمية المطلوبة", reqd=1, in_list_view=1),
				field("unit", "Data", "Unit / الوحدة", in_list_view=1),
				column("column_break_1"),
				field("available_quantity", "Float", "Available Qty / الكمية المتوفرة", in_list_view=1),
				field("shortage_quantity", "Float", "Shortage / النقص", read_only=1, in_list_view=1),
				field("expiry_date", "Date", "Earliest Expiry / أقرب تاريخ انتهاء"),
				field("status", "Select", "Status / الحالة", options="Missing / ناقص\nSufficient / مكتمل\nExpired / منتهي\nNeeds Restock / يحتاج تعويض", default="Missing / ناقص", read_only=1, in_list_view=1),
				field("notes", "Small Text", "Notes / ملاحظات"),
			],
		),
		make_doctype(
			"First Aid Cabinet Register",
			[
				field("naming_series", "Select", "Naming Series", options="SAU-FAC-.YYYY.-.####", reqd=1),
				field("company", "Link", "Company / الشركة", options="Company", reqd=1, in_list_view=1),
				field("cabinet_location", "Data", "Cabinet Location / موقع الخزانة", reqd=1, in_list_view=1),
				field("work_site", "Data", "Work Site / موقع العمل"),
				column("column_break_1"),
				field("responsible_user", "Link", "Responsible Person / المسؤول عن الإسعافات", options="User", reqd=1),
				field("responsible_qualified", "Check", "Responsible Person Trained / المسؤول مؤهل", default=0),
				field("inspection_date", "Date", "Inspection Date / تاريخ الفحص", reqd=1, in_list_view=1, default="Today"),
				field("next_inspection_date", "Date", "Next Inspection / الفحص القادم"),
				section("conditions_section", "Storage and Signage / الحفظ والإعلان"),
				field("storage_conditions_met", "Check", "Healthy Storage and Temperature / ظروف حفظ صحية ودرجة حرارة مناسبة", default=0),
				field("red_crescent_marked", "Check", "Marked with Red Crescent on White / معلّمة بهلال أحمر على خلفية بيضاء", default=0),
				column("column_break_2"),
				field("location_signage_posted", "Check", "Location Signage Posted / إعلانات ظاهرة تدل على مكان الخزانة", default=0),
				field("responsible_name_posted", "Check", "Responsible Name Posted / اسم المسؤول معلن", default=0),
				section("items_section", "Cabinet Contents / محتويات الخزانة"),
				field("items", "Table", "Items / الأصناف", options="First Aid Cabinet Item"),
				section("result_section", "Result / النتيجة"),
				field("total_shortage_items", "Int", "Items Short / أصناف ناقصة", read_only=1, in_list_view=1),
				field("compliance_score", "Percent", "Compliance / نسبة الاكتمال", read_only=1),
				column("column_break_3"),
				field("status", "Select", "Status / الحالة", options="Draft / مسودة\nCompliant / ممتثل\nRestock Required / يحتاج تعويض\nNon-Compliant / غير ممتثل", default="Draft / مسودة", read_only=1, in_list_view=1),
				field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
				field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations Art.29 (Labor Law Art.142)"),
				field("notes", "Text Editor", "Notes / ملاحظات"),
			],
			autoname="naming_series:",
			title_field="cabinet_location",
			search_fields="company,cabinet_location,status",
			icon="fa fa-medkit",
		),
		make_doctype(
			"Remote Work Site Compliance",
			[
				field("naming_series", "Select", "Naming Series", options="SAU-RWS-.YYYY.-.####", reqd=1),
				field("company", "Link", "Company / الشركة", options="Company", reqd=1, in_list_view=1),
				field("site_name", "Data", "Site Name / اسم الموقع", reqd=1, in_list_view=1),
				field("assessment_date", "Date", "Assessment Date / تاريخ التقييم", reqd=1, default="Today"),
				column("column_break_1"),
				field("workers_count", "Int", "Workers on Site / عدد العمال بالموقع"),
				field("responsible_user", "Link", "Responsible User / المسؤول", options="User"),
				section("classification_section", "Remote Classification / تصنيف البعد عن العمران", "المادة (30): يزيد على 50 كم بطريق معبد أو 25 كم بطريق غير معبد، أو تجمع سكاني تنقصه المرافق والخدمات."),
				field("road_type", "Select", "Road Type / نوع الطريق", options="\nPaved / معبد\nUnpaved / غير معبد", in_list_view=1),
				field("distance_km", "Float", "Distance from Urban Scope (km) / المسافة عن النطاق العمراني"),
				column("column_break_2"),
				field("lacks_facilities_settlement", "Check", "Settlement Lacking Facilities / تجمع سكاني تنقصه المرافق", default=0),
				field("is_remote_area", "Check", "Classified Remote / مصنّف بعيداً عن العمران", read_only=1, in_list_view=1),
				section("obligations_section", "Employer Obligations / التزامات صاحب العمل", "تُقدَّم على نفقة صاحب العمل وفق ما يحدده الوزير — المادة (146) من النظام."),
				field("shops_provided", "Check", "Shops at Fair Prices / حوانيت بأسعار معتدلة", default=0),
				field("recreation_provided", "Check", "Recreation and Sports Facilities / وسائل ترفيه وملاعب رياضية", default=0),
				field("medical_care_provided", "Check", "Medical Care for Workers and Families / ترتيبات طبية للعمال وأسرهم", default=0),
				column("column_break_3"),
				field("schools_provided", "Check", "Schools for Workers' Children / مدارس لأولاد العمال", default=0),
				field("mosques_provided", "Check", "Mosques or Prayer Rooms / مساجد أو مصليات", default=0),
				field("literacy_programs_provided", "Check", "Literacy Programs / برامج محو الأمية", default=0),
				section("result_section", "Result / النتيجة"),
				field("obligations_met", "Int", "Obligations Met / الالتزامات المستوفاة", read_only=1, in_list_view=1),
				field("compliance_score", "Percent", "Compliance / نسبة الامتثال", read_only=1),
				column("column_break_4"),
				field("status", "Select", "Status / الحالة", options="Draft / مسودة\nNot Applicable / غير منطبق\nCompliant / ممتثل\nPartially Compliant / ممتثل جزئياً\nNon-Compliant / غير ممتثل", default="Draft / مسودة", read_only=1, in_list_view=1),
				field("evidence_attachment", "Attach", "Evidence / مرفق الإثبات"),
				field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations Art.30 (Labor Law Art.146)"),
				field("notes", "Text Editor", "Notes / ملاحظات"),
			],
			autoname="naming_series:",
			title_field="site_name",
			search_fields="company,site_name,status",
			icon="fa fa-map-marker",
		),
	]
)


# ---------------------------------------------------------------------------
# المادة (32): الأعمال المحظورة على الأحداث
# ---------------------------------------------------------------------------
COMPLIANCE_DOCTYPES.extend(
	[
		make_doctype(
			"Juvenile Prohibited Work",
			[
				field("naming_series", "Select", "Naming Series", options="SAU-JPW-.YYYY.-.####", reqd=1),
				field("work_code", "Data", "Work Code / رمز العمل", reqd=1, unique=1, in_list_view=1),
				field("work_name_ar", "Small Text", "Prohibited Work (Arabic) / العمل المحظور بالعربية", reqd=1, in_list_view=1),
				field("work_name_en", "Small Text", "Prohibited Work (English) / العمل المحظور بالإنجليزية"),
				column("column_break_1"),
				field("hazard_type", "Select", "Hazard Type / نوع الخطر", options="\nHealth / صحي\nSafety / السلامة\nMoral / أخلاقي\nPhysical / جسدي\nPsychological / نفسي"),
				field("active", "Check", "Active / نشط", default=1, in_list_view=1),
				section("matching_section", "Detection Keywords / كلمات الرصد"),
				field("keywords", "Small Text", "Keywords / الكلمات الدالة", description="كلمات مفصولة بفواصل تُستخدم لرصد العمل المسند للحدث."),
				column("column_break_2"),
				field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations Art.32 (Labor Law Art.161)"),
				field("source_page", "Data", "Source Page / صفحة المصدر"),
				field("notes", "Text Editor", "Notes / ملاحظات"),
			],
			autoname="naming_series:",
			title_field="work_name_ar",
			search_fields="work_code,work_name_ar,work_name_en",
			icon="fa fa-child",
		),
	]
)


CUSTOM_FIELDS = {
	"Employee": [
		{
			"fieldname": "gosi_first_contribution_date",
			"fieldtype": "Date",
			"label": "GOSI First Contribution Date / تاريخ أول اشتراك في التأمينات",
			"insert_after": "date_of_joining",
			"description": (
				"تاريخ أول مدة اشتراك للعامل في التأمينات الاجتماعية أو التقاعد المدني. "
				"من بدأ اشتراكه قبل 3 يوليو 2024 يبقى على النظام السابق، ومن بدأ في هذا التاريخ أو بعده يخضع لنظام التأمينات الجديد. "
				"إذا تُرك فارغاً يُستخدم تاريخ الالتحاق بالعمل كتقدير."
			),
		},
		{
			"fieldname": "gosi_subscription_date_source",
			"fieldtype": "Select",
			"label": "Subscription Date Source / مصدر تاريخ الاشتراك",
			"insert_after": "gosi_first_contribution_date",
			"options": "\nAssumed from Joining Date / مُقدَّر من تاريخ الالتحاق\nConfirmed from GOSI / مؤكد من التأمينات",
			"description": (
				"القيمة المُقدَّرة تعني أن التاريخ مأخوذ من تاريخ الالتحاق بالعمل ولم يُطابَق بسجل التأمينات، "
				"وقد تكون خاطئة إذا كانت للعامل مدد اشتراك سابقة لدى صاحب عمل آخر."
			),
		},
	],
	"End of Service Benefit": [
		{
			"fieldname": "wage_basis_section",
			"fieldtype": "Section Break",
			"label": "EOSB Wage Basis Review / مراجعة أساس أجر المكافأة",
			"insert_after": "last_basic_salary",
			"description": "Legal review marker because EOSB may require the last wage rather than basic salary only.",
		},
		{
			"fieldname": "eosb_wage_basis",
			"fieldtype": "Select",
			"label": "EOSB Wage Basis / أساس أجر المكافأة",
			"insert_after": "wage_basis_section",
			"options": "Basic Salary / الراتب الأساسي\nTotal Contract Wage / الأجر الشامل في العقد\nManual Legal Review / مراجعة قانونية يدوية",
			"default": "Basic Salary / الراتب الأساسي",
			"reqd": 1,
		},
		{
			"fieldname": "last_total_salary",
			"fieldtype": "Currency",
			"label": "Last Total Wage / آخر أجر شامل",
			"insert_after": "eosb_wage_basis",
			"description": "Auto-filled from Saudi Employment Contract total salary when available.",
		},
		{
			"fieldname": "legal_review_required",
			"fieldtype": "Check",
			"label": "Legal Review Required / يحتاج مراجعة قانونية",
			"insert_after": "last_total_salary",
			"default": 1,
		},
		{
			"fieldname": "legal_review_notes",
			"fieldtype": "Small Text",
			"label": "Legal Review Notes / ملاحظات المراجعة القانونية",
			"insert_after": "legal_review_required",
		},
	],
	"Labor Inspection Violation": [
		{
			"fieldname": "fine_payment_due_date",
			"fieldtype": "Date",
			"label": "Fine Payment Due Date / مهلة سداد الغرامة",
			"insert_after": "fine_amount",
			"description": "Use for the 60-day penalty payment tracking when a fine notification date is known.",
		},
		{
			"fieldname": "fine_payment_status",
			"fieldtype": "Select",
			"label": "Fine Payment Status / حالة سداد الغرامة",
			"insert_after": "fine_payment_due_date",
			"options": "Not Applicable / غير منطبق\nPending / معلق\nPaid / مدفوع\nObjected / معترض عليه\nOverdue / متأخر",
			"default": "Not Applicable / غير منطبق",
		},
	],
	"Saudi Employment Contract": [
		{
			"fieldname": "contract_variant_section",
			"fieldtype": "Section Break",
			"label": "Regulatory Contract Variant / نوع العقد النظامي",
			"insert_after": "contract_type",
		},
		{
			"fieldname": "regulatory_contract_variant",
			"fieldtype": "Select",
			"label": "Regulatory Contract Variant / نوع العقد النظامي",
			"insert_after": "contract_variant_section",
			"options": "Standard / قياسي\nPart-time / لبعض الوقت\nFlexible / مرن\nRemote / عن بعد\nTemporary / مؤقت\nCasual / عرضي\nSeasonal / موسمي",
			"default": "Standard / قياسي",
		},
		{
			"fieldname": "portal_evidence_reference",
			"fieldtype": "Link",
			"label": "Portal Evidence / إثبات المنصة",
			"insert_after": "regulatory_contract_variant",
			"options": "Contract Portal Evidence",
		},
	],
	"Disciplinary Procedure": [
		{
			"fieldname": "violation_catalog_section",
			"fieldtype": "Section Break",
			"label": "Annex 1 Violation Catalog / كتالوج مخالفات ملحق 1",
			"insert_after": "violation_type",
			"description": "Use the unified work regulation violation table before issuing the penalty decision.",
		},
		{
			"fieldname": "violation_catalog",
			"fieldtype": "Link",
			"label": "Violation Catalog / المخالفة النظامية",
			"insert_after": "violation_catalog_section",
			"options": "Disciplinary Violation Catalog",
		},
		{
			"fieldname": "occurrence_number",
			"fieldtype": "Int",
			"label": "Occurrence Number / رقم التكرار",
			"insert_after": "violation_catalog",
			"default": 1,
			"description": "1 to 4 based on repeated violation history.",
		},
		{
			"fieldname": "recommended_penalty",
			"fieldtype": "Small Text",
			"label": "Recommended Penalty / الجزاء المقترح",
			"insert_after": "occurrence_number",
			"read_only": 1,
		},
		{
			"fieldname": "catalog_legal_reference",
			"fieldtype": "Data",
			"label": "Catalog Legal Reference / المرجع من الكتالوج",
			"insert_after": "recommended_penalty",
			"read_only": 1,
		},
		{
			"fieldname": "catalog_requires_review",
			"fieldtype": "Check",
			"label": "Catalog Requires Review / الكتالوج يتطلب مراجعة",
			"insert_after": "catalog_legal_reference",
			"read_only": 1,
		},
	],
	"Disability Accommodation Row": [
		{
			"fieldname": "accommodation_catalog",
			"fieldtype": "Link",
			"label": "Accommodation Catalog / كتالوج التسهيلات",
			"insert_after": "accommodation_type",
			"options": "Disability Accommodation Catalog",
		},
		{
			"fieldname": "catalog_requirement_details",
			"fieldtype": "Small Text",
			"label": "Catalog Requirement / متطلب الكتالوج",
			"insert_after": "accommodation_catalog",
			"read_only": 1,
		},
	],
}


WORKSPACE_COMPLIANCE_GROUPS = [
	{
		"id": "saudi_hr_card_regulation_records",
		"label": "لوائح وسجلات الامتثال",
		"links": [
			("Saudi HR Command Center", "saudi-compliance-command-center", "Page"),
			("Work Regulation", "Work Regulation", "DocType"),
			("Disciplinary Violation Catalog", "Disciplinary Violation Catalog", "DocType"),
			("Disability Accommodation Catalog", "Disability Accommodation Catalog", "DocType"),
			("Statutory HR Records Register", "Statutory HR Records Register", "DocType"),
			("Ministry Filing Tracker", "Ministry Filing Tracker", "DocType"),
			("Training Disclosure Register", "Training Disclosure Register", "DocType"),
		],
	},
	{
		"id": "saudi_hr_card_employee_evidence",
		"label": "إثباتات الموظفين والعقود",
		"links": [
			("Employee Document Custody Log", "Employee Document Custody Log", "DocType"),
			("Contract Portal Evidence", "Contract Portal Evidence", "DocType"),
			("Training Agreement", "Training Agreement", "DocType"),
			("Disability Employment Compliance", "Disability Employment Compliance", "DocType"),
			("Expat Work Authorization Control", "Expat Work Authorization Control", "DocType"),
		],
	},
	{
		"id": "saudi_hr_card_recruitment_providers",
		"label": "مكاتب التوظيف والاستقدام",
		"links": [
			("Recruitment Service Provider Compliance", "Recruitment Service Provider Compliance", "DocType"),
			("Recruitment Provider Complaint", "Recruitment Provider Complaint", "DocType"),
		],
	},
	{
		"id": "saudi_hr_card_working_controls",
		"label": "أنماط وساعات العمل",
		"links": [
			("Work Arrangement Control", "Work Arrangement Control", "DocType"),
			("Working Time Compliance Check", "Working Time Compliance Check", "DocType"),
			("Holiday Leave Overlap Rule", "Holiday Leave Overlap Rule", "DocType"),
			("Special Employment Category Control", "Special Employment Category Control", "DocType"),
			("Juvenile Prohibited Work", "Juvenile Prohibited Work", "DocType"),
		],
	},
	{
		"id": "saudi_hr_card_safety_inspection",
		"label": "السلامة والتفتيش والغرامات",
		"links": [
			("Safety Inspection and Risk Control", "Safety Inspection and Risk Control", "DocType"),
			("First Aid Cabinet Register", "First Aid Cabinet Register", "DocType"),
			("Inspection Fine SLA", "Inspection Fine SLA", "DocType"),
			("Labor Inspection", "Labor Inspection", "DocType"),
			("Work Injury", "Work Injury", "DocType"),
		],
	},
	{
		"id": "saudi_hr_card_site_and_occupation",
		"label": "مواقع العمل والمهن المقصورة",
		"links": [
			("Remote Work Site Compliance", "Remote Work Site Compliance", "DocType"),
			("Saudi Only Profession", "Saudi Only Profession", "DocType"),
		],
	},
]

WORKSPACE_REPORT_LINKS = [
	(
		"Saudi Compliance Obligation Backlog",
		"Saudi Compliance Obligation Backlog",
		"Report",
	),
	(
		"Saudi Legal Review Queue",
		"Saudi Legal Review Queue",
		"Report",
	),
]

WORKSPACE_EXIT_LINK = ("Final Settlement SLA", "Final Settlement SLA", "DocType")
VALID_WORKSPACE_LINK_TYPES = {"DocType", "Page", "Report"}
WORKSPACE_SUBTITLE = (
	'<span class="h6 text-muted">مساحة عمل احترافية لإدارة عمليات اليوم، ودورة الموظف، '
	'والحضور، والرواتب، والامتثال السعودي.</span>'
)

DISCIPLINARY_CATALOG_DEFAULTS = [
	("ATT-001", "Attendance / مواعيد العمل", "Late up to 15 minutes without disruption / التأخر حتى 15 دقيقة دون تعطيل", "Written warning / إنذار كتابي", "5% daily wage", "10% daily wage", "20% daily wage", 40),
	("ATT-002", "Attendance / مواعيد العمل", "Late up to 15 minutes with disruption / التأخر حتى 15 دقيقة مع تعطيل", "Written warning / إنذار كتابي", "15% daily wage", "25% daily wage", "50% daily wage", 40),
	("ATT-003", "Attendance / مواعيد العمل", "Late more than 15 up to 30 minutes without disruption / التأخر أكثر من 15 إلى 30 دقيقة دون تعطيل", "10% daily wage", "15% daily wage", "25% daily wage", "50% daily wage", 40),
	("ATT-004", "Attendance / مواعيد العمل", "Late more than 15 up to 30 minutes with disruption / التأخر أكثر من 15 إلى 30 دقيقة مع تعطيل", "25% daily wage", "50% daily wage", "75% daily wage", "One day / يوم", 40),
	("ATT-005", "Attendance / مواعيد العمل", "Late more than 30 up to 60 minutes without disruption / التأخر أكثر من 30 إلى 60 دقيقة دون تعطيل", "25% daily wage", "50% daily wage", "75% daily wage", "One day / يوم", 40),
	("ATT-006", "Attendance / مواعيد العمل", "Late more than 30 up to 60 minutes with disruption / التأخر أكثر من 30 إلى 60 دقيقة مع تعطيل", "30% daily wage", "50% daily wage", "One day / يوم", "Two days plus late-time deduction / يومان مع حسم التأخير", 40),
	("ATT-007", "Attendance / مواعيد العمل", "Late more than one hour / التأخر لأكثر من ساعة", "Written warning / إنذار كتابي", "One day / يوم", "Two days / يومان", "Three days plus late-time deduction / ثلاثة أيام مع حسم التأخير", 40),
	("ATT-008", "Attendance / مواعيد العمل", "Leaving work up to 15 minutes early / ترك العمل أو الانصراف قبل الموعد بما لا يتجاوز 15 دقيقة", "Written warning / إنذار كتابي", "10% daily wage", "25% daily wage", "One day plus time deduction / يوم مع حسم مدة الترك", 40),
	("ATT-009", "Attendance / مواعيد العمل", "Leaving work more than 15 minutes early / ترك العمل أو الانصراف قبل الموعد بما يتجاوز 15 دقيقة", "10% daily wage", "25% daily wage", "50% daily wage", "One day plus time deduction / يوم مع حسم مدة الترك", 40),
	("ATT-010", "Attendance / مواعيد العمل", "Remaining at workplace after hours without permission / البقاء أو العودة لمكان العمل بعد الدوام دون إذن", "Written warning / إنذار كتابي", "10% daily wage", "25% daily wage", "One day / يوم", 40),
	("ATT-011", "Attendance / مواعيد العمل", "Absence one day without written permission / الغياب يوماً واحداً دون إذن أو عذر", "50% daily wage", "One day / يوم", "Two days / يومان", "Three days / ثلاثة أيام", 41),
	("ATT-012", "Attendance / مواعيد العمل", "Continuous absence two to six days / الغياب المتصل من يومين إلى ستة أيام", "Two days / يومان", "Three days / ثلاثة أيام", "Four days / أربعة أيام", "Promotion delay or one allowance denial plus absence deduction", 41),
	("ATT-013", "Attendance / مواعيد العمل", "Continuous absence seven to ten days / الغياب المتصل من سبعة إلى عشرة أيام", "Four days / أربعة أيام", "Five days / خمسة أيام", "Promotion delay or one allowance denial", "Termination with EOSB if absence total does not exceed 30 days", 41),
	("ATT-014", "Attendance / مواعيد العمل", "Continuous absence eleven to fourteen days / الغياب المتصل من 11 إلى 14 يوماً", "Five days / خمسة أيام", "Promotion delay or one allowance denial with termination warning", "Termination under Article 80 / فصل طبقاً للمادة 80", "Legal review / مراجعة قانونية", 41),
	("ATT-015", "Attendance / مواعيد العمل", "Continuous absence more than fifteen days / الانقطاع أكثر من خمسة عشر يوماً متصلة", "Termination without EOSB after written warning / فصل دون مكافأة بعد إنذار", "", "", "", 41),
	("ATT-016", "Attendance / مواعيد العمل", "Intermittent absence exceeding thirty days / الغياب المتقطع أكثر من ثلاثين يوماً", "Termination without EOSB after written warning / فصل دون مكافأة بعد إنذار", "", "", "", 41),
	("ORG-001", "Work Organization / تنظيم العمل", "Being outside assigned workplace during work time / التواجد في غير مكان العمل", "10% daily wage", "25% daily wage", "50% daily wage", "One day / يوم", 41),
	("ORG-002", "Work Organization / تنظيم العمل", "Receiving non-work visitors without permission / استقبال زوار لغير أمور العمل", "Written warning / إنذار كتابي", "10% daily wage", "15% daily wage", "25% daily wage", 41),
	("ORG-003", "Work Organization / تنظيم العمل", "Using company tools for private purposes / استعمال معدات المنشأة لأغراض خاصة", "Written warning / إنذار كتابي", "10% daily wage", "25% daily wage", "50% daily wage", 41),
	("ORG-004", "Work Organization / تنظيم العمل", "Interfering in work outside assignment / التدخل في عمل ليس من الاختصاص", "50% daily wage", "One day / يوم", "Two days / يومان", "Three days / ثلاثة أيام", 41),
	("ORG-005", "Work Organization / تنظيم العمل", "Entering or exiting from unauthorized place / الدخول أو الخروج من غير المكان المخصص", "Written warning / إنذار كتابي", "10% daily wage", "15% daily wage", "25% daily wage", 42),
	("ORG-006", "Work Organization / تنظيم العمل", "Neglecting cleaning or maintenance of machines / الإهمال في تنظيف الآلات أو صيانتها", "50% daily wage", "One day / يوم", "Two days / يومان", "Three days / ثلاثة أيام", 42),
	("ORG-007", "Work Organization / تنظيم العمل", "Not returning tools to assigned places / عدم وضع أدوات الصيانة في أماكنها", "Written warning / إنذار كتابي", "25% daily wage", "50% daily wage", "One day / يوم", 42),
	("ORG-008", "Work Organization / تنظيم العمل", "Tearing or damaging company announcements / تمزيق أو إتلاف إعلانات المنشأة", "Two days / يومان", "Three days / ثلاثة أيام", "Five days / خمسة أيام", "Termination with EOSB / فصل مع المكافأة", 42),
	("ORG-009", "Work Organization / تنظيم العمل", "Neglecting employee custody items / الإهمال في العهد", "Two days / يومان", "Three days / ثلاثة أيام", "Five days / خمسة أيام", "Termination with EOSB / فصل مع المكافأة", 42),
	("ORG-010", "Work Organization / تنظيم العمل", "Eating in unauthorized place or time / الأكل في غير المكان أو الوقت المعد", "Written warning / إنذار كتابي", "10% daily wage", "15% daily wage", "25% daily wage", 42),
	("ORG-011", "Work Organization / تنظيم العمل", "Sleeping during work / النوم أثناء العمل", "Written warning / إنذار كتابي", "10% daily wage", "25% daily wage", "50% daily wage", 42),
	("ORG-012", "Work Organization / تنظيم العمل", "Sleeping where continuous alertness is required / النوم في حالات تتطلب يقظة مستمرة", "50% daily wage", "One day / يوم", "Two days / يومان", "Three days / ثلاثة أيام", 42),
	("ORG-013", "Work Organization / تنظيم العمل", "Loitering or being outside work area / التسكع أو الوجود في غير مكان العمل", "10% daily wage", "25% daily wage", "50% daily wage", "One day / يوم", 42),
	("ORG-014", "Work Organization / تنظيم العمل", "Tampering with attendance evidence / التلاعب في إثبات الحضور والانصراف", "One day / يوم", "Two days / يومان", "Promotion delay or one allowance denial", "Termination with EOSB / فصل مع المكافأة", 42),
	("ORG-015", "Work Organization / تنظيم العمل", "Disobeying normal work orders / عدم إطاعة الأوامر أو التعليمات", "25% daily wage", "50% daily wage", "One day / يوم", "Two days / يومان", 42),
	("ORG-016", "Work Organization / تنظيم العمل", "Inciting violation of written work instructions / التحريض على مخالفة التعليمات", "Two days / يومان", "Three days / ثلاثة أيام", "Five days / خمسة أيام", "Termination with EOSB / فصل مع المكافأة", 42),
	("ORG-017", "Safety / السلامة", "Smoking in prohibited places / التدخين في الأماكن المحظورة", "Two days / يومان", "Three days / ثلاثة أيام", "Five days / خمسة أيام", "Termination with EOSB / فصل مع المكافأة", 42),
	("ORG-018", "Safety / السلامة", "Neglect causing health, safety, material, or equipment harm / الإهمال المسبب لضرر صحي أو سلامة أو مواد", "Two days / يومان", "Three days / ثلاثة أيام", "Five days / خمسة أيام", "Termination with EOSB / فصل مع المكافأة", 42),
	("CON-001", "Conduct / سلوك العامل", "Fighting or creating disturbances / التشاجر أو إحداث مشاغبات", "One day / يوم", "Two days / يومان", "Three days / ثلاثة أيام", "Five days / خمسة أيام", 42),
	("CON-002", "Conduct / سلوك العامل", "False work injury claim / ادعاء كاذب بإصابة عمل", "One day / يوم", "Two days / يومان", "Three days / ثلاثة أيام", "Five days / خمسة أيام", 42),
	("CON-003", "Conduct / سلوك العامل", "Refusing medical examination or treatment instructions / رفض الفحص الطبي أو التعليمات الطبية", "One day / يوم", "Two days / يومان", "Three days / ثلاثة أيام", "Five days / خمسة أيام", 42),
	("CON-004", "Safety / السلامة", "Violating health instructions / مخالفة التعليمات الصحية", "50% daily wage", "One day / يوم", "Two days / يومان", "Five days / خمسة أيام", 43),
	("CON-005", "Conduct / سلوك العامل", "Writing on walls or posting announcements / الكتابة على الجدران أو لصق إعلانات", "Written warning / إنذار كتابي", "10% daily wage", "25% daily wage", "50% daily wage", 43),
	("CON-006", "Conduct / سلوك العامل", "Refusing administrative inspection on leaving / رفض التفتيش الإداري", "25% daily wage", "50% daily wage", "One day / يوم", "Two days / يومان", 43),
	("CON-007", "Integrity / الأمانة", "Not delivering collected funds on time / عدم تسليم النقود المحصلة", "Two days / يومان", "Three days / ثلاثة أيام", "Five days / خمسة أيام", "Termination with EOSB / فصل مع المكافأة", 43),
	("CON-008", "Safety / السلامة", "Refusing protective clothing or safety devices / الامتناع عن ارتداء وسائل الوقاية", "Written warning / إنذار كتابي", "One day / يوم", "Two days / يومان", "Five days / خمسة أيام", 43),
	("CON-009", "Conduct / سلوك العامل", "Intentional seclusion with other gender at work / تعمد الخلوة في أماكن العمل", "Two days / يومان", "Three days / ثلاثة أيام", "Five days / خمسة أيام", "Termination with EOSB / فصل مع المكافأة", 43),
	("CON-010", "Conduct / سلوك العامل", "Indecent verbal or physical insinuation / الإيحاء بما يخدش الحياء", "Two days / يومان", "Three days / ثلاثة أيام", "Five days / خمسة أيام", "Termination with EOSB / فصل مع المكافأة", 43),
	("CON-011", "Conduct / سلوك العامل", "Insulting coworkers verbally, by gesture, or electronically / الاعتداء بالقول أو الإشارة على الزملاء", "Two days / يومان", "Three days / ثلاثة أيام", "Five days / خمسة أيام", "Termination with EOSB / فصل مع المكافأة", 43),
	("CON-012", "Conduct / سلوك العامل", "Physical assault of coworkers or others indecently / الاعتداء الجسدي بطريقة إباحية", "Termination without EOSB under Article 80 / فصل دون مكافأة", "", "", "", 43),
	("CON-013", "Conduct / سلوك العامل", "Assault against employer, manager, or supervisor / الاعتداء على صاحب العمل أو المدير أو الرئيس", "Termination without EOSB under Article 80 / فصل دون مكافأة", "", "", "", 43),
	("CON-014", "Conduct / سلوك العامل", "Malicious report or complaint / تقديم بلاغ أو شكوى كيدية", "Three days / ثلاثة أيام", "Five days / خمسة أيام", "Termination with EOSB / فصل مع المكافأة", "", 43),
	("CON-015", "Conduct / سلوك العامل", "Not complying with investigation committee attendance / عدم الامتثال للحضور أمام لجنة التحقيق", "Two days / يومان", "Three days / ثلاثة أيام", "Five days / خمسة أيام", "Termination with EOSB / فصل مع المكافأة", 43),
	("CON-016", "Conduct / سلوك العامل", "Not complying with approved official uniform / عدم التقيد بالزي الرسمي", "One day / يوم", "Two days / يومان", "Three days / ثلاثة أيام", "Five days / خمسة أيام", 43),
]

DISABILITY_ACCOMMODATION_DEFAULTS = [
	("DAC-PHY-001", "Physical / جسدية أو حركية", "Office / مكتبية", "Wheelchair accessible office workspace / تهيئة مكتب لمستخدم الكرسي المتحرك", "Ramps, accessible toilets, adjusted desk height, shelf reach, and safe emergency exit route.", "Annex 2 pp.45"),
	("DAC-PHY-002", "Physical / جسدية أو حركية", "Technical / فنية", "Adjusted examination, pharmacy, or training equipment / تهيئة التجهيزات الفنية", "Adjusted beds, shelf heights, training tools, and room layout for movement access.", "Annex 2 pp.45"),
	("DAC-PHY-003", "Physical / جسدية أو حركية", "Teaching / تعليمية", "Accessible classroom or lecture room / تهيئة الفصل أو القاعة", "Ground-floor rooms or accessible elevators, lowered boards, and adequate spacing.", "Annex 2 pp.45"),
	("DAC-PHY-004", "Physical / جسدية أو حركية", "Manual / يدوية أو عضلية", "Adapted manual tools and lifting support / أدوات يدوية ورافعات ملائمة", "Adapted machinery handles, simple lifting aids, and suitable counters or worktops.", "Annex 2 pp.45"),
	("DAC-UPR-001", "Physical / جسدية أو حركية", "Office / مكتبية", "Upper-limb assistive workstation / تهيئة محطة عمل لإعاقة الأطراف العليا", "Modified keyboard, speech-to-text tools, adjustable chair and desk, and reachable controls.", "Annex 2 pp.45"),
	("DAC-SHO-001", "Physical / جسدية أو حركية", "All Jobs / جميع الوظائف", "Short stature access adjustment / تهيئة مناسبة لقصار القامة", "Appropriate heights for devices, furniture, door handles, elevator buttons, movable steps, and vehicle adaptation when needed.", "Annex 2 pp.45"),
	("DAC-VIS-001", "Visual / بصرية", "Office / مكتبية", "Screen reader and Braille support / قارئ شاشة ودعم برايل", "Arabic and English screen reader, Braille display, magnifier, OCR, Braille printer when needed, and safe audio emergency route.", "Annex 2 pp.46"),
	("DAC-VIS-002", "Visual / بصرية", "Technical / فنية", "Accessible technical systems / تهيئة الأنظمة الفنية للمكفوفين", "Portable screen reader, talking calculators or counting tools, accounting software support, and personal assistance when needed.", "Annex 2 pp.46"),
	("DAC-VIS-003", "Visual / بصرية", "Teaching / تعليمية", "Accessible teaching materials / مواد تعليمية مهيأة", "Floor/wall navigation signs, Braille or electronic curricula, large-print materials, and assistant when necessary.", "Annex 2 pp.46"),
	("DAC-HEA-001", "Hearing / سمعية", "Office / مكتبية", "Sign-language and visual alert support / لغة إشارة وإنذار ضوئي", "Sign-language interpreter or trained coworker, visual emergency alert, video-call phone, vibration and sign dictionary where available.", "Annex 2 pp.46"),
	("DAC-HEA-002", "Hearing / سمعية", "Technical / فنية", "Visual monitoring and alerts / مراقبة وتنبيهات بصرية", "Visual monitoring screens and light alerts in clinics, pharmacies, laboratories, and machines.", "Annex 2 pp.46"),
	("DAC-PSY-001", "Psychological / نفسية", "Office / مكتبية", "Low-stimulation workspace and flexible schedule / بيئة هادئة وجدول مرن", "Comfortable wall colors, non-stimulating environment, flexible work and rest schedule, and computerized scheduling when needed.", "Annex 2 pp.47"),
	("DAC-MED-001", "Medical Condition / حالة صحية", "Manual / يدوية أو عضلية", "High-safety tools for diabetes or bleeding conditions / أدوات عالية السلامة", "Use safe tools, machines, and equipment that reduce cuts, wounds, and injury risk for workers with diabetes or blood-fluidity conditions.", "Annex 2 pp.48"),
	("DAC-GEN-001", "General / عام", "All Jobs / جميع الوظائف", "Workforce awareness and attitude adjustment / توعية العاملين وتعديل الاتجاهات", "Awareness and conduct adjustment for coworkers and supervisors to enable inclusive work environment.", "Annex 2 pp.45-48"),
]


def sync_compliance_controls():
	for doctype_def in COMPLIANCE_DOCTYPES:
		sync_doctype(doctype_def)
	sync_custom_fields()
	ensure_compliance_default_rows()
	ensure_gosi_settings_defaults()
	sync_compliance_workspace()


def ensure_gosi_settings_defaults():
	"""ضبط إعدادات التأمينات بعد اكتمال مزامنة الحقول.

	لا يكفي تنفيذ هذا في patch: حقول الإعدادات الجديدة تُنشأ في مرحلة مزامنة
	الـDocTypes التي تلي تنفيذ الترقيات في دورة migrate، فأي قيمة تُكتب قبل
	وجود الحقل تُهمل بصمت. لذلك يُضبط هنا حيث تكون الحقول موجودة فعلاً.
	"""
	if not frappe.db.exists("DocType", "Saudi HR Settings"):
		return
	if not frappe.get_meta("Saudi HR Settings").has_field("gosi_saned_rate"):
		return

	settings = frappe.get_single("Saudi HR Settings")
	changed = False

	# تصحيح نسب ما قبل تخفيض اشتراك ساند من 1% إلى 0.75%
	if flt(settings.gosi_saudi_employee_rate) == 10.0:
		settings.gosi_saudi_employee_rate = 9.75
		changed = True
	if flt(settings.gosi_saudi_employer_rate) == 12.0:
		settings.gosi_saudi_employer_rate = 11.75
		changed = True

	# ساند غير مضبوط يعني أن إعدادات النظام الجديد لم تُهيَّأ بعد، فتُضبط مرة واحدة
	# ولا تُلمس بعدها حتى لا تُلغى اختيارات المستخدم.
	if not flt(settings.get("gosi_saned_rate")):
		settings.gosi_saned_rate = 0.75
		settings.gosi_occupational_hazards_rate = flt(settings.get("gosi_occupational_hazards_rate")) or 2.0
		settings.gosi_apply_new_system_schedule = 1
		changed = True

	if changed:
		settings.flags.ignore_permissions = True
		settings.flags.ignore_validate = True
		settings.save()


def sync_compliance_workspace():
	if not frappe.db.exists("Workspace", "Saudi HR"):
		return

	workspace = frappe.get_doc("Workspace", "Saudi HR")
	content = _get_workspace_content(workspace)
	_sync_workspace_content_cards(content)
	_sync_workspace_links(workspace)
	workspace.content = json.dumps(content, ensure_ascii=False)
	workspace.flags.ignore_links = True
	workspace.flags.ignore_version = True
	workspace.save(ignore_permissions=True)
	frappe.clear_cache()


def _get_workspace_content(workspace):
	try:
		content = json.loads(workspace.content or "[]")
	except Exception:
		content = []
	return content if isinstance(content, list) else []


def _sync_workspace_content_cards(content):
	for row in content:
		if isinstance(row, dict) and row.get("id") == "saudi_hr_subtitle":
			row.setdefault("data", {})["text"] = WORKSPACE_SUBTITLE
			break

	existing_ids = {row.get("id") for row in content if isinstance(row, dict)}
	insert_at = _find_content_index(content, "saudi_hr_card_compliance_legal")
	if insert_at is None:
		insert_at = _find_content_index(content, "saudi_hr_section_governance")
	if insert_at is None:
		insert_at = len(content) - 1

	offset = 1
	for group in WORKSPACE_COMPLIANCE_GROUPS:
		if group["id"] in existing_ids:
			continue
		content.insert(
			insert_at + offset,
			{
				"id": group["id"],
				"type": "card",
				"data": {"card_name": group["label"], "col": 4},
			},
		)
		offset += 1


def _find_content_index(content, item_id):
	for index, row in enumerate(content):
		if isinstance(row, dict) and row.get("id") == item_id:
			return index
	return None


def _sync_workspace_links(workspace):
	group_rows = []
	for group in WORKSPACE_COMPLIANCE_GROUPS:
		group_rows.append(_workspace_card_break(group["label"], len(group["links"])))
		group_rows.extend(_workspace_link(label, link_to, link_type) for label, link_to, link_type in group["links"])

	target_keys = {_workspace_row_key(row) for row in group_rows}
	for report_link in WORKSPACE_REPORT_LINKS:
		target_keys.add(_workspace_row_key(_workspace_link(*report_link)))
	target_keys.add(_workspace_row_key(_workspace_link(*WORKSPACE_EXIT_LINK)))

	new_links = []
	inserted_groups = False
	inserted_reports = False
	inserted_exit = False

	for row in workspace.links:
		cleaned = _clean_workspace_row(row)
		if not cleaned:
			continue
		if _workspace_row_key(cleaned) in target_keys:
			continue

		if not inserted_groups and cleaned.get("type") == "Card Break" and cleaned.get("label") == "التقارير والتحليلات":
			new_links.extend(group_rows)
			inserted_groups = True

		new_links.append(cleaned)

		if not inserted_exit and cleaned.get("type") == "Link" and cleaned.get("link_to") == "Termination Notice":
			new_links.append(_workspace_link(*WORKSPACE_EXIT_LINK))
			inserted_exit = True

		if not inserted_reports and cleaned.get("type") == "Link" and cleaned.get("link_to") == "Saudi Labor Coverage Matrix":
			new_links.extend(_workspace_link(*report_link) for report_link in WORKSPACE_REPORT_LINKS)
			inserted_reports = True

	if not inserted_groups:
		new_links.extend(group_rows)
	if not inserted_exit:
		new_links.append(_workspace_link(*WORKSPACE_EXIT_LINK))
	if not inserted_reports:
		new_links.extend(_workspace_link(*report_link) for report_link in WORKSPACE_REPORT_LINKS)

	_recalculate_workspace_link_counts(new_links)
	new_links = _drop_empty_workspace_cards(new_links)
	_recalculate_workspace_link_counts(new_links)
	workspace.set("links", new_links)


def _workspace_card_break(label, link_count):
	return {
		"type": "Card Break",
		"label": label,
		"hidden": 0,
		"is_query_report": 0,
		"link_count": link_count,
		"link_type": "DocType",
		"onboard": 0,
	}


def _workspace_link(label, link_to, link_type):
	return {
		"type": "Link",
		"label": label,
		"link_to": link_to,
		"link_type": link_type,
		"hidden": 0,
		"is_query_report": 1 if link_type == "Report" else 0,
		"link_count": 0,
		"onboard": 0,
	}


def _workspace_row_key(row):
	if row.get("type") == "Card Break":
		return ("Card Break", row.get("label"))
	return ("Link", row.get("label"), row.get("link_to"), row.get("link_type"))


def _clean_workspace_row(row):
	if row.get("type") == "Link" and row.get("link_type") not in VALID_WORKSPACE_LINK_TYPES:
		return None
	allowed = {
		"description",
		"hidden",
		"is_query_report",
		"label",
		"link_count",
		"link_to",
		"link_type",
		"onboard",
		"type",
	}
	cleaned = {key: row.get(key) for key in allowed if row.get(key) is not None}
	if cleaned.get("link_type") == "Report":
		cleaned["is_query_report"] = 1
	return cleaned


def _drop_empty_workspace_cards(rows):
	return [row for row in rows if row.get("type") != "Card Break" or row.get("link_count")]


def _recalculate_workspace_link_counts(rows):
	card_index = None
	for index, row in enumerate(rows):
		if row.get("type") == "Card Break":
			card_index = index
			row["link_count"] = 0
		elif row.get("type") == "Link" and card_index is not None:
			rows[card_index]["link_count"] = rows[card_index].get("link_count", 0) + 1


def sync_doctype(doctype_def):
	name = doctype_def["name"]
	if frappe.db.exists("DocType", name):
		doc = frappe.get_doc("DocType", name)
		update_doctype(doc, doctype_def)
		doc.save(ignore_permissions=True, ignore_version=True)
		return

	doc = frappe.get_doc(doctype_def)
	doc.flags.ignore_version = True
	doc.insert(ignore_permissions=True)


def update_doctype(doc, doctype_def):
	for key, value in doctype_def.items():
		if key in {"doctype", "fields", "permissions"}:
			continue
		setattr(doc, key, value)

	existing_fields = {row.fieldname: row for row in doc.fields}
	for field_def in doctype_def.get("fields", []):
		existing = existing_fields.get(field_def["fieldname"])
		if existing:
			for key, value in field_def.items():
				setattr(existing, key, value)
		else:
			doc.append("fields", field_def)

	if doctype_def.get("field_order"):
		# ترتيب الحقول في Frappe مصدره idx في جدول الحقول، لا الحقل field_order،
		# لذا تُعاد الفهرسة هنا حتى تظهر الحقول الجديدة في مواضعها المعلنة لا في نهاية النموذج.
		declared_order = {fieldname: index for index, fieldname in enumerate(doctype_def["field_order"])}
		trailing = len(declared_order)
		doc.fields.sort(key=lambda row: declared_order.get(row.fieldname, trailing))
		for index, row in enumerate(doc.fields, start=1):
			row.idx = index
		doc.field_order = doctype_def["field_order"]

	if doctype_def.get("permissions") is not None:
		sync_permissions(doc, doctype_def.get("permissions", []))


def sync_permissions(doc, permission_defs):
	allowed_roles = {permission_def.get("role") for permission_def in permission_defs if permission_def.get("role")}
	for row in list(doc.permissions):
		if row.role not in allowed_roles:
			doc.remove(row)

	existing = {row.role: row for row in doc.permissions}
	for permission_def in permission_defs:
		role = permission_def.get("role")
		if not role:
			continue
		row = existing.get(role)
		if not row:
			row = doc.append("permissions", {"role": role})
		for key in PERMISSION_FLAGS:
			setattr(row, key, cint(permission_def.get(key, 0)))


def sync_custom_fields():
	for doctype, fields in CUSTOM_FIELDS.items():
		if not frappe.db.exists("DocType", doctype):
			continue
		for field_def in fields:
			fieldname = field_def["fieldname"]
			custom_field_name = f"{doctype}-{fieldname}"
			values = dict(field_def)
			values.update({"doctype": "Custom Field", "dt": doctype})
			if frappe.db.exists("Custom Field", custom_field_name):
				continue
			else:
				values["name"] = custom_field_name
				frappe.get_doc(values).insert(ignore_permissions=True)


SAUDI_ONLY_PROFESSION_DEFAULTS = [
	("SOP-01", "كبير إداريي موارد بشرية", "Human Resources Senior Administrator", "Human Resources / الموارد البشرية"),
	("SOP-02", "مدير شؤون موظفين", "Personnel Affairs Manager", "Human Resources / الموارد البشرية"),
	("SOP-03", "مدير شؤون عمل وعمال", "Labor and Workers Affairs Manager", "Human Resources / الموارد البشرية"),
	("SOP-04", "مدير علاقات أفراد", "Personnel Relations Manager", "Human Resources / الموارد البشرية"),
	("SOP-05", "اختصاصي شؤون أفراد", "Personnel Affairs Specialist", "Human Resources / الموارد البشرية"),
	("SOP-06", "كاتب شؤون أفراد", "Personnel Affairs Clerk", "Human Resources / الموارد البشرية"),
	("SOP-07", "كاتب توظيف", "Recruitment Clerk", "Human Resources / الموارد البشرية"),
	("SOP-08", "كاتب شؤون موظفين", "Employee Affairs Clerk", "Human Resources / الموارد البشرية"),
	("SOP-09", "كاتب دوام", "Timekeeping Clerk", "Administrative Support / الدعم الإداري"),
	("SOP-10", "كاتب استقبال عام", "General Receptionist", "Reception and Front Office / الاستقبال"),
	("SOP-11", "كاتب استقبال فندقي", "Hotel Receptionist", "Reception and Front Office / الاستقبال"),
	("SOP-12", "كاتب استقبال مرضى", "Patient Receptionist", "Reception and Front Office / الاستقبال"),
	("SOP-13", "كاتب شكاوى", "Complaints Clerk", "Administrative Support / الدعم الإداري"),
	("SOP-14", "أمين صندوق", "Cashier", "Administrative Support / الدعم الإداري"),
	("SOP-15", "حارس أمن خاص", "Private Security Guard", "Security and Guarding / الأمن والحراسة"),
	("SOP-16", "معقب", "Government Transactions Agent (Mu'aqqib)", "Administrative Support / الدعم الإداري"),
	("SOP-17", "ناسخ أو مصلّح مفاتيح", "Key Cutter or Repairer", "Other Restricted / مهن مقصورة أخرى"),
	("SOP-18", "مخلّص جمركي", "Customs Clearance Agent", "Other Restricted / مهن مقصورة أخرى"),
]


# المادة (29): محتويات خزانة الإسعافات الطبية والحد الأدنى للكميات
FIRST_AID_CABINET_ITEMS = [
	("شاش حروق / Burn gauze", 50, "قطعة / piece"),
	("ضمادات إسفنجية / Sponge dressings", 10, "قطع / pieces"),
	("قطع شاش للتنظيف / Cleaning gauze pieces", 50, "قطعة / piece"),
	("قطع شاش معقم 10×10 / Sterile gauze 10x10", 50, "قطعة / piece"),
	("قطع شاش 5×5 / Gauze 5x5", 50, "قطعة / piece"),
	("أربطة شاش 5×5 / Gauze bandages 5x5", 10, "أربطة / bandages"),
	("تورنيكيت / Tourniquet", 1, "قطعة / piece"),
	("أربطة ضاغطة مقاسات مختلفة / Compression bandages, assorted sizes", 10, "أربطة / bandages"),
	("مسحات طبية / Medical swabs", 100, "قطعة / piece"),
	("لفات بلاستر / Plaster rolls", 5, "لفات / rolls"),
	("قطع بلاستر معقمة / Sterile plaster strips", 20, "قطعة / piece"),
	("قفازات معقمة / Sterile gloves", 20, "قفاز / glove"),
	("كمامات للفم / Face masks", 10, "كمامات / masks"),
	("محلول لغسيل العين / Eye wash solution", 1, "عبوة / pack"),
	("نقالة مريض قابلة للطي / Foldable patient stretcher", 1, "قطعة / piece"),
	("محلول مطهر للجروح / Wound antiseptic solution", 1, "عبوة / pack"),
	("طقم ممرات هوائية / Airway set", 1, "طقم / set"),
	("جبائر للفخذ والساق والساعد / Splints for thigh, leg and forearm", 1, "طقم / set"),
	("لوح صلب لإصابات العمود الفقري / Spinal board", 1, "قطعة / piece"),
	("طقم جبائر عنقية لإصابات الرقبة / Cervical collar set", 1, "طقم / set"),
	("مقص بالحجم المناسب / Scissors, suitable size", 2, "قطعة / piece"),
	("بطانية حجم كبير / Large blanket", 1, "قطعة / piece"),
	("ملقط بالحجم المناسب / Forceps, suitable size", 2, "قطعة / piece"),
]


# المادة (32): الأعمال التي يحظر تشغيل الحدث فيها
JUVENILE_PROHIBITED_WORK_DEFAULTS = [
	(
		"JPW-01",
		"العمل في المناجم، أو المحاجر، أو استخراج المواد المعدنية من تحت الأرض",
		"Work in mines, quarries, or underground extraction of mineral materials",
		"Safety / السلامة",
		"منجم,مناجم,محجر,محاجر,تعدين,استخراج المواد المعدنية,تحت الأرض,mine,mining,quarry,underground,mineral extraction",
	),
	(
		"JPW-02",
		"الصناعات ذات المخاطر الصحية",
		"Industries involving health hazards",
		"Health / صحي",
		"مخاطر صحية,مواد كيميائية,كيماويات,إشعاع,أسبستوس,رصاص,مبيدات,أبخرة سامة,health hazard,chemical,radiation,asbestos,lead,pesticide,toxic",
	),
	(
		"JPW-03",
		"الأعمال الشاقة",
		"Arduous work",
		"Physical / جسدي",
		"أعمال شاقة,عمل شاق,رفع أحمال,حمل أثقال,مجهود بدني شديد,arduous,heavy lifting,strenuous,hard labour,hard labor",
	),
	(
		"JPW-04",
		"الأعمال التي قد تعرض الحدث لمخاطر جسدية بسبب العمل على الآلات ذات المخاطر العالية مثل آلات القطع الحادة",
		"Work exposing the juvenile to physical risk from high-risk machinery such as sharp cutting machines",
		"Physical / جسدي",
		"آلات القطع,قطع حاد,منشار,مقصلة,مخرطة,آلات ذات مخاطر عالية,معدات ثقيلة,cutting machine,saw,lathe,press machine,high-risk machinery",
	),
	(
		"JPW-05",
		"أي عمل قد يؤدي مكان وظروف أدائه إلى تعريض الحدث للمشكلات الأخلاقية، والنفسية، والجسدية",
		"Any work whose place or conditions may expose the juvenile to moral, psychological, or physical harm",
		"Moral / أخلاقي",
		"ملاهي,أماكن ترفيه ليلية,بيئة غير أخلاقية,ضغط نفسي,عمل منفرد ليلاً,nightclub,gambling,morally hazardous,psychological harm",
	),
]


# المادة (23): حدود ساعات العمل الفعلية لفئات المادة (108) من النظام
SPECIAL_WORKING_HOURS_LIMITS = {
	"Standard / عمل اعتيادي": {"daily": 8, "ramadan_daily": 6},
	"Preparatory or Complementary / أعمال تجهيزية أو تكميلية": {"daily": 8, "ramadan_daily": 6},
	"Intermittent by Necessity / عمل متقطع بالضرورة": {"daily": 10, "ramadan_daily": 8},
	"Guarding / عمال الحراسة": {"daily": 12, "ramadan_daily": 10},
	"Cleaning / عمال النظافة": {"daily": 12, "ramadan_daily": 10},
}

EXEMPT_WORK_CATEGORY = "Senior Management / مناصب عالية ذات مسؤولية"
PREPARATORY_CATEGORY = "Preparatory or Complementary / أعمال تجهيزية أو تكميلية"
INTERMITTENT_CATEGORY = "Intermittent by Necessity / عمل متقطع بالضرورة"
GUARDING_CATEGORY = "Guarding / عمال الحراسة"
CLEANING_CATEGORY = "Cleaning / عمال النظافة"

MAX_PREPARATORY_MINUTES = 15
MAX_COMPLEMENTARY_MINUTES = 15
MAX_ADDED_MINUTES = 30
MIN_INTERMITTENT_REST_HOURS = 10
MAX_CLEANING_CONSECUTIVE_HOURS = 6
JUVENILE_MINIMUM_AGE = 15
JUVENILE_MAXIMUM_AGE = 18
JUVENILE_EDUCATION_EXCEPTION_MIN_AGE = 14

# المادة (35): شروط استثناء التعليم والتدريب الواردة في المادة (167) من النظام
EDUCATION_EXCEPTION_CONDITIONS = [
	("edu_direct_supervision", "إشراف مباشر من الجهة المسؤولة عن النشاط"),
	("edu_gradual_method", "أن يكون التعليم أو التدريب بأسلوب متدرج لا يشكل صعوبة على المتدرب"),
	("edu_no_academic_impact", "ألا يعوق التعليم والتدريب التحصيل الدراسي"),
	("edu_not_hazardous", "ألا تكون من الأعمال الخطرة المنصوص عليها في المادة (161) من النظام"),
	("edu_authority_approval", "موافقة الوزارة والجهة المرخِّصة للنشاط"),
]


def get_missing_education_exception_conditions(doc):
	"""الشروط غير المستوفاة لاستثناء التعليم والتدريب — المادة (35)."""
	return [label for fieldname, label in EDUCATION_EXCEPTION_CONDITIONS if not cint(doc.get(fieldname))]


def ensure_compliance_default_rows():
	ensure_disciplinary_violation_catalog()
	ensure_disability_accommodation_catalog()
	ensure_saudi_only_professions()
	ensure_juvenile_prohibited_work()


def ensure_juvenile_prohibited_work():
	if not frappe.db.exists("DocType", "Juvenile Prohibited Work"):
		return

	for code, name_ar, name_en, hazard_type, keywords in JUVENILE_PROHIBITED_WORK_DEFAULTS:
		if frappe.db.exists("Juvenile Prohibited Work", {"work_code": code}):
			continue
		frappe.get_doc(
			{
				"doctype": "Juvenile Prohibited Work",
				"naming_series": "SAU-JPW-.YYYY.-.####",
				"work_code": code,
				"work_name_ar": name_ar,
				"work_name_en": name_en,
				"hazard_type": hazard_type,
				"keywords": keywords,
				"active": 1,
				"legal_reference": "Executive Regulations Art.32 (Labor Law Art.161)",
				"source_page": "23",
			}
		).insert(ignore_permissions=True)


def match_juvenile_prohibited_work(description):
	"""ترجع اسم العمل المحظور على الأحداث المطابق للوصف، أو None — المادة (32)."""
	text = (description or "").strip().lower()
	if not text or not frappe.db.exists("DocType", "Juvenile Prohibited Work"):
		return None

	for row in frappe.get_all(
		"Juvenile Prohibited Work",
		filters={"active": 1},
		fields=["work_name_ar", "keywords"],
		order_by="work_code",
	):
		for keyword in (row.keywords or "").split(","):
			keyword = keyword.strip().lower()
			if keyword and keyword in text:
				return row.work_name_ar
	return None


def get_special_working_hours_limits(work_category, is_ramadan=0, worker_is_muslim=1):
	"""حدود الساعات اليومية والأسبوعية وفق المادة (23). ترجع None للفئة المستثناة."""
	if work_category == EXEMPT_WORK_CATEGORY:
		return None

	limits = SPECIAL_WORKING_HOURS_LIMITS.get(work_category)
	if not limits:
		limits = SPECIAL_WORKING_HOURS_LIMITS["Standard / عمل اعتيادي"]

	ramadan = cint(is_ramadan)
	muslim = cint(worker_is_muslim)
	# التخفيض اليومي في رمضان مقرر للعمال المسلمين
	daily = limits["ramadan_daily"] if (ramadan and muslim) else limits["daily"]
	weekly = 36 if (ramadan and muslim) else 48
	return {"daily": daily, "weekly": weekly}


def evaluate_special_working_hours(doc):
	"""تطبيق ضوابط المادة (23) على فحص امتثال ساعات العمل."""
	category = doc.work_category or "Standard / عمل اعتيادي"
	breaches = []

	limits = get_special_working_hours_limits(category, doc.is_ramadan, doc.worker_is_muslim)

	prep = flt(doc.preparatory_minutes)
	comp = flt(doc.complementary_minutes)
	doc.total_added_minutes = round(prep + comp, 2)

	if category == PREPARATORY_CATEGORY or prep or comp:
		if prep > MAX_PREPARATORY_MINUTES:
			breaches.append(f"الأعمال التجهيزية {prep:g} دقيقة تتجاوز {MAX_PREPARATORY_MINUTES} دقيقة")
		if comp > MAX_COMPLEMENTARY_MINUTES:
			breaches.append(f"الأعمال التكميلية {comp:g} دقيقة تتجاوز {MAX_COMPLEMENTARY_MINUTES} دقيقة")
		if doc.total_added_minutes > MAX_ADDED_MINUTES:
			breaches.append(f"مجموع الوقت المضاف {doc.total_added_minutes:g} دقيقة يتجاوز {MAX_ADDED_MINUTES} دقيقة")

	if category == GUARDING_CATEGORY and cint(doc.is_civil_or_industrial_security):
		breaches.append("الحراسات الأمنية المدنية والصناعية لا تدخل في تعريف عمال الحراسة بالمادة (23/4)")

	if category == CLEANING_CATEGORY and flt(doc.max_consecutive_hours) > MAX_CLEANING_CONSECUTIVE_HOURS:
		breaches.append(
			f"عمل النظافة المتوالي {flt(doc.max_consecutive_hours):g} ساعة يتجاوز {MAX_CLEANING_CONSECUTIVE_HOURS} ساعات المقررة بالمادة (23/5)"
		)

	if category == INTERMITTENT_CATEGORY and flt(doc.continuous_rest_hours) < MIN_INTERMITTENT_REST_HOURS:
		breaches.append(
			f"الراحة المتواصلة {flt(doc.continuous_rest_hours):g} ساعة أقل من {MIN_INTERMITTENT_REST_HOURS} ساعات خلال كل 24 ساعة"
		)

	if category in {INTERMITTENT_CATEGORY, GUARDING_CATEGORY, CLEANING_CATEGORY} and not cint(doc.prayer_time_enabled):
		breaches.append("يجب تمكين العمال من أداء الصلوات في أوقاتها")

	if limits is None:
		doc.standard_daily_hours = 0
		doc.standard_weekly_hours = 0
		doc.overtime_hours = 0
		doc.breach_summary = "\n".join(breaches) or None
		doc.status = "Category Control Breach / مخالفة ضوابط الفئة" if breaches else "Exempt Category / فئة مستثناة"
		return

	doc.standard_daily_hours = limits["daily"]
	doc.standard_weekly_hours = limits["weekly"]

	daily_excess = max(0, flt(doc.actual_daily_hours) - limits["daily"])
	weekly_excess = max(0, flt(doc.actual_weekly_hours) - limits["weekly"])
	# ما زاد على الحد يحتسب عملاً إضافياً — المادة (23/7) و(23/8)
	doc.overtime_hours = round(max(daily_excess, weekly_excess), 2)

	doc.breach_summary = "\n".join(breaches) or None

	if breaches:
		doc.status = "Category Control Breach / مخالفة ضوابط الفئة"
	elif category == "Standard / عمل اعتيادي":
		# العمل الاعتيادي يظل خاضعاً لضوابط المادتين (98) و(106) بسقفها المطلق
		doc.status = evaluate_working_time_status(
			doc.actual_daily_hours,
			doc.actual_weekly_hours,
			limits["daily"],
			limits["weekly"],
			doc.approval_reference,
		)
	elif doc.approval_reference:
		doc.status = "Exception Approved / استثناء معتمد"
	elif daily_excess:
		doc.status = "Daily Limit Exceeded / تجاوز الحد اليومي"
	elif weekly_excess:
		doc.status = "Weekly Limit Exceeded / تجاوز الحد الأسبوعي"
	else:
		doc.status = "Compliant / ممتثل"


def calculate_juvenile_age(date_of_birth, reference_date=None):
	if not date_of_birth:
		return None
	birth = getdate(date_of_birth)
	reference = getdate(reference_date or today())
	return round(date_diff(reference, birth) / 365.25, 2)


def evaluate_juvenile_controls(doc):
	"""ضوابط تشغيل الأحداث — المواد (32) و(33) و(34) من اللائحة."""
	doc.minimum_age_breach = 0
	doc.prohibited_work_breach = 0
	doc.night_work_breach = 0
	doc.matched_prohibited_work = None
	doc.juvenile_breach_summary = None

	if doc.category != "Young Worker / عامل حدث":
		doc.age_years = None
		return

	age = calculate_juvenile_age(doc.date_of_birth)
	doc.age_years = age
	breaches = []

	if age is None:
		doc.juvenile_breach_summary = "تاريخ ميلاد الحدث غير مسجل — يتعذر تطبيق ضوابط المواد (32) و(33) و(34)."
		doc.status = "Needs Review / يحتاج مراجعة"
		return

	matched = match_juvenile_prohibited_work(doc.assigned_work_description) if age < JUVENILE_MAXIMUM_AGE else None

	# شرط «ألا تكون من الأعمال الخطرة» لا يمكن أن يستوفى وقد طابق العمل دليل المحظورات
	if matched and cint(doc.get("edu_not_hazardous")):
		doc.edu_not_hazardous = 0

	missing_conditions = get_missing_education_exception_conditions(doc)
	doc.education_exception_valid = (
		1
		if cint(doc.education_exception_applies)
		and not missing_conditions
		and age >= JUVENILE_EDUCATION_EXCEPTION_MIN_AGE
		else 0
	)

	if cint(doc.education_exception_applies):
		if age < JUVENILE_EDUCATION_EXCEPTION_MIN_AGE:
			breaches.append(
				f"استثناء التعليم والتدريب لا يسري على من لم يبلغ الرابعة عشرة — العمر {age:g} سنة (المادة 167)"
			)
		elif missing_conditions:
			breaches.append(
				"استثناء التعليم والتدريب غير مستوفٍ لشروط المادة (35): " + "؛ ".join(missing_conditions)
			)

	if age < JUVENILE_MINIMUM_AGE and not cint(doc.education_exception_valid):
		doc.minimum_age_breach = 1
		breaches.append(
			f"العمر {age:g} سنة دون الخامسة عشرة — لا يجوز التشغيل ولا دخول أماكن العمل (المادة 33)"
		)

	if age < JUVENILE_MAXIMUM_AGE:
		if matched:
			doc.matched_prohibited_work = matched
			doc.prohibited_work_breach = 1
			breaches.append(f"العمل المسند يقع ضمن الأعمال المحظورة على الأحداث: {matched} (المادة 32)")

		doc.night_work_restriction = 1
		if cint(doc.night_shift_assigned) and doc.night_work_exception in (
			None,
			"",
			"None / لا يوجد",
		):
			doc.night_work_breach = 1
			breaches.append(
				"تشغيل ليلي دون استثناء نظامي — يحظر التشغيل مدة لا تقل عن اثنتي عشرة ساعة متتالية ليلاً (المادة 34)"
			)

		if not doc.daily_hours_limit:
			doc.daily_hours_limit = 6

	doc.juvenile_breach_summary = "\n".join(breaches) or None
	if breaches:
		doc.status = "Restriction Breach / مخالفة قيد"
	elif doc.status in {"Draft / مسودة", "Needs Review / يحتاج مراجعة"}:
		doc.status = "Compliant / ممتثل"


def ensure_saudi_only_professions():
	if not frappe.db.exists("DocType", "Saudi Only Profession"):
		return

	for code, name_ar, name_en, group in SAUDI_ONLY_PROFESSION_DEFAULTS:
		if frappe.db.exists("Saudi Only Profession", {"profession_code": code}):
			continue
		frappe.get_doc(
			{
				"doctype": "Saudi Only Profession",
				"naming_series": "SAU-SOP-.YYYY.-.####",
				"profession_code": code,
				"profession_name_ar": name_ar,
				"profession_name_en": name_en,
				"profession_group": group,
				"active": 1,
				"blocks_expat_assignment": 1,
				"includes_indirect_assignment": 1,
				"legal_reference": "Executive Regulations Art.11 (Labor Law Art.36)",
				"source_page": "6",
			}
		).insert(ignore_permissions=True)


def match_saudi_only_profession(designation):
	"""ترجع اسم المهنة المقصورة على السعوديين المطابقة، أو None — المادة (11)."""
	title = (designation or "").strip().lower()
	if not title or not frappe.db.exists("DocType", "Saudi Only Profession"):
		return None

	for row in frappe.get_all(
		"Saudi Only Profession",
		filters={"active": 1, "blocks_expat_assignment": 1},
		fields=["profession_name_ar", "profession_name_en"],
	):
		for candidate in (row.profession_name_ar, row.profession_name_en):
			if candidate and candidate.strip().lower() in title:
				return row.profession_name_ar or candidate
	return None


def is_saudi_only_profession(designation):
	"""ترجع True إذا كانت المهنة مقصورة على السعوديين وفق المادة (11)."""
	return match_saudi_only_profession(designation) is not None


def flag_saudi_only_profession(doc):
	"""رصد إسناد مهنة مقصورة على السعوديين لعامل غير سعودي — المادة (11)."""
	doc.matched_saudi_only_profession = None
	doc.restricted_profession_breach = 0

	designation = doc.get("target_profession")
	if not designation and doc.get("employee"):
		designation = frappe.db.get_value("Employee", doc.employee, "designation")
	if not designation:
		return

	matched = match_saudi_only_profession(designation)
	if not matched:
		return

	doc.matched_saudi_only_profession = matched
	if doc.get("employee") and is_saudi_nationality(get_employee_nationality(doc.employee)):
		return

	doc.restricted_profession_breach = 1
	frappe.msgprint(
		_(
			"Profession <b>{0}</b> is restricted to Saudi nationals under Executive Regulations Art.11, "
			"so it cannot be assigned to a non-Saudi worker under any job title.<br>"
			"المهنة <b>{0}</b> مقصورة على السعوديين بموجب المادة (11) من اللائحة التنفيذية، "
			"ولا يجوز إسنادها لعامل غير سعودي تحت أي مسمى وظيفي."
		).format(matched),
		title=_("Restricted Occupation / مهنة مقصورة"),
		indicator="red",
	)


def load_standard_first_aid_items(doc):
	"""تعبئة الجدول بالحد الأدنى النظامي لمحتويات خزانة الإسعافات — المادة (29)."""
	for item_name, quantity, unit in FIRST_AID_CABINET_ITEMS:
		doc.append(
			"items",
			{
				"item_name": item_name,
				"required_quantity": quantity,
				"unit": unit,
				"available_quantity": 0,
				"status": "Missing / ناقص",
			},
		)


def calculate_first_aid_cabinet(doc):
	"""حساب النقص في خزانة الإسعافات ونسبة الاكتمال — المادة (29)."""
	if not doc.get("items"):
		load_standard_first_aid_items(doc)

	shortage_items = 0
	for row in doc.get("items") or []:
		required = flt(row.required_quantity)
		available = flt(row.available_quantity)
		row.shortage_quantity = max(0, round(required - available, 2))
		expired = bool(row.expiry_date) and getdate(row.expiry_date) < getdate(today())
		if expired:
			row.status = "Expired / منتهي"
		elif available <= 0:
			row.status = "Missing / ناقص"
		elif row.shortage_quantity > 0:
			row.status = "Needs Restock / يحتاج تعويض"
		else:
			row.status = "Sufficient / مكتمل"
		if row.status != "Sufficient / مكتمل":
			shortage_items += 1

	total_rows = len(doc.get("items") or [])
	doc.total_shortage_items = shortage_items

	condition_flags = [
		cint(doc.storage_conditions_met),
		cint(doc.red_crescent_marked),
		cint(doc.location_signage_posted),
		cint(doc.responsible_name_posted),
	]
	compliant_units = (total_rows - shortage_items) + sum(condition_flags)
	total_units = total_rows + len(condition_flags)
	doc.compliance_score = round((compliant_units / total_units) * 100, 2) if total_units else 0

	if not total_rows:
		doc.status = "Draft / مسودة"
	elif shortage_items == 0 and all(condition_flags):
		doc.status = "Compliant / ممتثل"
	elif shortage_items:
		doc.status = "Restock Required / يحتاج تعويض"
	else:
		doc.status = "Non-Compliant / غير ممتثل"


REMOTE_SITE_OBLIGATION_FIELDS = [
	"shops_provided",
	"recreation_provided",
	"medical_care_provided",
	"schools_provided",
	"mosques_provided",
	"literacy_programs_provided",
]


def classify_remote_area(road_type, distance_km, lacks_facilities_settlement):
	"""المادة (30): >50 كم بطريق معبد أو >25 كم بطريق غير معبد أو تجمع تنقصه المرافق."""
	if cint(lacks_facilities_settlement):
		return True
	distance = flt(distance_km)
	if road_type == "Paved / معبد":
		return distance > 50
	if road_type == "Unpaved / غير معبد":
		return distance > 25
	return False


def calculate_remote_work_site(doc):
	"""تصنيف الموقع وحساب نسبة استيفاء التزامات المادة (146) من النظام."""
	doc.is_remote_area = 1 if classify_remote_area(
		doc.road_type, doc.distance_km, doc.lacks_facilities_settlement
	) else 0

	met = sum(cint(doc.get(fieldname)) for fieldname in REMOTE_SITE_OBLIGATION_FIELDS)
	doc.obligations_met = met
	total = len(REMOTE_SITE_OBLIGATION_FIELDS)
	doc.compliance_score = round((met / total) * 100, 2)

	if not doc.is_remote_area:
		doc.status = "Not Applicable / غير منطبق"
	elif met == total:
		doc.status = "Compliant / ممتثل"
	elif met:
		doc.status = "Partially Compliant / ممتثل جزئياً"
	else:
		doc.status = "Non-Compliant / غير ممتثل"


def ensure_disciplinary_violation_catalog():
	if not frappe.db.exists("DocType", "Disciplinary Violation Catalog"):
		return

	for code, category, name, first, second, third, fourth, source_page in DISCIPLINARY_CATALOG_DEFAULTS:
		if frappe.db.exists("Disciplinary Violation Catalog", {"violation_code": code}):
			continue
		frappe.get_doc(
			{
				"doctype": "Disciplinary Violation Catalog",
				"naming_series": "SAU-DVC-.YYYY.-.####",
				"violation_code": code,
				"violation_name": name,
				"category": category,
				"status": "Active / نشط",
				"penalty_first": first,
				"penalty_second": second,
				"penalty_third": third,
				"penalty_fourth": fourth,
				"requires_termination_review": 1 if "Termination" in fourth or "Termination" in first else 0,
				"legal_reference": "Annex 1 - Unified Work Regulation Violation Table",
				"source_page": str(source_page),
			}
		).insert(ignore_permissions=True)


def ensure_disability_accommodation_catalog():
	if not frappe.db.exists("DocType", "Disability Accommodation Catalog"):
		return

	for code, disability_type, job_family, title, details, source_page in DISABILITY_ACCOMMODATION_DEFAULTS:
		if frappe.db.exists("Disability Accommodation Catalog", {"accommodation_code": code}):
			continue
		frappe.get_doc(
			{
				"doctype": "Disability Accommodation Catalog",
				"naming_series": "SAU-DAC-.YYYY.-.####",
				"accommodation_code": code,
				"disability_type": disability_type,
				"job_family": job_family,
				"accommodation_title": title,
				"priority": "Recommended / موصى به",
				"requirement_details": details,
				"evidence_required": "Medical/disability certificate, workplace review, and implementation evidence.",
				"legal_reference": "Annex 2 - Accommodation and Facilitation Table",
				"source_page": source_page,
				"active": 1,
			}
		).insert(ignore_permissions=True)


def calculate_disability_ratio(doc):
	total = flt(doc.total_employees)
	disabled = flt(doc.disabled_employees)
	doc.compliance_ratio = round((disabled / total) * 100, 2) if total else 0
	required_count = (total * flt(doc.required_ratio or 4)) / 100
	doc.gap_to_required = max(0, round(required_count - disabled, 2))

	if total and total < 25:
		doc.status = "Not Applicable / غير منطبق"
	elif doc.compliance_ratio >= flt(doc.required_ratio or 4):
		doc.status = "Compliant / ممتثل"
	elif doc.status not in {"Needs Accommodation Review / يحتاج مراجعة التسهيلات"}:
		doc.status = "Below Required Ratio / أقل من النسبة المطلوبة"


def get_final_settlement_days(termination_initiated_by):
	return 7 if termination_initiated_by == "Employer / صاحب العمل" else 14


def derive_termination_initiator(termination_reason):
	reason = termination_reason or ""
	if "Resignation by Employee" in reason or "استقالة الموظف" in reason:
		return "Employee / الموظف"
	if "Termination by Employer" in reason or "Dismissal Without Notice" in reason or "صاحب العمل" in reason or "فصل فوري" in reason:
		return "Employer / صاحب العمل"
	return "Needs Review / يحتاج مراجعة"


def calculate_compensatory_leave_exit_payout(unused_hours, actual_hourly_wage):
	hours = max(0, flt(unused_hours))
	rate = max(0, flt(actual_hourly_wage))
	return round(hours * rate, 2)


def calculate_final_settlement_dates(doc):
	doc.termination_initiated_by = doc.termination_initiated_by or "Needs Review / يحتاج مراجعة"
	if doc.last_working_day:
		applicable_days = get_final_settlement_days(doc.termination_initiated_by)
		doc.settlement_due_date = add_days(
			doc.last_working_day,
			applicable_days,
		)
		doc.document_return_due_date = add_days(doc.last_working_day, applicable_days)
	if doc.termination_initiated_by == "Needs Review / يحتاج مراجعة":
		doc.legal_review_required = 1

	unused_hours = flt(doc.unused_compensatory_leave_hours)
	doc.compensatory_leave_payout_amount = calculate_compensatory_leave_exit_payout(
		unused_hours,
		doc.actual_hourly_wage_for_leave,
	)
	doc.compensatory_leave_review_required = cint(
		unused_hours > 0 and flt(doc.actual_hourly_wage_for_leave) <= 0
	)
	if doc.compensatory_leave_review_required:
		doc.legal_review_required = 1
	if (
		doc.status == "Settled / تمت التسوية"
		and unused_hours > 0
		and not doc.compensatory_leave_payout_evidence
	):
		frappe.throw(
			_("Attach evidence of paying the unused compensatory-leave balance before closing the settlement.<br>"
			  "أرفق إثبات دفع رصيد الإجازة التعويضية غير المستخدم قبل إغلاق التسوية."),
			title=_("Payout Evidence Required / إثبات الدفع مطلوب"),
		)

	if doc.status in {"Settled / تمت التسوية", "Cancelled / ملغى"}:
		return
	if doc.settlement_due_date and getdate(doc.settlement_due_date) < getdate(today()):
		doc.status = "Overdue / متأخر"


def calculate_flexible_work_limits(monthly_hours):
	hours = max(0, flt(monthly_hours))
	return {
		"overtime_hours": round(max(0, hours - 95), 2),
		"maximum_exceeded": hours > 160,
		"nitaqat_credit": 1 if hours >= 160 else 0,
		"paid_leave_entitled": False,
		"eosb_entitled": False,
		"probation_applicable": False,
		"overtime_at_base_hourly_rate": True,
	}


def calculate_work_arrangement_dates(doc):
	if doc.start_date and doc.end_date:
		doc.actual_days = max(0, (getdate(doc.end_date) - getdate(doc.start_date)).days + 1)

	if doc.arrangement_type in {"Temporary Work / العمل المؤقت", "Casual Work / العمل العرضي"}:
		doc.conversion_due_date = add_days(doc.start_date, 90) if doc.start_date else None
		doc.conversion_required = 1 if flt(doc.actual_days) > 90 else 0
		if doc.conversion_required and doc.status not in {"Closed / مغلق", "Cancelled / ملغى"}:
			doc.status = "Needs Conversion / يحتاج تحويل"

	if doc.arrangement_type == "Flexible Work / العمل المرن":
		doc.saudi_only_applicable = 1
		doc.compensatory_leave_allowed = 0
		doc.flexible_overtime_threshold = 95
		doc.flexible_monthly_maximum = 160
		limits = calculate_flexible_work_limits(doc.monthly_hours)
		doc.flexible_overtime_hours = limits["overtime_hours"]
		doc.flexible_nitaqat_credit = limits["nitaqat_credit"]
		doc.paid_leave_entitled = cint(limits["paid_leave_entitled"])
		doc.eosb_entitled = cint(limits["eosb_entitled"])
		doc.probation_applicable = cint(limits["probation_applicable"])
		doc.flexible_overtime_at_base_rate = cint(limits["overtime_at_base_hourly_rate"])
		doc.flexible_contract_max_end_date = add_months(doc.start_date, 12) if doc.start_date else None
		duration_exceeded = bool(
			doc.end_date
			and doc.flexible_contract_max_end_date
			and getdate(doc.end_date) > getdate(doc.flexible_contract_max_end_date)
		)
		doc.regular_contract_conversion_required = cint(duration_exceeded)
		doc.renewal_requires_worker_consent = cint(doc.is_renewal_or_extension)
		nationality = get_employee_nationality(doc.employee)
		requires_review = (
			(not is_saudi_nationality(nationality))
			or limits["maximum_exceeded"]
			or duration_exceeded
			or (doc.is_renewal_or_extension and not (doc.worker_renewal_consent_reference or "").strip())
			or (doc.status == "Active / نشط" and not doc.platform_reference)
		)
		if requires_review and doc.status not in {"Closed / مغلق", "Cancelled / ملغى"}:
			doc.status = "Needs Review / يحتاج مراجعة"


def evaluate_working_time_status(actual_daily_hours, actual_weekly_hours, standard_daily_hours=8, standard_weekly_hours=48, approval_reference=None):
	daily = flt(actual_daily_hours)
	weekly = flt(actual_weekly_hours)
	if daily > 10:
		return "Daily Limit Exceeded / تجاوز الحد اليومي"
	if weekly > 60:
		return "Weekly Limit Exceeded / تجاوز الحد الأسبوعي"
	if daily > flt(standard_daily_hours or 8) or weekly > flt(standard_weekly_hours or 48):
		return "Exception Approved / استثناء معتمد" if approval_reference else "Needs Review / يحتاج مراجعة"
	return "Compliant / ممتثل"


def calculate_working_time_status(doc):
	evaluate_special_working_hours(doc)


def get_holiday_overlap_action(overlap_type):
	return {
		"Weekly Rest / راحة أسبوعية": "Compensate Rest Day / تعويض يوم راحة",
		"Annual Leave / إجازة سنوية": "Extend Leave / تمديد الإجازة",
		"Sick Leave / إجازة مرضية": "Apply Sick Leave Pay Rule / تطبيق أجر المرضية",
	}.get(overlap_type, "Legal Review / مراجعة قانونية")


def calculate_holiday_overlap_action(doc):
	doc.required_action = get_holiday_overlap_action(doc.overlap_type)
	if doc.required_action == "Legal Review / مراجعة قانونية" and doc.status == "Open / مفتوح":
		doc.status = "Legal Review / مراجعة قانونية"


def calculate_statutory_record_counts(doc):
	required_rows = [row for row in doc.records if row.required and row.status != "Not Applicable / غير منطبق"]
	available_rows = [row for row in required_rows if row.status == "Available / متوفر"]
	doc.total_required = len(required_rows)
	doc.completed_count = len(available_rows)
	doc.gap_count = max(0, len(required_rows) - len(available_rows))
	if doc.gap_count:
		doc.status = "Gaps Found / توجد فجوات"
	elif doc.total_required:
		doc.status = "Compliant / ممتثل"


def calculate_inspection_fine_dates(doc):
	if doc.notification_date and not doc.payment_due_date:
		doc.payment_due_date = add_days(doc.notification_date, 60)
	if doc.status in {"Paid / مدفوعة", "Waived / معفاة", "Closed / مغلقة"}:
		return
	if doc.payment_due_date and getdate(doc.payment_due_date) < getdate(today()):
		doc.status = "Overdue / متأخرة"


def calculate_ministry_filing_status(doc):
	if doc.status in {"Accepted / مقبول", "Cancelled / ملغى"}:
		return
	if doc.due_date and getdate(doc.due_date) < getdate(today()):
		doc.status = "Overdue / متأخر"


def apply_disciplinary_catalog_recommendation(doc):
	if not getattr(doc, "violation_catalog", None) or not frappe.db.exists(
		"DocType", "Disciplinary Violation Catalog"
	):
		return

	catalog = frappe.db.get_value(
		"Disciplinary Violation Catalog",
		doc.violation_catalog,
		[
			"penalty_first",
			"penalty_second",
			"penalty_third",
			"penalty_fourth",
			"legal_reference",
			"requires_termination_review",
			"status",
		],
		as_dict=True,
	)
	if not catalog:
		return

	occurrence_number = min(max(cint(doc.occurrence_number or 1), 1), 4)
	penalty_field = {
		1: "penalty_first",
		2: "penalty_second",
		3: "penalty_third",
		4: "penalty_fourth",
	}[occurrence_number]
	doc.recommended_penalty = catalog.get(penalty_field)
	doc.catalog_legal_reference = catalog.get("legal_reference")
	doc.catalog_requires_review = 1 if catalog.get("requires_termination_review") or catalog.get("status") == "Needs Legal Review / يحتاج مراجعة قانونية" else 0


def apply_disability_accommodation_catalog(doc):
	if not frappe.db.exists("DocType", "Disability Accommodation Catalog"):
		return

	for row in getattr(doc, "accommodations", []) or []:
		if not getattr(row, "accommodation_catalog", None):
			continue
		requirement_details = frappe.db.get_value(
			"Disability Accommodation Catalog",
			row.accommodation_catalog,
			"requirement_details",
		)
		if requirement_details:
			row.catalog_requirement_details = requirement_details


def calculate_provider_compliance_status(doc):
	if doc.license_expiry_date and not doc.renewal_due_date:
		doc.renewal_due_date = add_days(doc.license_expiry_date, -60)

	if doc.status in {"Suspended / موقوف", "Closed / مغلق"}:
		return
	if doc.license_expiry_date and getdate(doc.license_expiry_date) < getdate(today()):
		doc.status = "Expired / منتهي"
	elif doc.renewal_due_date and getdate(doc.renewal_due_date) <= getdate(today()) and doc.status == "Active / نشط":
		doc.status = "Renewal Due / يستحق التجديد"


def calculate_provider_complaint_status(doc):
	if doc.received_on and not doc.response_due_date:
		doc.response_due_date = add_days(doc.received_on, 15)

	if doc.status in {"Resolved / معالجة", "Closed / مغلقة"}:
		return
	if doc.response_due_date and getdate(doc.response_due_date) < getdate(today()):
		doc.status = "Overdue / متأخرة"


def calculate_training_agreement_status(doc):
	if doc.training_end_date and doc.commitment_months and not doc.commitment_end_date:
		doc.commitment_end_date = add_months(doc.training_end_date, cint(doc.commitment_months))

	if doc.status in {"Waived / متنازل عنه", "Cancelled / ملغى"}:
		return
	if doc.recovery_applicable and flt(doc.recovery_amount) > 0:
		doc.status = "Recovery Due / يستحق استرداد"
	elif doc.commitment_end_date and getdate(doc.commitment_end_date) < getdate(today()):
		doc.status = "Completed / مكتمل"


def validate_compliance_doc(doc, method=None):
	if doc.doctype == "Disability Employment Compliance":
		calculate_disability_ratio(doc)
		apply_disability_accommodation_catalog(doc)
	elif doc.doctype == "Final Settlement SLA":
		calculate_final_settlement_dates(doc)
	elif doc.doctype == "Work Arrangement Control":
		calculate_work_arrangement_dates(doc)
	elif doc.doctype == "Working Time Compliance Check":
		calculate_working_time_status(doc)
	elif doc.doctype == "Holiday Leave Overlap Rule":
		calculate_holiday_overlap_action(doc)
	elif doc.doctype == "Statutory HR Records Register":
		calculate_statutory_record_counts(doc)
	elif doc.doctype == "Inspection Fine SLA":
		calculate_inspection_fine_dates(doc)
	elif doc.doctype == "Ministry Filing Tracker":
		calculate_ministry_filing_status(doc)
	elif doc.doctype == "Disciplinary Procedure":
		apply_disciplinary_catalog_recommendation(doc)
	elif doc.doctype == "Recruitment Service Provider Compliance":
		calculate_provider_compliance_status(doc)
	elif doc.doctype == "Recruitment Provider Complaint":
		calculate_provider_complaint_status(doc)
	elif doc.doctype == "Training Agreement":
		calculate_training_agreement_status(doc)
	elif doc.doctype == "First Aid Cabinet Register":
		calculate_first_aid_cabinet(doc)
	elif doc.doctype == "Remote Work Site Compliance":
		calculate_remote_work_site(doc)
	elif doc.doctype == "Expat Work Authorization Control":
		flag_saudi_only_profession(doc)
	elif doc.doctype == "Special Employment Category Control":
		evaluate_juvenile_controls(doc)


def create_final_settlement_from_termination(doc, method=None):
	if not frappe.db.exists("DocType", "Final Settlement SLA") or doc.doctype != "Termination Notice":
		return
	if frappe.db.exists("Final Settlement SLA", {"termination_notice": doc.name}):
		return

	termination_initiated_by = derive_termination_initiator(doc.termination_reason)
	applicable_days = get_final_settlement_days(termination_initiated_by)
	settlement_due = add_days(
		doc.notice_end_date,
		applicable_days,
	) if doc.notice_end_date else None
	document_due = add_days(doc.notice_end_date, applicable_days) if doc.notice_end_date else None
	frappe.get_doc(
		{
			"doctype": "Final Settlement SLA",
			"termination_notice": doc.name,
			"employee": doc.employee,
			"company": doc.company,
			"last_working_day": doc.notice_end_date,
			"termination_initiated_by": termination_initiated_by,
			"settlement_due_date": settlement_due,
			"document_return_due_date": document_due,
			"status": "Open / مفتوح",
			"risk_level": "High / مرتفع",
			"legal_review_required": cint(termination_initiated_by == "Needs Review / يحتاج مراجعة"),
			"notes": _("Auto-created from approved Termination Notice {0}.").format(doc.name),
		}
	).insert(ignore_permissions=True)
