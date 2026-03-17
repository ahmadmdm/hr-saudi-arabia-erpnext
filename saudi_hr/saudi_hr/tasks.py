"""
tasks.py — Scheduled Tasks for daily alerts.
"""
import frappe
from frappe.utils import today, add_days, getdate


def send_iqama_expiry_alerts():
	"""تنبيه انتهاء الإقامة قبل 90 و 30 يوماً."""
	settings = frappe.get_single("Saudi HR Settings")
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
		_send_alert(
			subject=f"تنبيه: انتهاء إقامة {rec.employee_name} خلال {days_left} يوم",
			message=f"إقامة الموظف {rec.employee_name} ({rec.employee}) ستنتهي في {rec.iqama_expiry_date}.",
			doctype="Work Permit Iqama",
			docname=rec.name,
		)


def send_contract_expiry_alerts():
	"""تنبيه انتهاء عقود العمل المحددة المدة خلال 60 يوماً."""
	records = frappe.get_all(
		"Saudi Employment Contract",
		filters={
			"contract_type": "محدد المدة / Fixed Term",
			"end_date": ["between", [today(), add_days(today(), 60)]],
			"contract_status": "Active / نشط",
		},
		fields=["name", "employee", "employee_name", "end_date"],
	)

	for rec in records:
		days_left = (getdate(rec.end_date) - getdate(today())).days
		_send_alert(
			subject=f"تنبيه: انتهاء عقد {rec.employee_name} خلال {days_left} يوم",
			message=f"عقد الموظف {rec.employee_name} ({rec.employee}) ينتهي في {rec.end_date}.",
			doctype="Saudi Employment Contract",
			docname=rec.name,
		)


def send_work_permit_expiry_alerts():
	"""تنبيه انتهاء تصاريح العمل خلال 90 يوماً."""
	records = frappe.get_all(
		"Work Permit Iqama",
		filters={
			"work_permit_expiry_date": ["between", [today(), add_days(today(), 90)]],
			"docstatus": 1,
		},
		fields=["name", "employee", "employee_name", "work_permit_expiry_date"],
	)

	for rec in records:
		days_left = (getdate(rec.work_permit_expiry_date) - getdate(today())).days
		_send_alert(
			subject=f"تنبيه: انتهاء تصريح عمل {rec.employee_name} خلال {days_left} يوم",
			message=f"تصريح عمل {rec.employee_name} ({rec.employee}) ينتهي في {rec.work_permit_expiry_date}.",
			doctype="Work Permit Iqama",
			docname=rec.name,
		)


def _send_alert(subject, message, doctype, docname):
	"""إرسال تنبيه بريدي + إشعار داخلي لـ HR Manager."""
	hr_managers = frappe.get_all(
		"Has Role",
		filters={"role": "HR Manager", "parenttype": "User"},
		fields=["parent"],
	)
	recipients = [r.parent for r in hr_managers if r.parent != "Guest"]

	site_url = frappe.utils.get_url()
	doc_url = f"{site_url}/app/{frappe.scrub(doctype)}/{docname}"

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

	if recipients:
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
		}).insert(ignore_permissions=True)


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
		_send_alert(
			subject=f"تنبيه: {rec.employee_name} اقترب من الحد الأقصى للإجازة المرضية ({int(rec.total_sick)} يوم)",
			message=f"الموظف {rec.employee_name} استنفد {int(rec.total_sick)} يوماً مرضياً هذا العام. الحد الأقصى 120 يوماً (م.117).",
			doctype="Saudi Sick Leave",
			docname="",
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
