// Copyright (c) 2026, Saudi HR
// Work Injury - Client Script
// نظام العمل السعودي م.148-156: إصابات العمل

frappe.ui.form.on('Work Injury', {

    onload(frm) {
        if (frm.is_new()) {
            frm.set_value('injury_date', frappe.datetime.get_today());
            frm.set_value('status', 'Draft / مسودة');
        }
        _add_gosi_button(frm);
    },

    refresh(frm) {
        _add_gosi_button(frm);
        // تحذير إذا مضى أكثر من 3 أيام دون إبلاغ GOSI
        if (!frm.doc.gosi_form_25_submitted && frm.doc.injury_date) {
            const days = frappe.datetime.get_diff(frappe.datetime.get_today(), frm.doc.injury_date);
            if (days > 3) {
                frm.dashboard.add_comment(
                    __(`⚠ Injury reported ${days} days ago. GOSI Form 25 must be filed within 3 working days (Art. 150).<br>⚠ مرّ ${days} يوماً على الإصابة. يجب تقديم نموذج GOSI 25 خلال 3 أيام عمل (م.150).`),
                    'red', true
                );
            }
        }
    },

    employee(frm) {
        if (!frm.doc.employee) return;
        frappe.db.get_value('Employee', frm.doc.employee,
            ['employee_name', 'company', 'department'],
            (r) => {
                frm.set_value('employee_name', r.employee_name);
                frm.set_value('company', r.company);
                frm.set_value('department', r.department);
            }
        );
    },

    injury_date(frm) {
        if (!frm.doc.injury_date) return;
        const deadline = frappe.datetime.add_days(frm.doc.injury_date, 3);
        const today = frappe.datetime.get_today();
        if (frappe.datetime.get_diff(today, frm.doc.injury_date) > 3
                && !frm.doc.gosi_form_25_submitted) {
            frappe.show_alert({
                message: __(`GOSI reporting deadline was ${deadline}. Please submit Form 25 immediately.<br>الموعد النهائي لإبلاغ GOSI كان ${deadline}. قدّم نموذج 25 فوراً.`),
                indicator: 'red'
            }, 7);
        }
    },

    gosi_form_25_submitted(frm) {
        if (frm.doc.gosi_form_25_submitted && !frm.doc.gosi_submission_date) {
            frm.set_value('gosi_submission_date', frappe.datetime.get_today());
        }
    },

    severity(frm) {
        if (frm.doc.severity === 'Fatal / وفاة') {
            frappe.show_alert({
                message: __('Fatal injury: Notify GOSI and relevant authorities immediately per Art. 156.<br>وفاة: أخطر GOSI والجهات المختصة فوراً وفقاً لمادة 156.'),
                indicator: 'red'
            }, 8);
        }
    },
});


function _add_gosi_button(frm) {
    if (frm.doc.docstatus === 0 && !frm.doc.gosi_form_25_submitted) {
        frm.add_custom_button(__('Mark GOSI Form 25 Submitted / تم تقديم نموذج 25'), function() {
            frm.set_value('gosi_form_25_submitted', 1);
            frm.set_value('gosi_submission_date', frappe.datetime.get_today());
            frm.set_value('status', 'Reported to GOSI / أُبلغت به GOSI');
            frm.save();
        }, __('Actions'));
    }
}
