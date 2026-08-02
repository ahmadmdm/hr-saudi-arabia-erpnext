frappe.ui.form.on("Saudi Leave Policy Assignment", {
	setup(frm) {
		frm.set_query("policy", () => ({
			filters: { enabled: 1 },
		}));
		frm.set_query("employee", () => ({
			filters: frm.doc.company ? { company: frm.doc.company, status: "Active" } : { status: "Active" },
		}));
		frm.set_query("department", () => ({
			filters: frm.doc.company ? { company: frm.doc.company } : {},
		}));
	},

	refresh(frm) {
		frm.set_intro(
			__("Resolution priority: Employee, then Department, then Saudi HR Settings."),
			"blue"
		);
	},

	policy(frm) {
		if (!frm.doc.policy) {
			frm.set_value("company", "");
			return;
		}
		frappe.db.get_value("Saudi Leave Policy", frm.doc.policy, ["company", "enabled"]).then((result) => {
			const values = result.message || {};
			frm.set_value("company", values.company || "");
			if (!values.enabled) {
				frappe.msgprint(__("The selected policy is disabled."));
			}
		});
	},

	applies_to(frm) {
		if (frm.doc.applies_to === "Employee / موظف") {
			frm.set_value("department", "");
		} else if (frm.doc.applies_to === "Department / قسم") {
			frm.set_value("employee", "");
		}
	},
});
