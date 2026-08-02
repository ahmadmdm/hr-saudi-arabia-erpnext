frappe.ui.form.on("Saudi Leave Policy", {
	refresh(frm) {
		if (frm.is_new()) {
			frm.set_intro(
				__(
					"Define benefits at or above Saudi statutory minimums, then assign the policy to a department or employee."
				),
				"blue"
			);
		} else if (!frm.doc.enabled) {
			frm.set_intro(
				__("Disabled policies are ignored when leave entitlement is resolved."),
				"orange"
			);
		}
	},
});
