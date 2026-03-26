// Copyright (c) 2026, Saudi HR and contributors
// Saudi Monthly Payroll - Client Script
// كشف الراتب الشهري السعودي

frappe.ui.form.on('Saudi Monthly Payroll', {

    onload(frm) {
        if (frm.is_new()) {
            const today = frappe.datetime.get_today();
            const parts = today.split('-');
            frm.set_value('year', parseInt(parts[0]));
            frm.set_value('posting_date', today);
            frm.set_value('status', 'Draft / مسودة');
            // تعيين الشهر الحالي
            const monthNames = [
                'January / يناير', 'February / فبراير', 'March / مارس',
                'April / أبريل', 'May / مايو', 'June / يونيو',
                'July / يوليو', 'August / أغسطس', 'September / سبتمبر',
                'October / أكتوبر', 'November / نوفمبر', 'December / ديسمبر'
            ];
            frm.set_value('month', monthNames[parseInt(parts[1]) - 1]);
        }
        _add_buttons(frm);
    },

    refresh(frm) {
        _add_buttons(frm);
    },

    company(frm)  { _update_period(frm); },
    month(frm)    { _update_period(frm); },
    year(frm)     { _update_period(frm); },
});


frappe.ui.form.on('Saudi Monthly Payroll Employee', {
    basic_salary(frm, cdt, cdn)     { _calc_row(frm, cdt, cdn); },
    housing_allowance(frm, cdt, cdn){ _calc_row(frm, cdt, cdn); },
    transport_allowance(frm, cdt, cdn){ _calc_row(frm, cdt, cdn); },
    other_allowances(frm, cdt, cdn) { _calc_row(frm, cdt, cdn); },
    loan_deduction(frm, cdt, cdn)   { _calc_row(frm, cdt, cdn); },
});


// ─── Buttons ─────────────────────────────────────────────────────────────────

function _add_buttons(frm) {
    frm.clear_custom_buttons();

    if (frm.doc.docstatus === 0) {
        // زر جلب الموظفين
        frm.add_custom_button(__('Fetch Employees / جلب الموظفين'), function() {
            _fetch_employees(frm);
        }, __('Actions / إجراءات'));

        // زر إعادة الحساب
        frm.add_custom_button(__('Recalculate All / إعادة الحساب'), function() {
            _recalculate_all(frm);
        }, __('Actions / إجراءات'));

        // زر إنشاء القيد اليومي
        if (frm.doc.employees && frm.doc.employees.length > 0) {
            frm.add_custom_button(__('Create Journal Entry / إنشاء قيد يومي'), function() {
                _create_journal_entry(frm);
            }).addClass('btn-primary');
        }
    }

    // زر فتح Journal Entry الموجود
    if (frm.doc.payroll_journal_entry) {
        frm.add_custom_button(__('View Journal Entry / عرض القيد اليومي'), function() {
            frappe.set_route('Form', 'Journal Entry', frm.doc.payroll_journal_entry);
        });
    }
}


// ─── Action Handlers ─────────────────────────────────────────────────────────

function _fetch_employees(frm) {
    if (!frm.doc.company) {
        frappe.msgprint(__('Please select a Company first.<br>يرجى اختيار الشركة أولاً.'), __('Required'));
        return;
    }
    if (!frm.doc.month || !frm.doc.year) {
        frappe.msgprint(__('Please select Month and Year first.<br>يرجى اختيار الشهر والسنة أولاً.'), __('Required'));
        return;
    }

    // حفظ أولاً إذا كان جديداً
    const do_fetch = function() {
        frappe.call({
            method: 'saudi_hr.saudi_hr.doctype.saudi_monthly_payroll.saudi_monthly_payroll.fetch_employees',
            args: { doc_name: frm.doc.name },
            freeze: true,
            freeze_message: __('Fetching employees and calculating salaries...<br>جاري جلب الموظفين وحساب الرواتب...'),
            callback(r) {
                if (r.message) {
                    frm.reload_doc();
                    frappe.show_alert({
                        message: __(`Fetched ${r.message.count} employees. Total Net: ${format_currency(r.message.total_net)}`),
                        indicator: 'green'
                    }, 5);
                }
            }
        });
    };

    if (frm.is_new()) {
        frm.save().then(do_fetch);
    } else {
        do_fetch();
    }
}


function _recalculate_all(frm) {
    if (!frm.doc.employees || frm.doc.employees.length === 0) {
        frappe.msgprint(__('No employees. Please fetch employees first.<br>لا يوجد موظفون. جلب الموظفين أولاً.'));
        return;
    }

    frappe.call({
        method: 'saudi_hr.saudi_hr.doctype.saudi_monthly_payroll.saudi_monthly_payroll.fetch_employees',
        args: { doc_name: frm.doc.name },
        freeze: true,
        freeze_message: __('Recalculating...<br>جارٍ إعادة الحساب...'),
        callback(r) {
            if (r.message) {
                frm.reload_doc();
                frappe.show_alert({ message: __('Salaries recalculated / تم إعادة الحساب'), indicator: 'blue' }, 4);
            }
        }
    });
}


function _create_journal_entry(frm) {
    frappe.confirm(
        __(`Create a Journal Entry for <b>${frm.doc.month} ${frm.doc.year}</b> with <b>${frm.doc.total_employees}</b> employees?<br>إنشاء قيد يومي لرواتب <b>${frm.doc.month} ${frm.doc.year}</b> لـ <b>${frm.doc.total_employees}</b> موظف؟`),
        function() {
            frappe.call({
                method: 'saudi_hr.saudi_hr.doctype.saudi_monthly_payroll.saudi_monthly_payroll.create_journal_entry_from_payroll',
                args: { doc_name: frm.doc.name },
                freeze: true,
                freeze_message: __('Creating Journal Entry...<br>جاري إنشاء القيد اليومي...'),
                callback(r) {
                    if (r.message) {
                        frm.reload_doc();
                    }
                }
            });
        }
    );
}


// ─── Row Calculations ─────────────────────────────────────────────────────────

function _calc_row(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    const basic    = flt(row.basic_salary);
    const housing  = flt(row.housing_allowance);
    const trans    = flt(row.transport_allowance);
    const other    = flt(row.other_allowances);
    const gross    = basic + housing + trans + other;

    // GOSI اقتطاع الموظف
    const nat = (row.nationality || '').toLowerCase();
    const is_saudi = ['saudi', 'سعودي', 'sa', 'saudi arabia'].includes(nat);
    const gosi_rate = is_saudi ? 10.0 : 0.0;
    const gosi_base = Math.min(basic, 45000);
    const gosi_ded  = parseFloat((gosi_base * gosi_rate / 100).toFixed(2));

    const total_deductions = gosi_ded + flt(row.sick_leave_deduction) + flt(row.loan_deduction);
    const net = parseFloat((gross + flt(row.overtime_addition) - total_deductions).toFixed(2));

    frappe.model.set_value(cdt, cdn, 'gross_salary', parseFloat(gross.toFixed(2)));
    frappe.model.set_value(cdt, cdn, 'gosi_employee_deduction', gosi_ded);
    frappe.model.set_value(cdt, cdn, 'total_deductions', parseFloat(total_deductions.toFixed(2)));
    frappe.model.set_value(cdt, cdn, 'net_salary', net);

    _update_totals(frm);
}


// ─── Totals ───────────────────────────────────────────────────────────────────

function _update_totals(frm) {
    let total_gross = 0, total_gosi = 0, total_sick = 0, total_loan = 0, total_ot = 0, total_net = 0;
    (frm.doc.employees || []).forEach(row => {
        total_gross += flt(row.gross_salary);
        total_gosi  += flt(row.gosi_employee_deduction);
        total_sick  += flt(row.sick_leave_deduction);
        total_loan  += flt(row.loan_deduction);
        total_ot    += flt(row.overtime_addition);
        total_net   += flt(row.net_salary);
    });
    frm.set_value('total_employees',      (frm.doc.employees || []).length);
    frm.set_value('total_gross',          parseFloat(total_gross.toFixed(2)));
    frm.set_value('total_gosi_deductions',parseFloat(total_gosi.toFixed(2)));
    frm.set_value('total_sick_deductions',parseFloat(total_sick.toFixed(2)));
    frm.set_value('total_loan_deductions',parseFloat(total_loan.toFixed(2)));
    frm.set_value('total_overtime',       parseFloat(total_ot.toFixed(2)));
    frm.set_value('total_net_payable',    parseFloat(total_net.toFixed(2)));
}


function _update_period(frm) {
    if (frm.doc.month && frm.doc.year) {
        frm.set_value('period_label', `${frm.doc.month} ${frm.doc.year}`);
    }
}
