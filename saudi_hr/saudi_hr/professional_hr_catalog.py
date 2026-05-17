import frappe
from frappe import _


CATALOG_VERSION = "2026-05-08-component-parent-routes"


CATEGORIES = [
	{"id": "daily", "title": "Daily Command", "title_ar": "قيادة اليوم", "tone": "Operations"},
	{"id": "setup", "title": "Setup and Governance", "title_ar": "الإعداد والحوكمة", "tone": "Foundation"},
	{"id": "workflow", "title": "Workflow Control", "title_ar": "إدارة سير الموافقات", "tone": "Control"},
	{"id": "recruitment", "title": "Recruitment", "title_ar": "الاستقطاب", "tone": "Talent"},
	{"id": "onboarding", "title": "Onboarding and Contracts", "title_ar": "التوظيف والعقود", "tone": "Lifecycle"},
	{"id": "time", "title": "Time, Leave, and Payroll", "title_ar": "الدوام والإجازات والرواتب", "tone": "Payroll"},
	{"id": "performance", "title": "Performance and Growth", "title_ar": "الأداء والتطوير", "tone": "Growth"},
	{"id": "relations", "title": "Employee Relations", "title_ar": "علاقات الموظفين", "tone": "People"},
	{"id": "compliance", "title": "Compliance and Legal", "title_ar": "الامتثال والشؤون القانونية", "tone": "Risk"},
	{"id": "exit", "title": "Exit and Settlement", "title_ar": "إنهاء الخدمة والتسويات", "tone": "Closure"},
	{"id": "components", "title": "System Components", "title_ar": "مكونات النظام", "tone": "Structure"},
	{"id": "reports", "title": "Reports and Analytics", "title_ar": "التقارير والتحليلات", "tone": "Insights"},
]


FEATURES = [
	{"id": "mobile-attendance", "category": "daily", "title": "Mobile Attendance", "title_ar": "الحضور الجوال", "summary": "GPS attendance with lightweight challenge-based voice verification.", "summary_ar": "تسجيل حضور وانصراف بالجوال مع تحقق صوتي خفيف بالتحدي.", "target_type": "URL", "target": "/mobile-attendance", "priority": "Primary"},
	{"id": "attendance-action-hub", "category": "daily", "title": "Attendance Action Hub", "title_ar": "مركز إجراءات الحضور", "summary": "Daily attendance command page for exceptions, follow-up, and action routing.", "summary_ar": "صفحة قيادة يومية لمعالجة الاستثناءات والمتابعة وتوجيه الإجراءات.", "target_type": "Page", "target": "attendance-action-hub", "priority": "Primary"},
	{"id": "team-attendance-review", "category": "daily", "title": "Team Attendance Review", "title_ar": "مراجعة حضور الفريق", "summary": "Team-level report for attendance control and manager follow-up.", "summary_ar": "تقرير على مستوى الفريق لضبط الحضور ومتابعة المدراء.", "target_type": "Report", "target": "Team Attendance Review", "priority": "Primary"},
	{"id": "employee-org-tree", "category": "daily", "title": "Employee Org Tree", "title_ar": "الهيكل التنظيمي للموظفين", "summary": "Visual organization map for departments, managers, and employee scope.", "summary_ar": "خريطة تنظيمية لعرض الإدارات والمدراء ونطاق الموظفين.", "target_type": "Page", "target": "employee-org-tree", "priority": "Primary"},
	{"id": "saudi-hr-settings", "category": "setup", "title": "Saudi HR Settings", "title_ar": "إعدادات الموارد البشرية السعودية", "summary": "Central control for Saudi HR policies, voice mode, rates, alerts, and operating preferences.", "summary_ar": "مركز ضبط السياسات ونمط الصوت والنسب والتنبيهات وتفضيلات التشغيل.", "target_type": "DocType", "target": "Saudi HR Settings", "priority": "Primary", "allow_entry": False, "action_label": "Open Settings"},
	{"id": "attendance-location", "category": "setup", "title": "Attendance Location", "title_ar": "مواقع الحضور", "summary": "Define approved attendance zones and geofencing rules for mobile check-ins.", "summary_ar": "تعريف نطاقات الحضور المعتمدة وقواعد الموقع للحضور الجوال.", "target_type": "DocType", "target": "Attendance Location", "priority": "Primary"},
	{"id": "hr-policy-document", "category": "setup", "title": "HR Policy Document", "title_ar": "وثائق سياسات الموارد البشرية", "summary": "Maintain policy documents, versions, and acknowledgement governance.", "summary_ar": "إدارة وثائق السياسات وإصداراتها وحوكمة الإقرار بها.", "target_type": "DocType", "target": "HR Policy Document"},
	{"id": "legal-reference-matrix", "category": "setup", "title": "Legal Reference Matrix", "title_ar": "مصفوفة المراجع القانونية", "summary": "Reference Saudi labor rules and connect them to operational HR controls.", "summary_ar": "ربط مواد وأنظمة العمل السعودية بضوابط التشغيل في الموارد البشرية.", "target_type": "DocType", "target": "Legal Reference Matrix"},
	{"id": "saudi-regulatory-task", "category": "setup", "title": "Saudi Regulatory Task", "title_ar": "المهام التنظيمية السعودية", "summary": "Track statutory HR tasks, due dates, owners, and closure evidence.", "summary_ar": "متابعة المهام النظامية ومواعيدها والمسؤوليات وأدلة الإغلاق.", "target_type": "DocType", "target": "Saudi Regulatory Task"},
	{"id": "policy-acknowledgement", "category": "setup", "title": "Policy Acknowledgement", "title_ar": "إقرارات السياسات", "summary": "Record employee acknowledgement of HR policies and policy updates.", "summary_ar": "توثيق إقرار الموظفين بالسياسات وتحديثاتها.", "target_type": "DocType", "target": "Policy Acknowledgement"},
	{"id": "workflow", "category": "workflow", "title": "Workflow", "title_ar": "سير الموافقة", "summary": "Configure approval paths for HR documents and operational controls.", "summary_ar": "إعداد مسارات الموافقة لوثائق الموارد البشرية والضوابط التشغيلية.", "target_type": "DocType", "target": "Workflow"},
	{"id": "workflow-state", "category": "workflow", "title": "Workflow State", "title_ar": "حالات سير الموافقة", "summary": "Maintain workflow states used by HR approval processes.", "summary_ar": "إدارة حالات سير العمل المستخدمة في موافقات الموارد البشرية.", "target_type": "DocType", "target": "Workflow State"},
	{"id": "workflow-action", "category": "workflow", "title": "Workflow Action", "title_ar": "إجراءات سير الموافقة", "summary": "Monitor pending and completed approval actions across HR flows.", "summary_ar": "متابعة إجراءات الموافقة المعلقة والمكتملة عبر مسارات الموارد البشرية.", "target_type": "DocType", "target": "Workflow Action"},
	{"id": "overtime-approval-workflow", "category": "workflow", "title": "Overtime Approval Workflow", "title_ar": "سير موافقة العمل الإضافي", "summary": "Open the configured workflow record for overtime request approvals.", "summary_ar": "فتح سجل سير الموافقة الخاص بطلبات العمل الإضافي.", "target_type": "URL", "target": "/app/workflow/Overtime%20Approval%20Workflow"},
	{"id": "annual-leave-approval-workflow", "category": "workflow", "title": "Annual Leave Approval Workflow", "title_ar": "سير موافقة الإجازة السنوية", "summary": "Open the configured workflow record for annual leave approvals.", "summary_ar": "فتح سجل سير الموافقة الخاص بالإجازة السنوية.", "target_type": "URL", "target": "/app/workflow/Annual%20Leave%20Approval%20Workflow"},
	{"id": "sick-leave-approval-workflow", "category": "workflow", "title": "Sick Leave Approval Workflow", "title_ar": "سير موافقة الإجازة المرضية", "summary": "Open the configured workflow record for sick leave approvals.", "summary_ar": "فتح سجل سير الموافقة الخاص بالإجازة المرضية.", "target_type": "URL", "target": "/app/workflow/Sick%20Leave%20Approval%20Workflow"},
	{"id": "salary-adjustment-workflow", "category": "workflow", "title": "Salary Adjustment Workflow", "title_ar": "سير موافقة تعديل الراتب", "summary": "Open the configured workflow record for salary adjustment approvals.", "summary_ar": "فتح سجل سير الموافقة الخاص بتعديلات الرواتب.", "target_type": "URL", "target": "/app/workflow/Salary%20Adjustment%20Workflow"},
	{"id": "hiring-requisition", "category": "recruitment", "title": "Hiring Requisition", "title_ar": "طلب توظيف", "summary": "Request, approve, and track headcount needs before recruitment starts.", "summary_ar": "طلب واعتماد ومتابعة الاحتياج الوظيفي قبل بدء الاستقطاب.", "target_type": "DocType", "target": "Hiring Requisition", "priority": "Primary"},
	{"id": "candidate-profile", "category": "recruitment", "title": "Candidate Profile", "title_ar": "ملف المرشح", "summary": "Maintain candidate information and recruitment pipeline records.", "summary_ar": "إدارة بيانات المرشحين وسجلات خط الاستقطاب.", "target_type": "DocType", "target": "Candidate Profile"},
	{"id": "employee-onboarding", "category": "onboarding", "title": "Employee Onboarding", "title_ar": "تهيئة الموظف", "summary": "Coordinate onboarding tasks, owners, and readiness before joining.", "summary_ar": "تنسيق مهام التهيئة والمسؤوليات وجاهزية الموظف قبل المباشرة.", "target_type": "DocType", "target": "Employee Onboarding", "priority": "Primary"},
	{"id": "employee-profile", "category": "onboarding", "title": "Employee Profile", "title_ar": "ملف الموظف الشامل", "summary": "Open the employee master profile for core employment data.", "summary_ar": "فتح ملف الموظف الرئيسي لبيانات التوظيف الأساسية.", "target_type": "DocType", "target": "Employee", "priority": "Primary"},
	{"id": "saudi-employment-contract", "category": "onboarding", "title": "Saudi Employment Contract", "title_ar": "عقد العمل السعودي", "summary": "Manage Saudi employment contracts, terms, expiry, and renewals.", "summary_ar": "إدارة عقود العمل السعودية وشروطها وانتهائها وتجديدها.", "target_type": "DocType", "target": "Saudi Employment Contract", "priority": "Primary"},
	{"id": "medical-examination", "category": "onboarding", "title": "Medical Examination", "title_ar": "الفحص الطبي", "summary": "Track medical examination requirements and results for employees.", "summary_ar": "متابعة متطلبات ونتائج الفحص الطبي للموظفين.", "target_type": "DocType", "target": "Medical Examination"},
	{"id": "work-permit-iqama", "category": "onboarding", "title": "Work Permit Iqama", "title_ar": "رخصة العمل والإقامة", "summary": "Track work permit and Iqama records, expiry dates, and renewals.", "summary_ar": "متابعة رخص العمل والإقامات وتواريخ الانتهاء والتجديد.", "target_type": "DocType", "target": "Work Permit Iqama", "priority": "Primary"},
	{"id": "saudi-monthly-payroll", "category": "time", "title": "Saudi Monthly Payroll", "title_ar": "الرواتب الشهرية السعودية", "summary": "Run monthly Saudi payroll with deductions, contributions, and settlement context.", "summary_ar": "تشغيل الرواتب الشهرية مع الاستقطاعات والاشتراكات وسياق التسويات.", "target_type": "DocType", "target": "Saudi Monthly Payroll", "priority": "Primary"},
	{"id": "wps-submission", "category": "time", "title": "WPS Submission", "title_ar": "رفع حماية الأجور", "summary": "Prepare and track WPS payroll submissions.", "summary_ar": "تجهيز ومتابعة ملفات رفع حماية الأجور.", "target_type": "DocType", "target": "WPS Submission", "priority": "Primary"},
	{"id": "saudi-employee-checkin", "category": "time", "title": "Saudi Employee Checkin", "title_ar": "حركات حضور الموظفين", "summary": "Review employee check-in and check-out movements.", "summary_ar": "مراجعة حركات حضور وانصراف الموظفين.", "target_type": "DocType", "target": "Saudi Employee Checkin"},
	{"id": "saudi-daily-attendance", "category": "time", "title": "Saudi Daily Attendance", "title_ar": "الحضور اليومي السعودي", "summary": "Daily attendance records for operational payroll and compliance follow-up.", "summary_ar": "سجلات الحضور اليومية للتشغيل والرواتب والامتثال.", "target_type": "DocType", "target": "Saudi Daily Attendance"},
	{"id": "monthly-attendance-record", "category": "time", "title": "Monthly Attendance Record", "title_ar": "سجل الحضور الشهري", "summary": "Monthly attendance consolidation for payroll review.", "summary_ar": "تجميع الحضور الشهري لمراجعة الرواتب.", "target_type": "DocType", "target": "Monthly Attendance Record"},
	{"id": "saudi-employee-voice-profile", "category": "time", "title": "Saudi Employee Voice Profile", "title_ar": "ملف البصمة الصوتية", "summary": "Manage employee voice profiles when full biometric mode is enabled.", "summary_ar": "إدارة ملفات البصمة الصوتية عند تفعيل وضع البصمة الكاملة.", "target_type": "DocType", "target": "Saudi Employee Voice Profile"},
	{"id": "saudi-shift-type", "category": "time", "title": "Saudi Shift Type", "title_ar": "أنواع الورديات السعودية", "summary": "Define Saudi HR shift schedules used by attendance and payroll controls.", "summary_ar": "تعريف جداول الورديات داخل الموارد البشرية السعودية للحضور والرواتب.", "target_type": "DocType", "target": "Saudi Shift Type"},
	{"id": "saudi-shift-assignment", "category": "time", "title": "Saudi Shift Assignment", "title_ar": "تعيين الورديات السعودية", "summary": "Assign employees to Saudi HR shift schedules for attendance validation.", "summary_ar": "تعيين الموظفين على الورديات السعودية للتحقق من الحضور.", "target_type": "DocType", "target": "Saudi Shift Assignment"},
	{"id": "saudi-shift-assignment-tool", "category": "time", "title": "Saudi Shift Assignment Tool", "title_ar": "أداة تعيين الورديات السعودية", "summary": "Bulk assign Saudi HR shifts inside the Saudi HR app.", "summary_ar": "تعيين الورديات السعودية جماعياً داخل تطبيق الموارد البشرية السعودية.", "target_type": "DocType", "target": "Saudi Shift Assignment Tool"},
	{"id": "overtime-request", "category": "time", "title": "Overtime Request", "title_ar": "طلب عمل إضافي", "summary": "Request, approve, and post overtime based on HR policy.", "summary_ar": "طلب واعتماد وترحيل العمل الإضافي حسب سياسة الموارد البشرية.", "target_type": "DocType", "target": "Overtime Request"},
	{"id": "saudi-annual-leave", "category": "time", "title": "Saudi Annual Leave", "title_ar": "الإجازة السنوية السعودية", "summary": "Manage annual leave requests, balances, approvals, and disbursement context.", "summary_ar": "إدارة طلبات الإجازة السنوية والأرصدة والموافقات وسياق الصرف.", "target_type": "DocType", "target": "Saudi Annual Leave", "priority": "Primary"},
	{"id": "saudi-sick-leave", "category": "time", "title": "Saudi Sick Leave", "title_ar": "الإجازة المرضية السعودية", "summary": "Track sick leave rules, thresholds, and approval workflow.", "summary_ar": "متابعة قواعد الإجازة المرضية وحدودها وسير موافقاتها.", "target_type": "DocType", "target": "Saudi Sick Leave"},
	{"id": "maternity-paternity-leave", "category": "time", "title": "Maternity Paternity Leave", "title_ar": "إجازة الأمومة والأبوة", "summary": "Manage family-related statutory leave records.", "summary_ar": "إدارة سجلات الإجازات النظامية المرتبطة بالأسرة.", "target_type": "DocType", "target": "Maternity Paternity Leave"},
	{"id": "special-leave", "category": "time", "title": "Special Leave", "title_ar": "الإجازات الخاصة", "summary": "Track special leave cases and approvals.", "summary_ar": "متابعة حالات الإجازات الخاصة وموافقاتها.", "target_type": "DocType", "target": "Special Leave"},
	{"id": "employee-loan", "category": "time", "title": "Employee Loan", "title_ar": "سلفة/قرض الموظف", "summary": "Manage employee loans and payroll recovery.", "summary_ar": "إدارة سلف وقروض الموظفين واستردادها من الرواتب.", "target_type": "DocType", "target": "Employee Loan"},
	{"id": "gosi-contribution", "category": "time", "title": "GOSI Contribution", "title_ar": "اشتراكات التأمينات", "summary": "Track GOSI contributions and payroll accounting impact.", "summary_ar": "متابعة اشتراكات التأمينات وأثرها المحاسبي في الرواتب.", "target_type": "DocType", "target": "GOSI Contribution"},
	{"id": "nitaqat-record", "category": "time", "title": "Nitaqat Record", "title_ar": "سجل نطاقات", "summary": "Track Saudization and Nitaqat compliance records.", "summary_ar": "متابعة السعودة وسجلات امتثال نطاقات.", "target_type": "DocType", "target": "Nitaqat Record"},
	{"id": "performance-review", "category": "performance", "title": "Performance Review", "title_ar": "مراجعة الأداء", "summary": "Manage employee performance reviews and development outcomes.", "summary_ar": "إدارة مراجعات أداء الموظفين ومخرجات التطوير.", "target_type": "DocType", "target": "Performance Review", "priority": "Primary"},
	{"id": "salary-adjustment", "category": "performance", "title": "Salary Adjustment", "title_ar": "تعديل الراتب", "summary": "Request and approve salary adjustments with governance controls.", "summary_ar": "طلب واعتماد تعديلات الرواتب بضوابط حوكمة واضحة.", "target_type": "DocType", "target": "Salary Adjustment", "priority": "Primary"},
	{"id": "promotion-transfer", "category": "performance", "title": "Promotion Transfer", "title_ar": "ترقية أو نقل", "summary": "Manage promotions, transfers, and position movement decisions.", "summary_ar": "إدارة الترقيات والنقل وقرارات الحركة الوظيفية.", "target_type": "DocType", "target": "Promotion Transfer", "priority": "Primary"},
	{"id": "training-record", "category": "performance", "title": "Training Record", "title_ar": "سجل التدريب", "summary": "Track employee training participation and development evidence.", "summary_ar": "متابعة مشاركة الموظفين في التدريب وأدلة التطوير.", "target_type": "DocType", "target": "Training Record"},
	{"id": "employee-grievance", "category": "relations", "title": "Employee Grievance", "title_ar": "تظلم الموظف", "summary": "Record and resolve employee grievance cases.", "summary_ar": "تسجيل ومعالجة حالات تظلم الموظفين.", "target_type": "DocType", "target": "Employee Grievance"},
	{"id": "investigation-record", "category": "relations", "title": "Investigation Record", "title_ar": "سجل التحقيق", "summary": "Document employee investigations, findings, and actions.", "summary_ar": "توثيق التحقيقات والنتائج والإجراءات.", "target_type": "DocType", "target": "Investigation Record"},
	{"id": "employee-warning-notice", "category": "relations", "title": "Employee Warning Notice", "title_ar": "إنذار الموظف", "summary": "Issue and track warning notices with HR governance.", "summary_ar": "إصدار ومتابعة الإنذارات ضمن حوكمة الموارد البشرية.", "target_type": "DocType", "target": "Employee Warning Notice"},
	{"id": "absence-case", "category": "relations", "title": "Absence Case", "title_ar": "حالة غياب", "summary": "Track absence cases, justification, and resolution.", "summary_ar": "متابعة حالات الغياب والتبرير والإغلاق.", "target_type": "DocType", "target": "Absence Case"},
	{"id": "work-injury", "category": "relations", "title": "Work Injury", "title_ar": "إصابة عمل", "summary": "Record workplace injuries and follow-up actions.", "summary_ar": "تسجيل إصابات العمل وإجراءات المتابعة.", "target_type": "DocType", "target": "Work Injury"},
	{"id": "disciplinary-procedure", "category": "compliance", "title": "Disciplinary Procedure", "title_ar": "إجراء تأديبي", "summary": "Manage disciplinary procedures aligned with policy and labor law.", "summary_ar": "إدارة الإجراءات التأديبية وفق السياسة ونظام العمل.", "target_type": "DocType", "target": "Disciplinary Procedure"},
	{"id": "disciplinary-decision-log", "category": "compliance", "title": "Disciplinary Decision Log", "title_ar": "سجل القرارات التأديبية", "summary": "Track disciplinary decisions, evidence, and execution status.", "summary_ar": "متابعة القرارات التأديبية والأدلة وحالة التنفيذ.", "target_type": "DocType", "target": "Disciplinary Decision Log"},
	{"id": "disciplinary-appeal", "category": "compliance", "title": "Disciplinary Appeal", "title_ar": "اعتراض تأديبي", "summary": "Manage employee appeals against disciplinary decisions.", "summary_ar": "إدارة اعتراضات الموظفين على القرارات التأديبية.", "target_type": "DocType", "target": "Disciplinary Appeal"},
	{"id": "labor-dispute", "category": "compliance", "title": "Labor Dispute", "title_ar": "نزاع عمالي", "summary": "Track labor disputes, milestones, and settlement actions.", "summary_ar": "متابعة النزاعات العمالية ومراحلها وإجراءات التسوية.", "target_type": "DocType", "target": "Labor Dispute"},
	{"id": "labor-inspection", "category": "compliance", "title": "Labor Inspection", "title_ar": "تفتيش العمل", "summary": "Record labor inspections, findings, and corrective actions.", "summary_ar": "تسجيل زيارات التفتيش والملاحظات والإجراءات التصحيحية.", "target_type": "DocType", "target": "Labor Inspection"},
	{"id": "hr-compliance-action-log", "category": "compliance", "title": "HR Compliance Action Log", "title_ar": "سجل إجراءات الامتثال", "summary": "Central log for HR compliance actions and closure evidence.", "summary_ar": "سجل مركزي لإجراءات الامتثال وأدلة الإغلاق.", "target_type": "DocType", "target": "HR Compliance Action Log"},
	{"id": "termination-notice", "category": "exit", "title": "Termination Notice", "title_ar": "إشعار إنهاء الخدمة", "summary": "Issue and track termination notices with required dates and reasons.", "summary_ar": "إصدار ومتابعة إشعارات إنهاء الخدمة والتواريخ والأسباب.", "target_type": "DocType", "target": "Termination Notice"},
	{"id": "exit-clearance", "category": "exit", "title": "Exit Clearance", "title_ar": "إخلاء الطرف", "summary": "Coordinate clearance items before final settlement.", "summary_ar": "تنسيق بنود إخلاء الطرف قبل التسوية النهائية.", "target_type": "DocType", "target": "Exit Clearance", "priority": "Primary"},
	{"id": "exit-interview", "category": "exit", "title": "Exit Interview", "title_ar": "مقابلة الخروج", "summary": "Capture exit interview feedback and retention signals.", "summary_ar": "توثيق مقابلات الخروج ومؤشرات الاحتفاظ والتحسين.", "target_type": "DocType", "target": "Exit Interview"},
	{"id": "end-of-service-benefit", "category": "exit", "title": "End of Service Benefit", "title_ar": "مكافأة نهاية الخدمة", "summary": "Calculate and track EOSB entitlement and settlement details.", "summary_ar": "احتساب ومتابعة مستحقات نهاية الخدمة وتفاصيل التسوية.", "target_type": "DocType", "target": "End of Service Benefit"},
	{"id": "annual-leave-disbursement", "category": "exit", "title": "Annual Leave Disbursement", "title_ar": "صرف رصيد الإجازات", "summary": "Manage annual leave balance disbursement during settlement.", "summary_ar": "إدارة صرف رصيد الإجازات ضمن التسويات.", "target_type": "DocType", "target": "Annual Leave Disbursement"},
	{"id": "branch-employee-directory-row", "category": "components", "title": "Branch Employee Directory Row", "title_ar": "صف دليل موظفي الفرع", "summary": "Internal employee directory line used inside branch and organizational views.", "summary_ar": "سطر داخلي لدليل الموظفين يستخدم داخل عروض الفروع والتنظيم.", "target_type": "DocType", "target": "Branch Employee Directory Row", "allow_entry": False, "route_target_type": "Page", "route_target": "employee-org-tree", "action_label": "Open Parent View"},
	{"id": "employee-loan-installment", "category": "components", "title": "Employee Loan Installment", "title_ar": "قسط سلفة الموظف", "summary": "Installment schedule component used inside employee loan recovery records.", "summary_ar": "مكوّن جدول الأقساط المستخدم داخل سجلات استرداد سلف الموظفين.", "target_type": "DocType", "target": "Employee Loan Installment", "allow_entry": False, "route_target_type": "DocType", "route_target": "Employee Loan", "action_label": "Open Parent Records"},
	{"id": "labor-inspection-violation", "category": "components", "title": "Labor Inspection Violation", "title_ar": "مخالفة تفتيش العمل", "summary": "Violation detail component captured within labor inspection records.", "summary_ar": "مكوّن تفاصيل المخالفات المسجلة داخل سجلات تفتيش العمل.", "target_type": "DocType", "target": "Labor Inspection Violation", "allow_entry": False, "route_target_type": "DocType", "route_target": "Labor Inspection", "action_label": "Open Parent Records"},
	{"id": "monthly-attendance-detail", "category": "components", "title": "Monthly Attendance Detail", "title_ar": "تفصيل الحضور الشهري", "summary": "Employee-level attendance detail line used in monthly attendance consolidation.", "summary_ar": "سطر تفصيلي على مستوى الموظف داخل تجميع الحضور الشهري.", "target_type": "DocType", "target": "Monthly Attendance Detail", "allow_entry": False, "route_target_type": "DocType", "route_target": "Monthly Attendance Record", "action_label": "Open Parent Records"},
	{"id": "payroll-adjustment-item", "category": "components", "title": "Payroll Adjustment Item", "title_ar": "بند تعديل الرواتب", "summary": "Payroll adjustment line component used inside monthly payroll processing.", "summary_ar": "مكوّن بند التعديل المستخدم داخل معالجة الرواتب الشهرية.", "target_type": "DocType", "target": "Payroll Adjustment Item", "allow_entry": False, "route_target_type": "DocType", "route_target": "Saudi Monthly Payroll", "action_label": "Open Parent Records"},
	{"id": "saudi-monthly-payroll-employee", "category": "components", "title": "Saudi Monthly Payroll Employee", "title_ar": "موظف الرواتب الشهرية السعودية", "summary": "Employee payroll line component generated within Saudi monthly payroll runs.", "summary_ar": "سطر راتب الموظف الذي ينشأ داخل تشغيل الرواتب الشهرية السعودية.", "target_type": "DocType", "target": "Saudi Monthly Payroll Employee", "allow_entry": False, "route_target_type": "DocType", "route_target": "Saudi Monthly Payroll", "action_label": "Open Parent Records"},
	{"id": "saudi-labor-coverage-matrix", "category": "reports", "title": "Saudi Labor Coverage Matrix", "title_ar": "مصفوفة تغطية نظام العمل", "summary": "Report coverage of Saudi labor requirements across HR controls.", "summary_ar": "تقرير تغطية متطلبات نظام العمل عبر ضوابط الموارد البشرية.", "target_type": "Report", "target": "Saudi Labor Coverage Matrix"},
	{"id": "policy-compliance-register", "category": "reports", "title": "Policy Compliance Register", "title_ar": "سجل امتثال السياسات", "summary": "Review policy compliance status and gaps.", "summary_ar": "مراجعة حالة امتثال السياسات والفجوات.", "target_type": "Report", "target": "Policy Compliance Register"},
	{"id": "compliance-case-tracker", "category": "reports", "title": "Compliance Case Tracker", "title_ar": "متابعة قضايا الامتثال", "summary": "Track compliance cases across ownership and status.", "summary_ar": "متابعة قضايا الامتثال حسب الملكية والحالة.", "target_type": "Report", "target": "Compliance Case Tracker"},
	{"id": "labor-inspection-tracker", "category": "reports", "title": "Labor Inspection Tracker", "title_ar": "متابعة تفتيش العمل", "summary": "Monitor inspection findings and corrective actions.", "summary_ar": "متابعة ملاحظات التفتيش والإجراءات التصحيحية.", "target_type": "Report", "target": "Labor Inspection Tracker"},
	{"id": "gosi-monthly-report", "category": "reports", "title": "GOSI Monthly Report", "title_ar": "تقرير التأمينات الشهري", "summary": "Monthly report for GOSI contribution review.", "summary_ar": "تقرير شهري لمراجعة اشتراكات التأمينات.", "target_type": "Report", "target": "GOSI Monthly Report"},
	{"id": "eosb-calculation-report", "category": "reports", "title": "EOSB Calculation Report", "title_ar": "تقرير احتساب نهاية الخدمة", "summary": "Review EOSB calculations and settlement values.", "summary_ar": "مراجعة احتساب مكافأة نهاية الخدمة وقيم التسويات.", "target_type": "Report", "target": "EOSB Calculation Report"},
	{"id": "contract-expiry-report", "category": "reports", "title": "Contract Expiry Report", "title_ar": "تقرير انتهاء العقود", "summary": "Monitor contract expiry dates and renewal pipeline.", "summary_ar": "متابعة انتهاء العقود ومسار التجديد.", "target_type": "Report", "target": "Contract Expiry Report"},
	{"id": "work-permit-expiry-report", "category": "reports", "title": "Work Permit Expiry Report", "title_ar": "تقرير انتهاء الرخص والإقامات", "summary": "Monitor work permit and Iqama expiry risks.", "summary_ar": "متابعة مخاطر انتهاء رخص العمل والإقامات.", "target_type": "Report", "target": "Work Permit Expiry Report"},
	{"id": "nitaqat-compliance-report", "category": "reports", "title": "Nitaqat Compliance Report", "title_ar": "تقرير امتثال نطاقات", "summary": "Review Nitaqat compliance and Saudization position.", "summary_ar": "مراجعة امتثال نطاقات ووضع السعودة.", "target_type": "Report", "target": "Nitaqat Compliance Report"},
	{"id": "saudi-leave-balance-report", "category": "reports", "title": "Saudi Leave Balance Report", "title_ar": "تقرير أرصدة الإجازات", "summary": "Review leave balances and liabilities.", "summary_ar": "مراجعة أرصدة الإجازات والالتزامات.", "target_type": "Report", "target": "Saudi Leave Balance Report"},
	{"id": "outstanding-employee-loans", "category": "reports", "title": "Outstanding Employee Loans", "title_ar": "سلف الموظفين القائمة", "summary": "Report outstanding employee loan balances.", "summary_ar": "تقرير أرصدة سلف الموظفين القائمة.", "target_type": "Report", "target": "Outstanding Employee Loans"},
	{"id": "loan-deduction-register", "category": "reports", "title": "Loan Deduction Register", "title_ar": "سجل استقطاعات السلف", "summary": "Review payroll loan deductions.", "summary_ar": "مراجعة استقطاعات السلف في الرواتب.", "target_type": "Report", "target": "Loan Deduction Register"},
	{"id": "monthly-loan-recovery-summary", "category": "reports", "title": "Monthly Loan Recovery Summary", "title_ar": "ملخص استرداد السلف الشهري", "summary": "Summarize monthly employee loan recovery.", "summary_ar": "تلخيص استرداد سلف الموظفين شهرياً.", "target_type": "Report", "target": "Monthly Loan Recovery Summary"},
	{"id": "wps-export-report", "category": "reports", "title": "WPS Export Report", "title_ar": "تقرير تصدير حماية الأجور", "summary": "Review WPS export output before submission.", "summary_ar": "مراجعة مخرجات تصدير حماية الأجور قبل الرفع.", "target_type": "Report", "target": "WPS Export Report"},
	{"id": "wps-submission-tracker", "category": "reports", "title": "WPS Submission Tracker", "title_ar": "متابعة رفع حماية الأجور", "summary": "Track WPS submission status, files, and follow-up.", "summary_ar": "متابعة حالة رفع حماية الأجور والملفات والإجراءات.", "target_type": "Report", "target": "WPS Submission Tracker", "priority": "Primary"},
]


def _route_for_target(target_type, target):
	if not target:
		return ""
	if target_type == "URL":
		return target
	if target_type == "Page":
		return f"/app/{target}"
	if target_type == "Report":
		return f"/app/query-report/{target}"
	return f"/app/{frappe.scrub(target).replace('_', '-')}"


def _route_for_feature(feature):
	return _route_for_target(
		feature.get("route_target_type") or feature.get("target_type"),
		feature.get("route_target") or feature.get("target"),
	)


def _feature_with_route(feature):
	item = dict(feature)
	item["route"] = _route_for_feature(feature)
	item["detail_route"] = f"/app/professional-hr-feature/{feature['id']}"
	if feature.get("target_type") == "DocType" and feature.get("allow_entry") is not False:
		item["entry_route"] = f"/app/professional-hr-entry/{feature['id']}"
	return item


@frappe.whitelist()
def get_professional_hr_catalog():
	features = [_feature_with_route(feature) for feature in FEATURES]
	category_counts = {category["id"]: 0 for category in CATEGORIES}
	for feature in features:
		category_counts[feature["category"]] = category_counts.get(feature["category"], 0) + 1

	return {
		"version": CATALOG_VERSION,
		"categories": [dict(category, count=category_counts.get(category["id"], 0)) for category in CATEGORIES],
		"features": features,
		"total_features": len(features),
		"primary_features": len([feature for feature in features if feature.get("priority") == "Primary"]),
	}


@frappe.whitelist()
def get_professional_hr_feature(feature_id):
	catalog = get_professional_hr_catalog()
	feature = next((item for item in catalog["features"] if item["id"] == feature_id), None)
	if not feature:
		frappe.throw(_("Professional HR feature not found."), frappe.DoesNotExistError)

	category = next((item for item in catalog["categories"] if item["id"] == feature["category"]), None)
	related = [
		item
		for item in catalog["features"]
		if item["category"] == feature["category"] and item["id"] != feature["id"]
	][:6]

	return {
		"feature": feature,
		"category": category,
		"related": related,
		"catalog_summary": {
			"total_features": catalog["total_features"],
			"category_features": category.get("count") if category else 0,
		},
	}
