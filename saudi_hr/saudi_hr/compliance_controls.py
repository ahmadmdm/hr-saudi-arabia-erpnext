import json

import frappe
from frappe import _
from frappe.utils import add_days, add_months, cint, flt, getdate, today


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


def section(fieldname, label, description=None):
	docfield = field(fieldname, "Section Break", label)
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
			field("status", "Select", "Status / الحالة", options="Draft / مسودة\nActive / نشط\nNeeds Conversion / يحتاج تحويل\nExpired / منتهي\nClosed / مغلق\nCancelled / ملغى", default="Draft / مسودة", in_list_view=1),
			section("period_section", "Period & Limits / المدة والحدود"),
			field("start_date", "Date", "Start Date / تاريخ البداية", reqd=1),
			field("end_date", "Date", "End Date / تاريخ النهاية"),
			field("actual_days", "Int", "Actual Days / الأيام الفعلية", read_only=1),
			column("column_break_2"),
			field("conversion_due_date", "Date", "Conversion Due Date / تاريخ التحول المحتمل"),
			field("conversion_required", "Check", "Conversion Required / يتطلب تحويل", read_only=1),
			field("daily_hours_limit", "Float", "Daily Hours Limit / حد الساعات اليومي"),
			field("weekly_hours_limit", "Float", "Weekly Hours Limit / حد الساعات الأسبوعي"),
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
			section("hours_section", "Hours / الساعات"),
			field("actual_daily_hours", "Float", "Actual Daily Hours / ساعات اليوم الفعلية"),
			field("actual_weekly_hours", "Float", "Actual Weekly Hours / ساعات الأسبوع الفعلية"),
			column("column_break_2"),
			field("overtime_hours", "Float", "Overtime Hours / ساعات العمل الإضافي"),
			field("status", "Select", "Status / الحالة", options="Compliant / ممتثل\nDaily Limit Exceeded / تجاوز الحد اليومي\nWeekly Limit Exceeded / تجاوز الحد الأسبوعي\nException Approved / استثناء معتمد\nNeeds Review / يحتاج مراجعة", default="Needs Review / يحتاج مراجعة", in_list_view=1),
			field("approval_reference", "Link", "Approval Reference / مرجع الاعتماد", options="Overtime Request"),
			field("exception_reason", "Small Text", "Exception Reason / سبب الاستثناء"),
			field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations working-hours controls"),
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
				field("legal_reference", "Data", "Legal Reference / المرجع النظامي", default="Executive Regulations special employment category controls"),
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


CUSTOM_FIELDS = {
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
		],
	},
	{
		"id": "saudi_hr_card_safety_inspection",
		"label": "السلامة والتفتيش والغرامات",
		"links": [
			("Safety Inspection and Risk Control", "Safety Inspection and Risk Control", "DocType"),
			("Inspection Fine SLA", "Inspection Fine SLA", "DocType"),
			("Labor Inspection", "Labor Inspection", "DocType"),
			("Work Injury", "Work Injury", "DocType"),
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
	sync_compliance_workspace()


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


def ensure_compliance_default_rows():
	ensure_disciplinary_violation_catalog()
	ensure_disability_accommodation_catalog()


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


def calculate_final_settlement_dates(doc):
	if doc.last_working_day and not doc.settlement_due_date:
		doc.settlement_due_date = add_days(doc.last_working_day, 14)
	if doc.last_working_day and not doc.document_return_due_date:
		doc.document_return_due_date = add_days(doc.last_working_day, 7)

	if doc.status in {"Settled / تمت التسوية", "Cancelled / ملغى"}:
		return
	if doc.settlement_due_date and getdate(doc.settlement_due_date) < getdate(today()):
		doc.status = "Overdue / متأخر"


def calculate_work_arrangement_dates(doc):
	if doc.start_date and doc.end_date:
		doc.actual_days = max(0, (getdate(doc.end_date) - getdate(doc.start_date)).days + 1)

	if doc.arrangement_type in {"Temporary Work / العمل المؤقت", "Casual Work / العمل العرضي"}:
		doc.conversion_due_date = add_days(doc.start_date, 90) if doc.start_date else None
		doc.conversion_required = 1 if flt(doc.actual_days) > 90 else 0
		if doc.conversion_required and doc.status not in {"Closed / مغلق", "Cancelled / ملغى"}:
			doc.status = "Needs Conversion / يحتاج تحويل"


def calculate_working_time_status(doc):
	if flt(doc.actual_daily_hours) > 10:
		doc.status = "Daily Limit Exceeded / تجاوز الحد اليومي"
	elif flt(doc.actual_weekly_hours) > 60:
		doc.status = "Weekly Limit Exceeded / تجاوز الحد الأسبوعي"
	elif doc.status == "Needs Review / يحتاج مراجعة":
		doc.status = "Compliant / ممتثل"


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


def create_final_settlement_from_termination(doc, method=None):
	if not frappe.db.exists("DocType", "Final Settlement SLA") or doc.doctype != "Termination Notice":
		return
	if frappe.db.exists("Final Settlement SLA", {"termination_notice": doc.name}):
		return

	settlement_due = add_days(doc.notice_end_date, 14) if doc.notice_end_date else None
	document_due = add_days(doc.notice_end_date, 7) if doc.notice_end_date else None
	frappe.get_doc(
		{
			"doctype": "Final Settlement SLA",
			"termination_notice": doc.name,
			"employee": doc.employee,
			"company": doc.company,
			"last_working_day": doc.notice_end_date,
			"settlement_due_date": settlement_due,
			"document_return_due_date": document_due,
			"status": "Open / مفتوح",
			"risk_level": "High / مرتفع",
			"legal_review_required": 1,
			"notes": _("Auto-created from approved Termination Notice {0}.").format(doc.name),
		}
	).insert(ignore_permissions=True)
