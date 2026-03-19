const INVESTIGATION_RECORD_SECTION_DESCRIPTIONS = {
	reference_section: "Identify the source case, allegation date, and assigned investigator.",
	timeline_section: "Track the lifecycle of the investigation from opening to closure.",
	details_section: "Write the allegation, employee statement, findings, and recommended outcome.",
};


frappe.ui.form.on("Investigation Record", {
	refresh(frm) {
		apply_investigation_record_section_descriptions(frm, INVESTIGATION_RECORD_SECTION_DESCRIPTIONS);
	},
});


function apply_investigation_record_section_descriptions(frm, descriptions) {
	for (const [fieldname, description] of Object.entries(descriptions)) {
		frm.set_df_property(fieldname, "description", __(description));
	}
	frm.refresh_fields(Object.keys(descriptions));
}