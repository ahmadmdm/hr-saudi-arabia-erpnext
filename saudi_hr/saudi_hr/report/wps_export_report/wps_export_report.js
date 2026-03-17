frappe.query_reports["WPS Export Report"] = {
    filters: [
        {
            fieldname: "payroll_document",
            label: __("Saudi Monthly Payroll"),
            fieldtype: "Link",
            options: "Saudi Monthly Payroll",
            reqd: 1
        }
    ],

    onload: function (report) {
        report.page.add_inner_button(__("Download WPS SIF File"), function () {
            let payroll = report.get_filter_value("payroll_document");
            if (!payroll) {
                frappe.msgprint(__("Please select a Saudi Monthly Payroll first"));
                return;
            }
            frappe.call({
                method: "saudi_hr.saudi_hr.report.wps_export_report.wps_export_report.download_wps_sif",
                args: { payroll_document: payroll },
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint(__("WPS SIF File downloaded successfully."));
                    }
                }
            });
            // Trigger stream download
            window.location.href = frappe.urllib.get_full_url(
                `/api/method/saudi_hr.saudi_hr.report.wps_export_report.wps_export_report.download_wps_sif?payroll_document=${encodeURIComponent(payroll)}`
            );
        });
    }
};
