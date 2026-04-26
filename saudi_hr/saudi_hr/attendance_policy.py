import frappe
from frappe.utils import add_to_date, get_datetime, get_time, getdate


VOICE_POLICY_DISABLED = "Disabled / معطل"
VOICE_POLICY_OPTIONAL = "Optional / اختياري"
VOICE_POLICY_REQUIRED = "Required / إلزامي"


def _get_shift_assignment(employee, attendance_date):
	assignment = frappe.db.get_value(
		"Shift Assignment",
		{
			"employee": employee,
			"status": "Active",
			"docstatus": 1,
			"start_date": ["<=", attendance_date],
			"end_date": ["in", ["", None]],
		},
		["name", "shift_type", "start_date", "end_date"],
		as_dict=True,
	)
	if assignment or not frappe.db.exists("DocType", "Shift Assignment"):
		return assignment

	rows = frappe.db.sql(
		"""
		SELECT name, shift_type, start_date, end_date
		FROM `tabShift Assignment`
		WHERE employee = %s
		  AND status = 'Active'
		  AND docstatus = 1
		  AND start_date <= %s
		  AND (end_date IS NULL OR end_date = '' OR end_date >= %s)
		ORDER BY start_date DESC, modified DESC
		LIMIT 1
		""",
		(employee, attendance_date, attendance_date),
		as_dict=True,
	)
	return rows[0] if rows else None


def _get_shift_type(shift_type):
	if not shift_type:
		return None
	return frappe.db.get_value(
		"Shift Type",
		shift_type,
		[
			"name",
			"start_time",
			"end_time",
			"begin_check_in_before_shift_start_time",
			"allow_check_out_after_shift_end_time",
			"enable_late_entry_marking",
			"late_entry_grace_period",
			"enable_early_exit_marking",
			"early_exit_grace_period",
		],
		as_dict=True,
	)


def _combine_shift_datetime(attendance_date, time_value):
	if not time_value:
		return None
	attendance_date = getdate(attendance_date)
	time_value = get_time(time_value)
	return get_datetime(f"{attendance_date} {time_value}")


def _build_schedule_window(attendance_date, shift_type_doc):
	if not shift_type_doc:
		return {}

	start_dt = _combine_shift_datetime(attendance_date, shift_type_doc.start_time)
	end_dt = _combine_shift_datetime(attendance_date, shift_type_doc.end_time)
	if start_dt and end_dt and end_dt <= start_dt:
		end_dt = add_to_date(end_dt, days=1)

	checkin_window_start = add_to_date(
		start_dt,
		minutes=-(shift_type_doc.begin_check_in_before_shift_start_time or 0),
	) if start_dt else None
	checkout_window_end = add_to_date(
		end_dt,
		minutes=(shift_type_doc.allow_check_out_after_shift_end_time or 0),
	) if end_dt else None
	late_after = add_to_date(start_dt, minutes=(shift_type_doc.late_entry_grace_period or 0)) if start_dt else None
	early_before = add_to_date(end_dt, minutes=-(shift_type_doc.early_exit_grace_period or 0)) if end_dt else None

	return {
		"expected_start": start_dt,
		"expected_end": end_dt,
		"checkin_window_start": checkin_window_start,
		"checkout_window_end": checkout_window_end,
		"late_after": late_after,
		"early_before": early_before,
	}


def summarize_schedule_status(policy, reference_time=None, last_log_type=None):
	reference_time = get_datetime(reference_time) if reference_time else get_datetime()
	expected_start = policy.get("expected_start")
	expected_end = policy.get("expected_end")
	checkin_window_start = policy.get("checkin_window_start") or expected_start
	checkout_window_end = policy.get("checkout_window_end") or expected_end

	if not expected_start or not expected_end:
		return {
			"code": "unscheduled",
			"label": "No scheduled shift / لا توجد وردية مجدولة",
			"minutes_until_start": None,
			"minutes_until_end": None,
		}

	minutes_until_start = max(0, int((expected_start - reference_time).total_seconds() // 60))
	minutes_until_end = max(0, int((expected_end - reference_time).total_seconds() // 60))

	if checkin_window_start and reference_time < checkin_window_start:
		code = "before_checkin_window"
		label = "Before check-in window / قبل نافذة الحضور"
	elif reference_time < expected_start:
		code = "checkin_window_open"
		label = "Check-in window open / نافذة الحضور مفتوحة"
	elif reference_time < expected_end:
		code = "shift_in_progress"
		if last_log_type == "OUT":
			label = "Checked out before shift end / تم الانصراف قبل نهاية الوردية"
		else:
			label = "Shift in progress / الوردية جارية"
	elif checkout_window_end and reference_time <= checkout_window_end:
		code = "checkout_window_open"
		label = "Checkout window open / نافذة الانصراف مفتوحة"
	else:
		code = "shift_closed"
		label = "Shift closed / الوردية مغلقة"

	return {
		"code": code,
		"label": label,
		"minutes_until_start": minutes_until_start,
		"minutes_until_end": minutes_until_end,
	}


def resolve_mobile_attendance_policy(employee, attendance_date, location=None):
	attendance_date = getdate(attendance_date)
	assignment = _get_shift_assignment(employee, attendance_date)
	shift_type_name = assignment.shift_type if assignment else None
	policy_source = "Shift Assignment"

	if not shift_type_name and location:
		shift_type_name = location.get("default_shift_type")
		policy_source = "Attendance Location"

	shift_type_doc = _get_shift_type(shift_type_name)
	window = _build_schedule_window(attendance_date, shift_type_doc)

	voice_policy = (location or {}).get("voice_verification_policy") or VOICE_POLICY_DISABLED
	voice_ttl = int((location or {}).get("voice_challenge_ttl_seconds") or 300)
	voice_max_duration = int((location or {}).get("voice_max_duration_seconds") or 15)

	return {
		"policy_source": policy_source if shift_type_doc else "Contract Hours",
		"shift_assignment": assignment.name if assignment else None,
		"shift_type": shift_type_doc.name if shift_type_doc else None,
		"expected_start": window.get("expected_start"),
		"expected_end": window.get("expected_end"),
		"checkin_window_start": window.get("checkin_window_start"),
		"checkout_window_end": window.get("checkout_window_end"),
		"late_after": window.get("late_after"),
		"early_before": window.get("early_before"),
		"enforce_schedule": int((location or {}).get("enforce_schedule") or 0),
		"voice_policy": voice_policy,
		"voice_challenge_ttl_seconds": max(30, voice_ttl),
		"voice_max_duration_seconds": max(5, voice_max_duration),
	}


def calculate_attendance_variance(log_type, event_time, policy):
	late_minutes = 0
	early_exit_minutes = 0

	if log_type == "IN" and policy.get("expected_start") and event_time > policy["expected_start"]:
		late_minutes = max(0, int((event_time - policy["expected_start"]).total_seconds() // 60))
		if policy.get("late_after") and event_time <= policy["late_after"]:
			late_minutes = 0

	if log_type == "OUT" and policy.get("expected_end") and event_time < policy["expected_end"]:
		early_exit_minutes = max(0, int((policy["expected_end"] - event_time).total_seconds() // 60))
		if policy.get("early_before") and event_time >= policy["early_before"]:
			early_exit_minutes = 0

	return {
		"late_minutes": late_minutes,
		"early_exit_minutes": early_exit_minutes,
		"late_entry": 1 if late_minutes > 0 else 0,
		"early_exit": 1 if early_exit_minutes > 0 else 0,
	}