// Copyright (c) 2026, Saudi HR and contributors
// GOSI Contribution - Client Script

const MONTHS = [
    ['January / يناير', 'January / يناير'],
    ['February / فبراير', 'February / فبراير'],
    ['March / مارس', 'March / مارس'],
    ['April / أبريل', 'April / أبريل'],
    ['May / مايو', 'May / مايو'],
    ['June / يونيو', 'June / يونيو'],
    ['July / يوليو', 'July / يوليو'],
    ['August / أغسطس', 'August / أغسطس'],
    ['September / سبتمبر', 'September / سبتمبر'],
    ['October / أكتوبر', 'October / أكتوبر'],
    ['November / نوفمبر', 'November / نوفمبر'],
    ['December / ديسمبر', 'December / ديسمبر'],
];

frappe.ui.form.on('GOSI Contribution', {

    onload(frm) {
        if (frm.is_new()) {
            const today = frappe.datetime.get_today();
            frm.set_value('year', parseInt(today.split('-')[0]));
            frm.set_value('payment_status', 'Pending');
        }
        frm.add_custom_button(__('Generate for All Employees / توليد للكل'), function() {
            _generate_for_all(frm);
        }, __('Actions'));
    },

    employee(frm) {
        if (!frm.doc.employee) return;
        frappe.call({
            method: 'frappe.client.get',
            args: { doctype: 'Employee', name: frm.doc.employee },
            callback(r) {
                if (!r.message) return;
                const emp = r.message;
                frm.set_value('employee_name', emp.employee_name);
                frm.set_value('company', emp.company);
                frm.set_value('nationality', emp.nationality || '');
                // Fetch basic salary as contribution base
                frappe.call({
                    method: 'saudi_hr.saudi_hr.doctype.gosi_contribution.gosi_contribution.get_employee_basic_salary',
                    args: { employee: frm.doc.employee },
                    callback(s) {
                        if (s.message) {
                            frm.set_value('contribution_base', s.message);
                        }
                        _apply_rates(frm);
                    }
                });
            }
        });
    },

    nationality(frm) { _apply_rates(frm); },

    contribution_base(frm)          { _calc_contributions(frm); },
    employee_contribution_rate(frm) { _calc_contributions(frm); },
    employer_contribution_rate(frm) { _calc_contributions(frm); },

    month(frm) { _set_period_label(frm); },
    year(frm)  { _set_period_label(frm); },
});


function _apply_rates(frm) {
    const nat = (frm.doc.nationality || '').toLowerCase();
    const is_saudi = ['saudi', 'سعودي', 'sa', 'saudi arabia'].includes(nat);
    if (is_saudi) {
        frm.set_value('employee_contribution_rate', 10.0);
        frm.set_value('employer_contribution_rate', 12.0);
    } else {
        frm.set_value('employee_contribution_rate', 0.0);
        frm.set_value('employer_contribution_rate', 2.0);
    }
    _calc_contributions(frm);
}

function _calc_contributions(frm) {
    const base = flt(frm.doc.contribution_base);
    const capped = Math.min(base, 45000);
    if (base > 45000) {
        frm.set_value('contribution_base', 45000);
    }
    const emp_cont  = flt((capped * flt(frm.doc.employee_contribution_rate) / 100).toFixed(2));
    const er_cont   = flt((capped * flt(frm.doc.employer_contribution_rate)  / 100).toFixed(2));
    frm.set_value('employee_contribution', emp_cont);
    frm.set_value('employer_contribution', er_cont);
    frm.set_value('total_contribution', flt((emp_cont + er_cont).toFixed(2)));
}

function _set_period_label(frm) {
    if (frm.doc.month && frm.doc.year) {
        frm.set_value('period_label', `${frm.doc.month} ${frm.doc.year}`);
    }
}

function _generate_for_all(frm) {
    if (!frm.doc.company || !frm.doc.month || !frm.doc.year) {
        frappe.msgprint(__('Please fill Company, Month and Year first.<br>يرجى تعبئة الشركة والشهر والسنة أولاً.'), 'Missing Fields');
        return;
    }
    frappe.confirm(
        __(`Generate GOSI records for all active employees of ${frm.doc.company} for ${frm.doc.month} ${frm.doc.year}?<br>إنشاء سجلات GOSI لجميع موظفي ${frm.doc.company} لشهر ${frm.doc.month} ${frm.doc.year}؟`),
        function() {
            frappe.call({
                method: 'saudi_hr.saudi_hr.doctype.gosi_contribution.gosi_contribution.generate_gosi_for_month',
                args: {
                    company: frm.doc.company,
                    month: frm.doc.month,
                    year: frm.doc.year,
                },
                freeze: true,
                freeze_message: __('Generating GOSI records... / جارٍ إنشاء السجلات...'),
                callback(r) {
                    if (r.message !== undefined) {
                        frappe.msgprint(
                            __(`Created ${r.message} GOSI record(s).<br>تم إنشاء ${r.message} سجل GOSI.`),
                            'Done / اكتمل'
                        );
                    }
                }
            });
        }
    );
}
