"""
tasks.py — Scheduled Tasks for daily alerts.
"""
import frappe
from frappe.utils import today, add_days, getdate


DEFAULT_ALERT_MILESTONES = (30, 14, 7, 1, 0)


def _get_saudi_hr_settings():
	return frappe.get_single("Saudi HR Settings")


def _email_alerts_enabled():
	settings = _get_saudi_hr_settings()
	return bool(settings.send_email_alerts)


def _get_alert_milestones(primary_day: int | None = None) -> set[int]:
	milestones = set(DEFAULT_ALERT_MILESTONES)
	if primary_day is not None:
		milestones.add(int(primary_day))
	return {day for day in milestones if day >= 0}


def _should_send_days_left_alert(days_left: int, primary_day: int | None = None) -> bool:
	return int(days_left) in _get_alert_milestones(primary_day)


def _has_existing_alert(user: str, subject: str, doctype: str, docname=None) -> bool:
	filters = {
		"for_user": user,
		"subject": subject,
		"document_type": doctype,
		"type": "Alert",
	}
	if docname:
		filters["document_name"] = docname
	return bool(frappe.db.exists("Notification Log", filters))


def _get_pending_alert_recipients(recipients, subject: str, doctype: str, docname=None) -> list[str]:
	return [
		user for user in recipients
		if not _has_existing_alert(user, subject, doctype, docname)
	]


def send_iqama_expiry_alerts():
	"""تنبيه انتهاء الإقامة قبل 90 و 30 يوماً."""
	settings = _get_saudi_hr_settings()
	alert_days = settings.iqama_expiry_alert_days or 90

	records = frappe.get_all(
		"Work Permit Iqama",
		filters={
			"iqama_expiry_date": ["between", [today(), add_days(today(), alert_days)]],
			"docstatus": 1,
		},
		fields=["name", "employee", "employee_name", "iqama_expiry_date"],
	)

	for rec in records:
		days_left = (getdate(rec.iqama_expiry_date) - getdate(today())).days
		if not _should_send_days_left_alert(days_left, alert_days):
			continue
		_send_alert(
			subject=f"تنبيه: انتهاء إقامة {rec.employee_name} خلال {days_left} يوم",
			message=f"إقامة الموظف {rec.employee_name} ({rec.employee}) ستنتهي في {rec.iqama_expiry_date}.",
			doctype="Work Permit Iqama",
			docname=rec.name,
		)


def send_contract_expiry_alerts():
	"""تنبيه انتهاء عقود العمل المحددة المدة خلال 60 يوماً."""
	settings = _get_saudi_hr_settings()
	alert_days = settings.contract_expiry_alert_days or 60

	records = frappe.get_all(
		"Saudi Employment Contract",
		filters={
			"contract_type": "محدد المدة / Fixed Term",
			"end_date": ["between", [today(), add_days(today(), alert_days)]],
			"contract_status": "Active / نشط",
		},
		fields=["name", "employee", "employee_name", "end_date"],
	)

	for rec in records:
		days_left = (getdate(rec.end_date) - getdate(today())).days
		if not _should_send_days_left_alert(days_left, alert_days):
			continue
		_send_alert(
			subject=f"تنبيه: انتهاء عقد {rec.employee_name} خلال {days_left} يوم",
			message=f"عقد الموظف {rec.employee_name} ({rec.employee}) ينتهي في {rec.end_date}.",
			doctype="Saudi Employment Contract",
			docname=rec.name,
		)


def send_work_permit_expiry_alerts():
	"""تنبيه انتهاء تصاريح العمل خلال 90 يوماً."""
	settings = _get_saudi_hr_settings()
	alert_days = settings.work_permit_expiry_alert_days or 90

	records = frappe.get_all(
		"Work Permit Iqama",
		filters={
			"work_permit_expiry_date": ["between", [today(), add_days(today(), alert_days)]],
			"docstatus": 1,
		},
		fields=["name", "employee", "employee_name", "work_permit_expiry_date"],
	)

	for rec in records:
		days_left = (getdate(rec.work_permit_expiry_date) - getdate(today())).days
		if not _should_send_days_left_alert(days_left, alert_days):
			continue
		_send_alert(
			subject=f"تنبيه: انتهاء تصريح عمل {rec.employee_name} خلال {days_left} يوم",
			message=f"تصريح عمل {rec.employee_name} ({rec.employee}) ينتهي في {rec.work_permit_expiry_date}.",
			doctype="Work Permit Iqama",
			docname=rec.name,
		)


def send_gosi_due_alerts():
	"""Monthly reminder for unpaid GOSI contributions of the previous payroll month."""
	today_date = getdate(today())
	first_of_month = today_date.replace(day=1)
	previous_month_date = add_days(first_of_month, -1)
	period_month = previous_month_date.strftime("%B")
	period_year = previous_month_date.year

	pending_records = frappe.get_all(
		"GOSI Contribution",
		filters={
			"month": period_month,
			"year": period_year,
			"payment_status": ["!=", "Paid / مدفوع"],
		},
		fields=["name", "employee_name", "company", "total_contribution", "payment_status"],
		order_by="company asc, employee_name asc",
	)

	if not pending_records:
		return

	total_amount = sum((record.total_contribution or 0) for record in pending_records)
	companies = sorted({record.company for record in pending_records if record.company})
	preview = "، ".join(record.employee_name for record in pending_records[:5] if record.employee_name)
	remaining_count = max(0, len(pending_records) - 5)
	if remaining_count:
		preview = f"{preview}، +{remaining_count}" if preview else f"+{remaining_count}"

	message = (
		f"يوجد {len(pending_records)} سجل اشتراك GOSI غير مسدد للفترة {period_month} {period_year}.\n"
		f"إجمالي المبلغ المستحق: {total_amount:,.2f} ريال.\n"
	)
	if companies:
		message += f"الشركات المعنية: {', '.join(companies)}.\n"
	if preview:
		message += f"أمثلة على السجلات: {preview}.\n"
	message += "يرجى مراجعة سجلات GOSI المعلقة وتحديث حالة السداد ورقم المرجع."

	_send_alert(
		subject=f"تنبيه GOSI الشهري: {len(pending_records)} سجل معلق للفترة {period_month} {period_year}",
		message=message,
		doctype="GOSI Contribution",
		docname=pending_records[0].name,
	)


def _send_alert(subject, message, doctype, docname=None):
	"""إرسال تنبيه بريدي + إشعار داخلي لـ HR Manager."""
	hr_managers = frappe.get_all(
		"Has Role",
		filters={"role": "HR Manager", "parenttype": "User"},
		fields=["parent"],
	)
	recipients = [r.parent for r in hr_managers if r.parent != "Guest"]
	recipients = _get_pending_alert_recipients(recipients, subject, doctype, docname)
	if not recipients:
		return

	site_url = frappe.utils.get_url()
	if docname:
		doc_url = f"{site_url}/app/{frappe.scrub(doctype)}/{docname}"
	else:
		doc_url = f"{site_url}/app/{frappe.scrub(doctype)}"

	html_message = f"""
	<div dir="rtl" style="font-family:Arial,Tahoma,sans-serif;font-size:13px;color:#222;padding:20px;">
		<div style="background:#1a5276;color:white;padding:12px 20px;border-radius:5px;margin-bottom:15px;">
			<strong>نظام الموارد البشرية السعودي — Saudi HR</strong>
		</div>
		<p>{message}</p>
		<p style="margin-top:20px;">
			<a href="{doc_url}" style="background:#1a5276;color:white;padding:8px 18px;
			text-decoration:none;border-radius:4px;font-size:13px;">
				عرض المستند ←
			</a>
		</p>
		<hr style="border:1px solid #eee;margin-top:25px;">
		<p style="font-size:11px;color:#888;">هذا البريد تلقائي من نظام الموارد البشرية السعودي</p>
	</div>
	"""

	if recipients and _email_alerts_enabled():
		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message=html_message,
			reference_doctype=doctype,
			reference_name=docname,
		)

	# Internal system notification
	for user in recipients:
		frappe.publish_realtime(
			"eval_js",
			f"frappe.show_alert({{message: '{subject.replace(chr(39), '')}', indicator: 'orange'}})",
			user=user,
		)
		frappe.get_doc({
			"doctype": "Notification Log",
			"subject": subject,
			"email_content": message,
			"document_type": doctype,
			"document_name": docname,
			"for_user": user,
			"type": "Alert",
		}).insert()


def send_sick_leave_threshold_alerts():
	"""تنبيه عند اقتراب الموظف من حد الإجازة المرضية 90 يوماً."""
	from frappe.utils import getdate
	import datetime

	year = getdate(frappe.utils.today()).year
	# Find employees with 75-90 sick days this year
	results = frappe.db.sql("""
		SELECT employee, employee_name, SUM(total_days) as total_sick
		FROM `tabSaudi Sick Leave`
		WHERE YEAR(from_date) = %s AND docstatus = 1
		GROUP BY employee
		HAVING total_sick BETWEEN 75 AND 120
	""", (year,), as_dict=True)

	for rec in results:
		# Find the most recent sick leave record for the employee to use as doc link
		latest_doc = frappe.db.sql(
			"""SELECT name FROM `tabSaudi Sick Leave`
			   WHERE employee=%s AND YEAR(from_date)=%s AND docstatus=1
			   ORDER BY from_date DESC LIMIT 1""",
			(rec.employee, year),
			as_list=True,
		)
		_send_alert(
			subject=f"تنبيه: {rec.employee_name} اقترب من الحد الأقصى للإجازة المرضية ({int(rec.total_sick)} يوم)",
			message=f"الموظف {rec.employee_name} استنفد {int(rec.total_sick)} يوماً مرضياً هذا العام. الحد الأقصى 120 يوماً (م.117).",
			doctype="Saudi Sick Leave",
			docname=latest_doc[0][0] if latest_doc else "",
		)


def send_probation_end_alerts():
	"""تنبيه انتهاء فترة التجربة قبل 14 يوماً (م.53 نظام العمل).
	Alert HR Manager + direct manager when probation ends within 14 days.
	"""
	two_weeks_ahead = add_days(today(), 14)
	records = frappe.get_all(
		"Saudi Employment Contract",
		filters={
			"probation_end_date": ["between", [today(), two_weeks_ahead]],
			"contract_status": "Active / نشط",
		},
		fields=["name", "employee", "employee_name", "probation_end_date", "probation_period_months"],
	)

	for rec in records:
		days_left = (getdate(rec.probation_end_date) - getdate(today())).days
		if not _should_send_days_left_alert(days_left, 14):
			continue
		_send_alert(
			subject=(
				f"تنبيه فترة التجربة: {rec.employee_name} — تنتهي خلال {days_left} يوم"
			),
			message=(
				f"فترة تجربة الموظف {rec.employee_name} ({rec.employee}) ستنتهي في "
				f"{rec.probation_end_date} (خلال {days_left} يوم).\n\n"
				"يُرجى اتخاذ القرار بشأن تثبيته أو إنهاء خدمته قبل انتهاء فترة التجربة "
				"وفقاً لنظام العمل السعودي م.53."
			),
			doctype="Saudi Employment Contract",
			docname=rec.name,
		)
