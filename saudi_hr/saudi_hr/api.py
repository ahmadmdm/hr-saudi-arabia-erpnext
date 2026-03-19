"""
saudi_hr/api.py
Mobile GPS Attendance API — endpoints called from the mobile PWA page.
"""
import frappe
from frappe import _
from frappe.utils import now_datetime, nowdate, get_datetime, flt, time_diff_in_hours

# ─── Haversine distance (returns metres) ──────────────────────────────────────
def _distance_meters(lat1, lon1, lat2, lon2):
	from math import asin, cos, pi, sqrt
	r = 6_371_000  # Earth radius in metres
	p = pi / 180
	a = (
		0.5
		- cos((lat2 - lat1) * p) / 2
		+ cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
	)
	return 2 * r * asin(sqrt(a))


# ─── Internal helpers ─────────────────────────────────────────────────────────
def _get_employee_for_user(user=None):
	"""Return Employee name for the given (or current) user, or raise."""
	user = user or frappe.session.user
	employee = frappe.db.get_value(
		"Employee", {"user_id": user, "status": "Active"}, "name"
	)
	if not employee:
		frappe.throw(_("لم يتم ربط حسابك بسجل موظف نشط. يرجى مراجعة مسؤول النظام."))
	return employee


def _get_location_for_branch(branch):
	"""Return the first active Attendance Location for the given branch."""
	if not branch:
		return None
	loc = frappe.db.get_value(
		"Attendance Location",
		{"branch": branch, "is_active": 1},
		["name", "location_name", "latitude", "longitude", "allowed_radius_meters"],
		as_dict=True,
	)
	return loc


def _get_todays_checkins(employee):
	"""Return today's Employee Checkin records for this employee, ordered by time."""
	return frappe.get_all(
		"Employee Checkin",
		filters={"employee": employee, "time": ["between", [nowdate() + " 00:00:00", nowdate() + " 23:59:59"]]},
		fields=["name", "log_type", "time", "latitude", "longitude"],
		order_by="time asc",
	)


# ─── Public API ───────────────────────────────────────────────────────────────
@frappe.whitelist()
def get_attendance_status():
	"""
	Return everything the mobile page needs to render:
	  - employee info
	  - branch location (coordinates + radius)
	  - today's checkins list
	  - last log type (IN / OUT / None) → determines what button to show
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("يجب تسجيل الدخول أولاً."), frappe.PermissionError)

	employee = _get_employee_for_user()
	emp_doc = frappe.db.get_value(
		"Employee",
		employee,
		["employee_name", "branch", "department", "image"],
		as_dict=True,
	)

	today_checkins = _get_todays_checkins(employee)

	# Determine last log type
	last_log_type = None
	last_checkin_time = None
	if today_checkins:
		last = today_checkins[-1]
		last_log_type = last.log_type
		last_checkin_time = str(last.time)

	# Get location for branch
	location = _get_location_for_branch(emp_doc.get("branch"))

	# Check if there is already attendance today (submitted)
	today_attendance = frappe.db.get_value(
		"Attendance",
		{"employee": employee, "attendance_date": nowdate(), "docstatus": 1},
		["name", "in_time", "out_time", "working_hours", "status"],
		as_dict=True,
	)

	return {
		"employee": employee,
		"employee_name": emp_doc.employee_name,
		"department": emp_doc.department,
		"image": emp_doc.image,
		"branch": emp_doc.branch,
		"last_log_type": last_log_type,
		"last_checkin_time": last_checkin_time,
		"today_checkins": today_checkins,
		"today_attendance": today_attendance,
		"location": location,
	}


@frappe.whitelist()
def do_mobile_checkin(latitude, longitude):
	"""
	Perform a GPS-validated check-in or check-out.

	1. Validates the user is a linked active employee.
	2. Gets the Attendance Location for the employee's branch.
	3. Calculates distance between employee GPS and branch GPS — rejects if > allowed radius.
	4. Determines log_type (IN / OUT).
	5. Creates Employee Checkin.
	6. On OUT: calculates working hours, creates & submits Attendance.
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("يجب تسجيل الدخول أولاً."), frappe.PermissionError)

	raw_latitude = latitude
	raw_longitude = longitude
	latitude = flt(latitude) if latitude not in (None, "", "null", "undefined") else None
	longitude = flt(longitude) if longitude not in (None, "", "null", "undefined") else None

	employee = _get_employee_for_user()
	branch = frappe.db.get_value("Employee", employee, "branch")

	# ── Location validation ──────────────────────────────────────────────────
	location = _get_location_for_branch(branch)
	if not location:
		# No location configured — allow check-in without GPS restriction
		pass
	else:
		if latitude is None or longitude is None:
			frappe.throw(_("تعذّر الحصول على إحداثيات GPS. يرجى السماح بإذن الموقع وإعادة المحاولة."))
		distance = _distance_meters(latitude, longitude, flt(location.latitude), flt(location.longitude))
		allowed = location.allowed_radius_meters or 100
		if distance > allowed:
			frappe.throw(
				_("أنت بعيد عن الفرع بمسافة {0} متر. الحد المسموح به هو {1} متر.").format(
					int(distance), int(allowed)
				)
			)

	# ── Determine log type ───────────────────────────────────────────────────
	today_checkins = _get_todays_checkins(employee)
	last_log = today_checkins[-1] if today_checkins else None
	log_type = "OUT" if (last_log and last_log.log_type == "IN") else "IN"

	now = now_datetime()

	# ── Create Employee Checkin ──────────────────────────────────────────────
	checkin = frappe.new_doc("Employee Checkin")
	checkin.update({
		"employee": employee,
		"log_type": log_type,
		"time": now,
		"latitude": latitude,
		"longitude": longitude,
		"device_id": "mobile-gps",
	})
	checkin.insert(ignore_permissions=True)
	frappe.db.commit()

	result = {
		"success": True,
		"log_type": log_type,
		"checkin_name": checkin.name,
		"checkin_time": str(now),
		"attendance_name": None,
		"message": _("تم تسجيل الحضور بنجاح في {0}").format(now.strftime("%H:%M"))
		if log_type == "IN"
		else _("تم تسجيل الانصراف بنجاح في {0}").format(now.strftime("%H:%M")),
	}

	# ── On OUT: create Attendance ────────────────────────────────────────────
	if log_type == "OUT":
		in_checkin = next((c for c in reversed(today_checkins) if c.log_type == "IN"), None)
		if in_checkin:
			in_time = get_datetime(in_checkin.time)
			out_time = now
			working_hours = time_diff_in_hours(out_time, in_time)

			# Skip if attendance already exists for today
			existing = frappe.db.get_value(
				"Attendance",
				{"employee": employee, "attendance_date": nowdate(), "docstatus": 1},
				"name",
			)
			if not existing:
				# Create and submit Attendance directly (ignore_permissions because employee
				# is registering their own attendance through a validated GPS flow)
				all_log_names = [c.name for c in today_checkins] + [checkin.name]

				attendance = frappe.new_doc("Attendance")
				attendance.update({
					"employee": employee,
					"attendance_date": nowdate(),
					"status": "Present",
					"working_hours": round(working_hours, 2),
					"in_time": in_time,
					"out_time": out_time,
				})
				attendance.insert(ignore_permissions=True)
				attendance.submit()

				# Link checkin records to this attendance
				for log_name in all_log_names:
					frappe.db.set_value("Employee Checkin", log_name, "attendance", attendance.name)
				frappe.db.commit()

				result["attendance_name"] = attendance.name
				result["working_hours"] = round(working_hours, 2)
				result["message"] = _("تم تسجيل الانصراف. مجموع ساعات العمل: {0} ساعة.").format(
					round(working_hours, 2)
				)

	return result


@frappe.whitelist()
def get_available_locations():
	"""Return all active Attendance Locations (for branch selector on mobile page)."""
	if frappe.session.user == "Guest":
		frappe.throw(_("يجب تسجيل الدخول أولاً."), frappe.PermissionError)

	return frappe.get_all(
		"Attendance Location",
		filters={"is_active": 1},
		fields=["name", "location_name", "branch", "latitude", "longitude", "allowed_radius_meters"],
		order_by="location_name asc",
	)
