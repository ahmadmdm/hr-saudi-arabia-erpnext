const LEGAL_REFERENCE_MATRIX_SECTION_DESCRIPTIONS = {
	reference_section: "Register the legal article, its effective date, and the internal owner responsible for monitoring it.",
	obligation_section: "Map each legal obligation to a control, policy, and evidence requirement.",
};


frappe.ui.form.on("Legal Reference Matrix", {
	refresh(frm) {
		apply_legal_reference_matrix_section_descriptions(frm, LEGAL_REFERENCE_MATRIX_SECTION_DESCRIPTIONS);
	},
});


function apply_legal_reference_matrix_section_descriptions(frm, descriptions) {
	for (const [fieldname, description] of Object.entries(descriptions)) {
		frm.set_df_property(fieldname, "description", __(description));
	}
	frm.refresh_fields(Object.keys(descriptions));
}