"""
saudi_hr/api.py
Mobile attendance, employee insights, and self-service leave APIs.
"""

import base64
import calendar
import json

import frappe
from frappe import _
from frappe.utils import flt, get_datetime, get_first_day, get_last_day, getdate, now_datetime, nowdate, time_diff_in_hours
from frappe.utils.file_manager import save_file

from saudi_hr.saudi_hr.doctype.maternity_paternity_leave.maternity_paternity_leave import LEAVE_DAYS
from saudi_hr.saudi_hr.location_utils import resolve_location_reference
from saudi_hr.saudi_hr.utils import assert_doctype_permissions, get_annual_leave_balance


SPECIAL_LEAVE_OPTIONS = [
	"Hajj Leave / إجازة حج (م.113 – 15 يوم)",
	"Bereavement Leave / إجازة وفاة (م.113 – 5 أيام)",
	"Marriage Leave / إجازة زواج (م.113 – 5 أيام)",
]

ELEVATED_ROLES = {"HR Manager", "HR User", "System Manager"}
MAX_MOBILE_ATTACHMENTS = 3
MAX_MOBILE_ATTACHMENT_SIZE = 5 * 1024 * 1024


def _distance_meters(lat1, lon1, lat2, lon2):
	from math import asin, cos, pi, sqrt

	r = 6_371_000
	p = pi / 180
	a = (
		0.5
		- cos((lat2 - lat1) * p) / 2
		+ cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
	)
	return 2 * r * asin(sqrt(a))


def _get_employee_for_user(user=None):
	user = user or frappe.session.user
	employee = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")
	if not employee:
		frappe.throw(_("لم يتم ربط حسابك بسجل موظف نشط. يرجى مراجعة مسؤول النظام."))
	return employee


def _get_employee_profile(employee):
	return frappe.db.get_value(
		"Employee",
		employee,
		["employee_name", "branch", "department", "image", "company", "designation"],
		as_dict=True,
	)


def _require_employee_context():
	if frappe.session.user == "Guest":
		frappe.throw(_("يجب تسجيل الدخول أولاً."), frappe.PermissionError)

	employee = _get_employee_for_user()
	return employee, _get_employee_profile(employee)


def _get_location_for_branch(branch):
	if not branch:
		return None
	return frappe.db.get_value(
		"Attendance Location",
		{"branch": branch, "is_active": 1},
		[
			"name",
			"location_name",
			"latitude",
			"longitude",
			"allowed_radius_meters",
			"plus_code",
			"location_source",
			"address_reference",
		],
		as_dict=True,
	)


def _get_todays_checkins(employee):
	return frappe.get_all(
		"Saudi Employee Checkin",
		filters={"employee": employee, "time": ["between", [nowdate() + " 00:00:00", nowdate() + " 23:59:59"]]},
		fields=["name", "log_type", "time", "latitude", "longitude", "verification_mode"],
		order_by="time asc",
	)


def _coerce_float(value):
	return flt(value) if value not in (None, "", "null", "undefined") else None


def _load_json_param(value, default=None):
	if value in (None, "", "null", "undefined"):
		return default
	if isinstance(value, (dict, list)):
		return value
	return json.loads(value)


def _decode_base64_content(content):
	if not content:
		return b""
	if "," in content and ";base64" in content.split(",", 1)[0]:
		content = content.split(",", 1)[1]
	return base64.b64decode(content)


def _attach_files(doc, attachments):
	if not attachments:
		return []

	if len(attachments) > MAX_MOBILE_ATTACHMENTS:
		frappe.throw(_("يمكن إرفاق ثلاثة ملفات كحد أقصى لكل عملية."))

	attached = []
	for index, attachment in enumerate(attachments, start=1):
		filename = (attachment or {}).get("filename") or f"{doc.name}-{index}"
		content = _decode_base64_content((attachment or {}).get("content"))
		if not content:
			continue
		if len(content) > MAX_MOBILE_ATTACHMENT_SIZE:
			frappe.throw(_("حجم الملف الواحد يجب ألا يتجاوز 5 ميجابايت."))

		file_doc = save_file(filename, content, doc.doctype, doc.name, is_private=1)
		attached.append({"file_name": file_doc.file_name, "file_url": file_doc.file_url})

	return attached


def _get_contract_hours_per_day(employee):
	working_hours = frappe.db.get_value(
		"Saudi Employment Contract",
		{"employee": employee, "contract_status": "Active / نشط"},
		"working_hours_per_day",
		order_by="start_date desc",
	)
	return flt(working_hours or 8)


def _get_period_bounds(month=None, year=None):
	today = getdate(nowdate())
	month_number = int(month or today.month)
	year_number = int(year or today.year)
	anchor = getdate(f"{year_number}-{month_number:02d}-01")
	return get_first_day(anchor), get_last_day(anchor), month_number, year_number


def _get_payroll_snapshot(employee):
	rows = frappe.db.sql(
		"""
		SELECT
			child.gosi_employee_deduction,
			child.sick_leave_deduction,
			child.loan_deduction,
			child.total_deductions,
			child.overtime_addition,
			child.net_salary,
			parent.month,
			parent.year,
			parent.status
		FROM `tabSaudi Monthly Payroll Employee` child
		INNER JOIN `tabSaudi Monthly Payroll` parent ON parent.name = child.parent
		WHERE child.employee = %s AND parent.docstatus = 1
		ORDER BY parent.year DESC, parent.modified DESC
		LIMIT 1
		""",
		employee,
		as_dict=True,
	)
	if not rows:
		return None

	row = rows[0]
	return {
		"period": f"{row.month} {row.year}",
		"status": row.status,
		"gosi_deduction": flt(row.gosi_employee_deduction),
		"sick_leave_deduction": flt(row.sick_leave_deduction),
		"loan_deduction": flt(row.loan_deduction),
		"total_deductions": flt(row.total_deductions),
		"overtime_addition": flt(row.overtime_addition),
		"net_salary": flt(row.net_salary),
	}


def _get_attendance_insights(employee, month=None, year=None):
	from_date, to_date, month_number, year_number = _get_period_bounds(month, year)
	working_hours_target = _get_contract_hours_per_day(employee)

	record = frappe.db.get_value(
		"Monthly Attendance Record",
		{"employee": employee, "year": year_number, "month": ["like", f"{calendar.month_name[month_number]}%"]},
		[
			"actual_present_days",
			"absent_days",
			"late_days",
			"late_minutes_total",
			"overtime_hours_total",
			"annual_leave_days",
			"sick_leave_days",
			"special_leave_days",
			"other_leave_days",
		],
		as_dict=True,
	)

	attendance_rows = frappe.get_all(
		"Saudi Daily Attendance",
		filters={"employee": employee, "attendance_date": ["between", [from_date, to_date]], "docstatus": 1},
		fields=["status", "working_hours", "late_entry", "early_exit"],
	)

	total_hours = round(sum(flt(row.working_hours) for row in attendance_rows), 2)
	recorded_days = len(attendance_rows)
	shortfall_days = sum(1 for row in attendance_rows if flt(row.working_hours) and flt(row.working_hours) < working_hours_target)
	early_exit_days = sum(1 for row in attendance_rows if row.early_exit)
	late_entry_days = sum(1 for row in attendance_rows if row.late_entry)

	return {
		"period_label": f"{calendar.month_name[month_number]} {year_number}",
		"present_days": int((record or {}).get("actual_present_days") or recorded_days),
		"absent_days": int((record or {}).get("absent_days") or 0),
		"late_days": int((record or {}).get("late_days") or late_entry_days),
		"late_minutes_total": int((record or {}).get("late_minutes_total") or 0),
		"overtime_hours_total": round(flt((record or {}).get("overtime_hours_total") or 0), 2),
		"recorded_days": recorded_days,
		"total_hours": total_hours,
		"average_hours": round(total_hours / recorded_days, 2) if recorded_days else 0,
		"shortfall_days": shortfall_days,
		"early_exit_days": early_exit_days,
		"target_hours_per_day": working_hours_target,
		"leave_days": {
			"annual": flt((record or {}).get("annual_leave_days") or 0),
			"sick": flt((record or {}).get("sick_leave_days") or 0),
			"special": flt((record or {}).get("special_leave_days") or 0),
			"other": flt((record or {}).get("other_leave_days") or 0),
		},
		"payroll": _get_payroll_snapshot(employee),
	}


def _get_leave_options(employee):
	annual_balance = get_annual_leave_balance(employee, nowdate())

	return {
		"annual": {
			"label": "Annual Leave / إجازة سنوية",
			"doctype": "Saudi Annual Leave",
			"balance": annual_balance.get("balance"),
			"entitled": annual_balance.get("entitled"),
			"taken": annual_balance.get("taken"),
		},
		"sick": {
			"label": "Sick Leave / إجازة مرضية",
			"doctype": "Saudi Sick Leave",
			"requires_attachments": True,
		},
		"special": {
			"label": "Special Leave / إجازة خاصة",
			"doctype": "Special Leave",
			"options": SPECIAL_LEAVE_OPTIONS,
			"requires_attachments": True,
		},
		"maternity_paternity": {
			"label": "Maternity / Paternity / أمومة وأبوة",
			"doctype": "Maternity Paternity Leave",
			"options": list(LEAVE_DAYS.keys()),
			"requires_attachments": True,
		},
	}


def _get_mobile_leave_base_fields(employee, profile):
	return {
		"employee": employee,
		"employee_name": profile.employee_name,
		"company": profile.company,
		"department": profile.department,
	}


def _build_mobile_leave_doc(employee, profile, request_type, attachments, payload):
	base_fields = _get_mobile_leave_base_fields(employee, profile)

	if request_type == "annual":
		return frappe.get_doc(
			{
				"doctype": "Saudi Annual Leave",
				**base_fields,
				"leave_start_date": payload["start_date"],
				"leave_end_date": payload["end_date"] or payload["start_date"],
				"half_day": int(payload.get("half_day") or 0),
				"description": payload.get("reason") or "",
			}
		)

	if request_type == "sick":
		return frappe.get_doc(
			{
				"doctype": "Saudi Sick Leave",
				**base_fields,
				"from_date": payload["start_date"],
				"to_date": payload["end_date"] or payload["start_date"],
				"medical_certificate_no": payload.get("medical_certificate_no"),
				"hospital_name": payload.get("hospital_name"),
				"medical_certificate_attached": 1 if attachments else 0,
			}
		)

	if request_type == "special":
		return frappe.get_doc(
			{
				"doctype": "Special Leave",
				**base_fields,
				"leave_type": payload.get("leave_subtype"),
				"leave_start_date": payload["start_date"],
				"leave_end_date": payload["end_date"] or payload["start_date"],
				"relationship_to_deceased": payload.get("relationship_to_deceased"),
				"documentation_attached": 1 if attachments else 0,
				"notes": payload.get("reason") or "",
			}
		)

	if request_type == "maternity_paternity":
		return frappe.get_doc(
			{
				"doctype": "Maternity Paternity Leave",
				**base_fields,
				"leave_type": payload.get("leave_subtype"),
				"leave_start_date": payload["start_date"],
				"expected_delivery_date": payload.get("expected_delivery_date"),
				"actual_delivery_date": payload.get("actual_delivery_date"),
				"hospital_name": payload.get("hospital_name"),
				"medical_certificate_attached": 1 if attachments else 0,
			}
		)

	frappe.throw(_("نوع طلب الإجازة غير مدعوم."))


def _docstatus_label(docstatus):
	if docstatus == 1:
		return "Submitted / مرسلة"
	if docstatus == 2:
		return "Cancelled / ملغاة"
	return "Draft / مسودة"


def _get_recent_leave_requests(employee, limit=8):
	rows = []

	for row in frappe.get_all(
		"Saudi Annual Leave",
		filters={"employee": employee},
		fields=["name", "status", "leave_start_date", "leave_end_date", "total_leave_days", "creation", "docstatus"],
		order_by="creation desc",
		limit=limit,
	):
		rows.append(
			{
				"name": row.name,
				"category": "Annual Leave / إجازة سنوية",
				"status": row.status,
				"from_date": row.leave_start_date,
				"to_date": row.leave_end_date,
				"days": flt(row.total_leave_days),
				"created_at": str(row.creation),
			}
		)

	for doctype, category, start_field, end_field, days_field, subtype_field, status_field in [
		("Saudi Sick Leave", "Sick Leave / إجازة مرضية", "from_date", "to_date", "total_days", None, None),
		("Special Leave", "Special Leave / إجازة خاصة", "leave_start_date", "leave_end_date", "actual_days", "leave_type", "status"),
		("Maternity Paternity Leave", "Maternity / Paternity / أمومة وأبوة", "leave_start_date", "leave_end_date", "entitled_days", "leave_type", None),
	]:
		fields = ["name", start_field, end_field, days_field, "creation", "docstatus"]
		if subtype_field:
			fields.append(subtype_field)
		if status_field:
			fields.append(status_field)

		for row in frappe.get_all(doctype, filters={"employee": employee}, fields=fields, order_by="creation desc", limit=limit):
			rows.append(
				{
					"name": row.name,
					"category": category,
					"subtype": getattr(row, subtype_field, None) if subtype_field else None,
					"status": getattr(row, status_field, None) if status_field else _docstatus_label(row.docstatus),
					"from_date": getattr(row, start_field, None),
					"to_date": getattr(row, end_field, None),
					"days": flt(getattr(row, days_field, 0) or 0),
					"created_at": str(row.creation),
				}
			)

	rows.sort(key=lambda item: item["created_at"], reverse=True)
	return rows[:limit]


def _build_verification_mode(raw_mode, attachments):
	modes = [segment for segment in (raw_mode or "gps").split("+") if segment]
	filenames = [((item or {}).get("filename") or "").lower() for item in (attachments or [])]
	if any(name.endswith((".jpg", ".jpeg", ".png", ".webp")) for name in filenames) and "face" not in modes:
		modes.append("face")
	if any(name.endswith((".webm", ".ogg", ".wav", ".mp3", ".m4a")) for name in filenames) and "voice" not in modes:
		modes.append("voice")
	return "+".join(dict.fromkeys(modes)) or "gps"


@frappe.whitelist()
def get_attendance_status():
	employee, profile = _require_employee_context()
	today_checkins = _get_todays_checkins(employee)

	last_log_type = None
	last_checkin_time = None
	if today_checkins:
		last = today_checkins[-1]
		last_log_type = last.log_type
		last_checkin_time = str(last.time)

	today_attendance = frappe.db.get_value(
		"Saudi Daily Attendance",
		{"employee": employee, "attendance_date": nowdate(), "docstatus": 1},
		["name", "in_time", "out_time", "working_hours", "status", "late_entry", "early_exit"],
		as_dict=True,
	)

	return {
		"employee": employee,
		"employee_name": profile.employee_name,
		"department": profile.department,
		"designation": profile.designation,
		"image": profile.image,
		"branch": profile.branch,
		"last_log_type": last_log_type,
		"last_checkin_time": last_checkin_time,
		"today_checkins": today_checkins,
		"today_attendance": today_attendance,
		"location": _get_location_for_branch(profile.branch),
		"insights": _get_attendance_insights(employee),
		"leave_options": _get_leave_options(employee),
		"recent_leave_requests": _get_recent_leave_requests(employee),
		"verification_features": {
			"max_attachment_count": MAX_MOBILE_ATTACHMENTS,
			"max_attachment_size_mb": int(MAX_MOBILE_ATTACHMENT_SIZE / (1024 * 1024)),
		},
	}


@frappe.whitelist()
def get_attendance_insights(month=None, year=None):
	employee, _profile = _require_employee_context()
	return _get_attendance_insights(employee, month=month, year=year)


@frappe.whitelist()
def do_mobile_checkin(latitude=None, longitude=None, verification_mode=None, verification_note=None, attachments_json=None):
	latitude = _coerce_float(latitude)
	longitude = _coerce_float(longitude)
	attachments = _load_json_param(attachments_json, default=[])

	employee, profile = _require_employee_context()
	branch = profile.branch
	location = _get_location_for_branch(branch)

	if location:
		if latitude is None or longitude is None:
			frappe.throw(_("تعذّر الحصول على إحداثيات GPS. يرجى السماح بإذن الموقع وإعادة المحاولة."))
		distance = _distance_meters(latitude, longitude, flt(location.latitude), flt(location.longitude))
		allowed = location.allowed_radius_meters or 100
		if distance > allowed:
			frappe.throw(
				_("أنت بعيد عن الفرع بمسافة {0} متر. الحد المسموح به هو {1} متر.").format(int(distance), int(allowed))
			)
	else:
		frappe.logger("saudi_hr").warning(
			f"GPS bypass: employee {employee} checked in without location validation (no Attendance Location for branch '{branch}')."
		)

	today_checkins = _get_todays_checkins(employee)
	last_log = today_checkins[-1] if today_checkins else None
	log_type = "OUT" if (last_log and last_log.log_type == "IN") else "IN"
	now = now_datetime()

	checkin = frappe.new_doc("Saudi Employee Checkin")
	checkin.update(
		{
			"employee": employee,
			"log_type": log_type,
			"time": now,
			"latitude": latitude,
			"longitude": longitude,
			"device_id": "mobile-gps",
			"verification_mode": _build_verification_mode(verification_mode, attachments),
			"verification_note": verification_note,
		}
	)
	assert_doctype_permissions("Saudi Employee Checkin", "create", doc=checkin)
	checkin.insert()
	attached_files = _attach_files(checkin, attachments)
	frappe.db.commit()

	result = {
		"success": True,
		"log_type": log_type,
		"checkin_name": checkin.name,
		"checkin_time": str(now),
		"attendance_name": None,
		"attached_files": attached_files,
		"message": _("تم تسجيل الحضور بنجاح في {0}").format(now.strftime("%H:%M"))
		if log_type == "IN"
		else _("تم تسجيل الانصراف بنجاح في {0}").format(now.strftime("%H:%M")),
	}

	if log_type == "OUT":
		in_checkin = next((item for item in reversed(today_checkins) if item.log_type == "IN"), None)
		if in_checkin:
			in_time = get_datetime(in_checkin.time)
			out_time = now
			working_hours = time_diff_in_hours(out_time, in_time)

			existing = frappe.db.get_value(
				"Saudi Daily Attendance",
				{"employee": employee, "attendance_date": nowdate(), "docstatus": 1},
				"name",
			)
			if not existing:
				attendance = frappe.new_doc("Saudi Daily Attendance")
				attendance.update(
					{
						"employee": employee,
						"attendance_date": nowdate(),
						"status": "Present / حاضر",
						"working_hours": round(working_hours, 2),
						"in_time": in_time,
						"out_time": out_time,
						"early_exit": 1 if working_hours < _get_contract_hours_per_day(employee) else 0,
					}
				)
				assert_doctype_permissions("Saudi Daily Attendance", ("create", "submit"), doc=attendance)
				attendance.insert()
				attendance.submit()

				all_log_names = [item.name for item in today_checkins] + [checkin.name]
				for log_name in all_log_names:
					frappe.db.set_value("Saudi Employee Checkin", log_name, "attendance", attendance.name)
				frappe.db.commit()

				result["attendance_name"] = attendance.name
				result["working_hours"] = round(working_hours, 2)
				result["message"] = _("تم تسجيل الانصراف. مجموع ساعات العمل: {0} ساعة.").format(
					round(working_hours, 2)
				)

	return result


@frappe.whitelist()
def submit_mobile_leave_request(
	request_type,
	start_date,
	end_date=None,
	reason=None,
	leave_subtype=None,
	relationship_to_deceased=None,
	medical_certificate_no=None,
	hospital_name=None,
	expected_delivery_date=None,
	actual_delivery_date=None,
	half_day=0,
	attachments_json=None,
):
	employee, profile = _require_employee_context()
	attachments = _load_json_param(attachments_json, default=[])
	request_type = (request_type or "").strip()
	doc = _build_mobile_leave_doc(
		employee,
		profile,
		request_type,
		attachments,
		{
			"start_date": start_date,
			"end_date": end_date,
			"reason": reason,
			"leave_subtype": leave_subtype,
			"relationship_to_deceased": relationship_to_deceased,
			"medical_certificate_no": medical_certificate_no,
			"hospital_name": hospital_name,
			"expected_delivery_date": expected_delivery_date,
			"actual_delivery_date": actual_delivery_date,
			"half_day": half_day,
		},
	)

	assert_doctype_permissions(doc.doctype, "create", doc=doc)
	doc.insert()
	attached_files = _attach_files(doc, attachments)
	frappe.db.commit()

	return {
		"doctype": doc.doctype,
		"name": doc.name,
		"attached_files": attached_files,
		"message": _("تم حفظ طلب الإجازة بنجاح وهو الآن بانتظار المراجعة."),
	}


@frappe.whitelist()
def resolve_location_reference_api(plus_code=None, latitude=None, longitude=None, geolocation=None, address_reference=None):
	_require_employee_context()

	return resolve_location_reference(
		plus_code=plus_code,
		latitude=latitude,
		longitude=longitude,
		geolocation=geolocation,
		address_reference=address_reference,
	)


@frappe.whitelist()
def get_available_locations():
	employee, profile = _require_employee_context()
	branch = profile.branch
	filters = {"is_active": 1}
	if not ELEVATED_ROLES.intersection(set(frappe.get_roles())):
		filters["branch"] = branch

	return frappe.get_all(
		"Attendance Location",
		filters=filters,
		fields=[
			"name",
			"location_name",
			"branch",
			"latitude",
			"longitude",
			"allowed_radius_meters",
			"plus_code",
			"location_source",
		],
		order_by="location_name asc",
	)


@frappe.whitelist()
def sync_branch_employee_directory():
	from saudi_hr.saudi_hr.doctype.saudi_hr_settings.saudi_hr_settings import sync_branch_employee_directory as _sync

	return _sync()


@frappe.whitelist()
def download_employee_branch_template():
	from saudi_hr.saudi_hr.doctype.saudi_hr_settings.saudi_hr_settings import (
		download_employee_branch_template as _download,
	)

	return _download()


@frappe.whitelist()
def import_employee_branch_template(file_url=None):
	from saudi_hr.saudi_hr.doctype.saudi_hr_settings.saudi_hr_settings import import_employee_branch_template as _import

	return _import(file_url=file_url)
