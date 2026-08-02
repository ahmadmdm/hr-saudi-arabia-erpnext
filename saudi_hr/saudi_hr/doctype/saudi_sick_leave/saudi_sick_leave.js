// Copyright (c) 2026, Saudi HR and contributors
// Saudi Sick Leave - Client Script
// نظام العمل السعودي م.117: 30 يوم بأجر كامل، 60 يوم بـ 75%، 30 يوم بدون أجر

frappe.ui.form.on('Saudi Sick Leave', {

    onload(frm) {
        if (frm.is_new()) {
            frm.set_value('from_date', frappe.datetime.get_today());
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
                _refresh_cycle(frm);
                // Fetch daily salary
                frappe.call({
                    method: 'saudi_hr.saudi_hr.doctype.saudi_sick_leave.saudi_sick_leave.get_daily_salary',
                    args: { employee: frm.doc.employee },
                    callback(s) {
                        if (s.message) frm.set_value('daily_salary', s.message);
                        _calc_pay(frm);
                    }
                });
            }
        });
    },

    from_date(frm) { _calc_days(frm); _refresh_cycle(frm); },
    to_date(frm)   { _calc_days(frm); },

    total_days(frm)                  { _calc_pay(frm); },
    sick_days_this_year_before(frm)  { _calc_pay(frm); },
    daily_salary(frm)                { _calc_pay(frm); },
});


function _calc_days(frm) {
    if (!frm.doc.from_date || !frm.doc.to_date) return;
    if (frm.doc.to_date < frm.doc.from_date) {
        frappe.msgprint(__('To Date cannot be before From Date / تاريخ النهاية لا يسبق تاريخ البداية'));
        frm.set_value('to_date', frm.doc.from_date);
        return;
    }
    const days = frappe.datetime.get_day_diff(frm.doc.to_date, frm.doc.from_date) + 1;
    frm.set_value('total_days', days);
    _set_cycle_boundary_review(frm);
}

function _refresh_cycle(frm) {
    if (!frm.doc.employee || !frm.doc.from_date) return;
    frappe.call({
        method: 'saudi_hr.saudi_hr.doctype.saudi_sick_leave.saudi_sick_leave.get_sick_leave_cycle',
        args: {
            employee: frm.doc.employee,
            from_date: frm.doc.from_date,
            exclude_doc: frm.doc.name || ''
        },
        callback(r) {
            const cycle = r.message || {};
            frm.set_value('benefit_cycle_start', cycle.cycle_start || frm.doc.from_date);
            frm.set_value('benefit_cycle_end', cycle.cycle_end || null);
            frm.set_value('sick_days_this_year_before', flt(cycle.used_days));
            frm.set_value('leave_policy', cycle.leave_policy || null);
            frm.set_value('leave_policy_assignment', cycle.leave_policy_assignment || null);
            frm.set_value('entitlement_source', cycle.entitlement_source || '');
            frm.set_value('policy_full_pay_days', flt(cycle.policy_full_pay_days) || 30);
            frm.set_value('policy_partial_pay_days', flt(cycle.policy_partial_pay_days) || 60);
            frm.set_value('policy_partial_pay_percentage', flt(cycle.policy_partial_pay_percentage) || 75);
            _set_cycle_boundary_review(frm);
            _calc_pay(frm);
        }
    });
}

function _set_cycle_boundary_review(frm) {
    const crosses = Boolean(
        frm.doc.to_date &&
        frm.doc.benefit_cycle_end &&
        frappe.datetime.get_day_diff(frm.doc.to_date, frm.doc.benefit_cycle_end) > 0
    );
    frm.set_value('cycle_boundary_review_required', crosses ? 1 : 0);
    frm.set_value(
        'cycle_boundary_note',
        crosses
            ? __('تتجاوز الإجازة نهاية دورة الاستحقاق الحالية؛ راجع توزيع الأيام بين الدورتين. / The request crosses the benefit-cycle boundary; review allocation across both cycles.')
            : ''
    );
}

function _calc_pay(frm) {
    const before    = flt(frm.doc.sick_days_this_year_before);
    const total     = flt(frm.doc.total_days);
    const after     = before + total;
    const daily     = flt(frm.doc.daily_salary);
    const fullLimit = flt(frm.doc.policy_full_pay_days) || 30;
    const partialLimit = flt(frm.doc.policy_partial_pay_days) || 60;
    const partialPercentage = flt(frm.doc.policy_partial_pay_percentage) || 75;
    const partialRate = partialPercentage / 100;
    const unpaidThreshold = fullLimit + partialLimit;

    frm.set_value('sick_days_this_year_after', after);

    // Server-validated policy values can improve the statutory tiers but never reduce them.
    const full_days = Math.min(total, Math.max(0, fullLimit - before));
    const remaining = Math.max(0, total - full_days);
    const partial_consumed = Math.max(0, Math.min(partialLimit, before - fullLimit));
    const partial_days = Math.min(remaining, Math.max(0, partialLimit - partial_consumed));
    const no_days = Math.max(0, remaining - partial_days);
    const pay = daily * full_days + daily * partialRate * partial_days;
    const effective_rate = total && daily ? (pay / (daily * total)) * 100 : 0;
    const alert_30 = after > fullLimit ? 1 : 0;
    const alert_90 = after > unpaidThreshold ? 1 : 0;
    let rate_label = 'شرائح نظامية مختلطة / Mixed Statutory Tiers';
    if (full_days === total) rate_label = 'أجر كامل (م.117) / Full Pay (Art.117)';
    else if (partial_days === total) rate_label = `${partialPercentage}% من الأجر (م.117) / ${partialPercentage}% Pay (Art.117)`;
    else if (no_days === total) rate_label = 'بدون أجر (م.117) / No Pay (Art.117)';

    frm.set_value('leave_pay_amount', flt(pay.toFixed(2)));
    frm.set_value('full_pay_days', full_days);
    frm.set_value('partial_pay_days', partial_days);
    frm.set_value('unpaid_days', no_days);
    frm.set_value('pay_rate', flt(effective_rate.toFixed(2)));
    frm.set_value('pay_label', rate_label);
    frm.set_value('alert_30_days', alert_30);
    frm.set_value('alert_90_days', alert_90);

    if (alert_90) {
        frappe.show_alert({
            message: __('دخل الموظف شريحة دون أجر بعد {0} يوماً تراكمياً؛ استمر في متابعة استحقاق 120 يوماً ولا تبدأ الإنهاء تلقائياً. / The employee entered the unpaid tier after {0} cumulative days; continue tracking the 120-day entitlement and do not terminate automatically.', [unpaidThreshold]),
            indicator: 'orange'
        });
    } else if (alert_30) {
        frappe.show_alert({
            message: __('تنبيه: الموظف تجاوز {0} يوم إجازة مرضية — معدل {1}% / Notice: Employee exceeded {0} sick days — {1}% pay rate', [fullLimit, partialPercentage]),
            indicator: 'orange'
        });
    }
}
