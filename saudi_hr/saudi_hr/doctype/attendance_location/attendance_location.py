import frappe
from frappe.model.document import Document


class AttendanceLocation(Document):
	def on_update(self):
		"""Auto-generate Geolocation JSON from latitude & longitude."""
		if self.latitude and self.longitude:
			self.geolocation = frappe.as_json({
				"type": "FeatureCollection",
				"features": [
					{
						"type": "Feature",
						"properties": {"point_type": "circle", "radius": self.allowed_radius_meters or 100},
						"geometry": {
							"type": "Point",
							"coordinates": [float(self.longitude), float(self.latitude)],
						},
					}
				],
			})
			frappe.db.set_value("Attendance Location", self.name, "geolocation", self.geolocation)
