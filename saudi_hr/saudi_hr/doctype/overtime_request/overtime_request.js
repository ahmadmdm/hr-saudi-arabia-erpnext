// Copyright (c) 2026, Saudi HR and contributors
// Overtime Request - Client Script

frappe.ui.form.on('Overtime Request', {

    onload(frm) {
        if (frm.is_new()) {
            frm.set_value('date', frappe.datetime.get_today());
            frm.set_value('approval_status', 'Pending / معلق');
            frm.set_value('compensation_method', 'Cash Payment / بدل نقدي');
        }
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
                frm.set_value('department', emp.department);
                // Fetch the actual and basic wages used by Article 107.
                frappe.call({
                    method: 'saudi_hr.saudi_hr.doctype.overtime_request.overtime_request.get_employee_overtime_salary',
                    args: { employee: frm.doc.employee },
                    callback(s) {
                        if (s.message) {
                            frm.set_value('monthly_basic', s.message.basic_salary);
                            frm.set_value('monthly_actual_wage', s.message.total_salary || s.message.basic_salary);
                            _calc_hourly_rate(frm);
                        }
                    }
                });
            }
        });
    },

    monthly_basic(frm) { _calc_hourly_rate(frm); },
    monthly_actual_wage(frm) { _calc_hourly_rate(frm); },
    compensation_method(frm) { _set_compensation(frm); },

    shift_start(frm) { _calc_overtime_hours(frm); },
    shift_end(frm)   { _calc_overtime_hours(frm); },
    normal_hours(frm){ _calc_overtime_hours(frm); },

    overtime_hours(frm) { _calc_amount(frm); },
    hourly_rate(frm)    { _calc_amount(frm); },
});


function _calc_hourly_rate(frm) {
    const basic = flt(frm.doc.monthly_basic);
    const actual = flt(frm.doc.monthly_actual_wage) || basic;
    if (!basic || !actual) return;
    const basic_hourly = basic / 240;
    const actual_hourly = actual / 240;
    const premium = basic_hourly * 0.5;
    const payable_hourly = actual_hourly + premium;
    frm.set_value('basic_hourly_rate', flt(basic_hourly.toFixed(4)));
    frm.set_value('actual_hourly_rate', flt(actual_hourly.toFixed(4)));
    frm.set_value('overtime_premium_hourly', flt(premium.toFixed(4)));
    frm.set_value('hourly_rate', flt(payable_hourly.toFixed(4)));
    frm.set_value('overtime_rate', flt((payable_hourly / basic_hourly).toFixed(4)));
    _calc_amount(frm);
}

function _calc_overtime_hours(frm) {
    if (!frm.doc.shift_start || !frm.doc.shift_end) return;

    const start = frappe.datetime.str_to_obj(frm.doc.date + ' ' + frm.doc.shift_start);
    let   end   = frappe.datetime.str_to_obj(frm.doc.date + ' ' + frm.doc.shift_end);

    if (!start || !end) return;

    // Handle overnight shifts
    if (end < start) {
        end = new Date(end.getTime() + 24 * 60 * 60 * 1000);
    }

    const total_hours = (end - start) / (1000 * 60 * 60);
    const normal      = flt(frm.doc.normal_hours) || 8;
    const overtime    = Math.max(0, flt((total_hours - normal).toFixed(2)));

    frm.set_value('overtime_hours', overtime);
    _calc_amount(frm);
}

function _calc_amount(frm) {
    const hourly   = flt(frm.doc.hourly_rate);
    const ot_hours = flt(frm.doc.overtime_hours);
    const is_leave = frm.doc.compensation_method === 'Compensatory Leave / إجازة تعويضية';
    const amount   = is_leave ? 0 : flt((hourly * ot_hours).toFixed(2));
    frm.set_value('overtime_amount', amount);
    const factor = 1.5;
    const leave_hours = is_leave ? flt((ot_hours * factor).toFixed(2)) : 0;
    const normal_hours = flt(frm.doc.normal_hours) || 8;
    frm.set_value('compensatory_leave_factor', factor);
    frm.set_value('compensatory_leave_hours', leave_hours);
    frm.set_value('compensatory_leave_days', is_leave ? flt((leave_hours / normal_hours).toFixed(4)) : 0);
    frm.set_value('compensatory_leave_use_by', is_leave && frm.doc.date
        ? frappe.datetime.add_days(frm.doc.date, 60)
        : null);
}

function _set_compensation(frm) {
    const is_leave = frm.doc.compensation_method === 'Compensatory Leave / إجازة تعويضية';
    frm.toggle_reqd('written_consent_reference', is_leave);
    _calc_amount(frm);
}
