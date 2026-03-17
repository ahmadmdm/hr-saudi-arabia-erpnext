frappe.ui.form.on("Attendance Location", {
	latitude: function (frm) {
		frm.trigger("refresh_geolocation");
	},
	longitude: function (frm) {
		frm.trigger("refresh_geolocation");
	},
	allowed_radius_meters: function (frm) {
		frm.trigger("refresh_geolocation");
	},
	refresh_geolocation: frappe.utils.debounce(function (frm) {
		if (frm.doc.latitude && frm.doc.longitude) {
			frm.call("set_geolocation").then(() => frm.refresh_field("geolocation"));
		}
	}, 800),
	refresh: function (frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("تحديث الموقع على الخريطة"), function () {
				frm.trigger("refresh_geolocation");
			});
		}
	},
});
