frappe.query_reports["Labor Inspection Tracker"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
		},
		{
			fieldname: "inspection_authority",
			label: __("Authority / الجهة"),
			fieldtype: "Select",
			options: "\nMinistry of Human Resources / وزارة الموارد البشرية\nGOSI / التأمينات الاجتماعية\nMunicipality / البلدية\nCivil Defense / الدفاع المدني\nInternal Audit / تدقيق داخلي\nOther / أخرى",
		},
		{
			fieldname: "inspection_status",
			label: __("Inspection Status / حالة التفتيش"),
			fieldtype: "Select",
			options: "\nDraft / مسودة\nOpen Findings / مخالفات مفتوحة\nUnder Follow-up / قيد المتابعة\nCorrected / تم التصحيح\nClosed / مغلق",
		},
		{
			fieldname: "violation_status",
			label: __("Violation Status / حالة المخالفة"),
			fieldtype: "Select",
			options: "\nOpen / مفتوح\nUnder Review / قيد المراجعة\nCorrective Action In Progress / التصحيح جارٍ\nCorrected / تم التصحيح\nWaived / معفى\nClosed / مغلق",
		},
		{
			fieldname: "from_date",
			label: __("From Date / من تاريخ"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date / إلى تاريخ"),
			fieldtype: "Date",
		},
	],
};