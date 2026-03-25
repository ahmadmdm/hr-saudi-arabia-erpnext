import json
import urllib.error
import urllib.parse
import urllib.request

import frappe
from frappe import _

try:
	from openlocationcode import openlocationcode as olc
except ImportError:
	olc = None


def build_geolocation(latitude, longitude, radius=100):
	return frappe.as_json(
		{
			"type": "FeatureCollection",
			"features": [
				{
					"type": "Feature",
					"properties": {
						"point_type": "circle",
						"radius": int(radius or 100),
					},
					"geometry": {
						"type": "Point",
						"coordinates": [float(longitude), float(latitude)],
					},
				}
			],
		}
	)


def extract_coordinates_from_geolocation(geolocation):
	if not geolocation:
		return None, None

	data = geolocation
	if isinstance(geolocation, str):
		try:
			data = json.loads(geolocation)
		except json.JSONDecodeError:
			return None, None

	features = data.get("features") or []
	for feature in features:
		geometry = feature.get("geometry") or {}
		coordinates = geometry.get("coordinates") or []
		if geometry.get("type") == "Point" and len(coordinates) >= 2:
			return float(coordinates[1]), float(coordinates[0])

	return None, None


def normalize_plus_code(value):
	return " ".join((value or "").upper().split())


def encode_plus_code(latitude, longitude):
	if not olc:
		return None
	return olc.encode(float(latitude), float(longitude))


def resolve_location_reference(
	*,
	plus_code=None,
	latitude=None,
	longitude=None,
	geolocation=None,
	location_input_method=None,
	address_reference=None,
):
	latitude = float(latitude) if latitude not in (None, "") else None
	longitude = float(longitude) if longitude not in (None, "") else None
	map_latitude, map_longitude = extract_coordinates_from_geolocation(geolocation)

	if map_latitude is not None and map_longitude is not None and location_input_method == "Map Pin / دبوس الخريطة":
		latitude, longitude = map_latitude, map_longitude

	resolved_plus_code = normalize_plus_code(plus_code)
	location_source = location_input_method or "Coordinates / إحداثيات"

	if resolved_plus_code:
		plus_code_result = _resolve_plus_code(
			resolved_plus_code,
			reference_latitude=latitude or map_latitude,
			reference_longitude=longitude or map_longitude,
			address_reference=address_reference,
		)
		latitude = plus_code_result["latitude"]
		longitude = plus_code_result["longitude"]
		resolved_plus_code = plus_code_result["plus_code"]
		location_source = plus_code_result["location_source"]

	if latitude is None or longitude is None:
		if map_latitude is not None and map_longitude is not None:
			latitude, longitude = map_latitude, map_longitude
			location_source = "Map Pin / دبوس الخريطة"
		else:
			frappe.throw(
				_("حدد الإحداثيات أو اختر نقطة من الخريطة أو أدخل Plus Code صالحاً."),
				title=_("Location Required / الموقع مطلوب"),
			)

	if not resolved_plus_code:
		resolved_plus_code = encode_plus_code(latitude, longitude)

	return {
		"latitude": round(float(latitude), 8),
		"longitude": round(float(longitude), 8),
		"plus_code": resolved_plus_code,
		"location_source": location_source,
	}


def _resolve_plus_code(plus_code, reference_latitude=None, reference_longitude=None, address_reference=None):
	if not olc:
		frappe.throw(
			_("مكتبة Plus Code غير مثبّتة. ثبّت openlocationcode ثم أعد المحاولة."),
			title=_("Plus Code Library Missing / مكتبة البلص كود غير متوفرة"),
		)

	normalized = normalize_plus_code(plus_code)
	if "+" not in normalized:
		frappe.throw(_("صيغة Plus Code غير صحيحة."), title=_("Invalid Plus Code / بلص كود غير صحيح"))

	if olc.isFull(normalized):
		decoded = olc.decode(normalized)
		return {
			"latitude": decoded.latitudeCenter,
			"longitude": decoded.longitudeCenter,
			"plus_code": normalized,
			"location_source": "Plus Code / بلص كود",
		}

	if reference_latitude is not None and reference_longitude is not None:
		full_code = olc.recoverNearest(normalized, float(reference_latitude), float(reference_longitude))
		decoded = olc.decode(full_code)
		return {
			"latitude": decoded.latitudeCenter,
			"longitude": decoded.longitudeCenter,
			"plus_code": full_code,
			"location_source": "Plus Code / بلص كود",
		}

	query = " ".join(part for part in [normalized, (address_reference or "").strip()] if part).strip()
	geocoded = _geocode_query(query)
	if geocoded:
		resolved_plus_code = encode_plus_code(geocoded["latitude"], geocoded["longitude"])
		return {
			"latitude": geocoded["latitude"],
			"longitude": geocoded["longitude"],
			"plus_code": resolved_plus_code or normalized,
			"location_source": "Plus Code + Locality / بلص كود مع مرجع",
		}

	frappe.throw(
		_(
			"تعذر تحليل البلص كود المختصر بدون مرجع جغرافي قريب. أدخل Full Plus Code أو أضف مرجعاً واضحاً ثم أكد الموقع من الخريطة."
		),
		title=_("Short Plus Code Needs Reference / البلص كود المختصر يحتاج مرجعاً"),
	)


def _geocode_query(query):
	if not query:
		return None

	params = urllib.parse.urlencode({"q": query, "format": "jsonv2", "limit": 1})
	request = urllib.request.Request(
		f"https://nominatim.openstreetmap.org/search?{params}",
		headers={"User-Agent": "saudi_hr/1.0 attendance-location"},
	)

	try:
		with urllib.request.urlopen(request, timeout=8) as response:
			payload = json.loads(response.read().decode("utf-8"))
	except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
		return None

	if not payload:
		return None

	result = payload[0]
	return {
		"latitude": float(result["lat"]),
		"longitude": float(result["lon"]),
	}