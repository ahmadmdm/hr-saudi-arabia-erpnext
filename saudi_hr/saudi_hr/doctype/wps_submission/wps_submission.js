frappe.ui.form.on("WPS Submission", {
	refresh(frm) {
		if (frm.doc.payroll_document) {
			frm.add_custom_button(__("Open Payroll / فتح المسير"), () => {
				frappe.set_route("Form", "Saudi Monthly Payroll", frm.doc.payroll_document);
			});

			frm.add_custom_button(__("Download WPS SIF File / تنزيل ملف حماية الأجور"), () => {
				window.location.href = frappe.urllib.get_full_url(
					`/api/method/saudi_hr.saudi_hr.report.wps_export_report.wps_export_report.download_wps_sif?payroll_document=${encodeURIComponent(frm.doc.payroll_document)}`
				);
			});
		}

		if (frm.doc.corrective_action_log) {
			frm.add_custom_button(__("Open Compliance Action / فتح إجراء الامتثال"), () => {
				frappe.set_route("Form", "HR Compliance Action Log", frm.doc.corrective_action_log);
			});
		}
	},
});