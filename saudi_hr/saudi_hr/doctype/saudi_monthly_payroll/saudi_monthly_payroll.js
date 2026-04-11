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
        _sync_workbook_fields(frm);
        _sync_auto_create_defaults(frm);
        _render_source_workbook_guidance(frm);
        _add_buttons(frm);
        _setup_payroll_grid_state(frm);
    },

    refresh(frm) {
        _sync_workbook_fields(frm);
        _sync_auto_create_defaults(frm);
        _render_source_workbook_guidance(frm);
        _add_buttons(frm);
        _setup_payroll_grid_state(frm);
    },

    company(frm)  { _update_period(frm); },
    month(frm)    { _update_period(frm); },
    year(frm)     { _update_period(frm); },
    posting_date(frm) { _sync_auto_create_defaults(frm); },
    auto_create_missing_employees(frm) {
        _sync_auto_create_defaults(frm);
        _refresh_payroll_grid_state(frm);
    },
});


frappe.ui.form.on('Saudi Monthly Payroll Employee', {
    basic_salary(frm, cdt, cdn)     { _calc_row(frm, cdt, cdn); },
    housing_allowance(frm, cdt, cdn){ _calc_row(frm, cdt, cdn); },
    transport_allowance(frm, cdt, cdn){ _calc_row(frm, cdt, cdn); },
    other_allowances(frm, cdt, cdn) { _calc_row(frm, cdt, cdn); },
    loan_deduction(frm, cdt, cdn)   { _calc_row(frm, cdt, cdn); },
    other_deductions(frm, cdt, cdn) { _calc_row(frm, cdt, cdn); },
});


// ─── Buttons ─────────────────────────────────────────────────────────────────

function _add_buttons(frm) {
    frm.clear_custom_buttons();
    const unlinkedCount = _count_unlinked_payroll_rows(frm);

    if (frm.doc.docstatus === 0) {
        // زر جلب الموظفين
        frm.add_custom_button(__('Fetch Employees / جلب الموظفين'), function() {
            _fetch_employees(frm);
        }, __('Actions / إجراءات'));

        // زر إعادة الحساب
        frm.add_custom_button(__('Recalculate All / إعادة الحساب'), function() {
            _recalculate_all(frm);
        }, __('Actions / إجراءات'));

        frm.add_custom_button(__('Import Workbook / استيراد ملف الرواتب'), function() {
            _import_workbook(frm);
        }, __('Actions / إجراءات'));

        frm.add_custom_button(__('Analyze Workbook / تحليل ملف الرواتب'), function() {
            _analyze_workbook(frm);
        }, __('Actions / إجراءات'));

        frm.add_custom_button(__('Validate Workbook / التحقق من ملف الرواتب'), function() {
            _validate_workbook(frm);
        }, __('Actions / إجراءات'));

        frm.add_custom_button(__('Download Payroll Import Template / تنزيل قالب رفع الرواتب'), function() {
            _download_payroll_import_template(frm);
        }, __('Actions / إجراءات'));

        frm.add_custom_button(__('Download Simple Payroll Template / تنزيل قالب رفع الرواتب المبسط'), function() {
            _download_simple_payroll_import_template(frm);
        }, __('Actions / إجراءات'));

        frm.add_custom_button(__('Download Gap Report / تنزيل تقرير الفجوات'), function() {
            _download_gap_report(frm);
        }, __('Actions / إجراءات'));

        frm.add_custom_button(__('Download Employee Setup Template / تنزيل قالب إعداد الموظفين'), function() {
            _download_employee_setup_template(frm);
        }, __('Actions / إجراءات'));

        frm.add_custom_button(__('Autofill Employee Names / تعبئة الأسماء تلقائيا'), function() {
            _autofill_employee_setup_names(frm);
        }, __('Actions / إجراءات'));

        frm.add_custom_button(__('Import Employee Setup / استيراد إعداد الموظفين'), function() {
            _import_employee_setup(frm);
        }, __('Actions / إجراءات'));

        if (unlinkedCount > 0) {
            frm.add_custom_button(__('Create Basic Employees / إنشاء موظفين أساسيين'), function() {
                _create_basic_employees(frm);
            }, __('Actions / إجراءات'));
        }

        // زر إنشاء القيد اليومي
        if (frm.doc.employees && frm.doc.employees.length > 0 && !frm.doc.payroll_journal_entry) {
            frm.add_custom_button(__('Create Journal Entry / إنشاء قيد يومي'), function() {
                _create_journal_entry(frm);
            }).addClass('btn-primary');
        }

        if (!frm.is_new()) {
            frm.add_custom_button(__('Delete Draft Payroll / حذف مسودة المسير'), function() {
                _delete_draft_payroll(frm);
            }).addClass('btn-danger');
        }
    }

    // زر فتح Journal Entry الموجود
    if (frm.doc.payroll_journal_entry) {
        frm.add_custom_button(__('View Journal Entry / عرض القيد اليومي'), function() {
            frappe.set_route('Form', 'Journal Entry', frm.doc.payroll_journal_entry);
        });
    }
}


function _sync_workbook_fields(frm) {
    frm.set_df_property('employee_setup_workbook', 'hidden', 1);
    frm.toggle_display('employee_setup_workbook', false);
    frm.refresh_field('employee_setup_workbook');

    const field = frm.get_field('employee_setup_workbook');
    if (field && field.wrapper) {
        $(field.wrapper).closest('.frappe-control').hide();
        $(field.wrapper).hide();
    }
}


function _sync_auto_create_defaults(frm) {
    const enabled = !!frm.doc.auto_create_missing_employees;
    if (enabled && !frm.doc.auto_create_default_gender) {
        frm.set_value('auto_create_default_gender', 'Prefer not to say');
    }
    if (enabled && !frm.doc.auto_create_default_date_of_birth) {
        frm.set_value('auto_create_default_date_of_birth', '1990-01-01');
    }
    if (enabled && !frm.doc.auto_create_default_date_of_joining) {
        frm.set_value('auto_create_default_date_of_joining', frm.doc.posting_date || frappe.datetime.get_today());
    }

    frm.toggle_display([
        'auto_create_default_gender',
        'auto_create_default_date_of_birth',
        'auto_create_default_date_of_joining'
    ], enabled);
}


function _render_source_workbook_guidance(frm) {
    const field = frm.get_field('source_workbook');
    if (!field || !field.$wrapper) {
        return;
    }

    let helpBox = field.$wrapper.find('.saudi-payroll-workbook-guidance');
    if (!helpBox.length) {
        helpBox = $(
            `<div class="saudi-payroll-workbook-guidance" style="margin-top: 10px; padding: 12px 14px; border-radius: 8px; background: #fff8db; border: 1px solid #f0d27a; line-height: 1.7;"></div>`
        );
        field.$wrapper.append(helpBox);
    }

    helpBox.html(_get_workbook_upload_guidance_html(frm));
}


function _get_workbook_upload_guidance_html(frm) {
    const templateHint = frm.doc.company
        ? __('For the safest format, use Download Payroll Import Template before preparing the file.<br>لأفضل نتيجة استخدم زر تنزيل قالب رفع الرواتب قبل تجهيز الملف.')
        : __('Select the company first so you can download the approved payroll import template.<br>اختر الشركة أولاً حتى تتمكن من تنزيل قالب رفع الرواتب المعتمد.');

    return `
        <div><b>${__('Workbook Upload Rules / تعليمات رفع ملف الرواتب')}</b></div>
        <div>${templateHint}</div>
        <ul style="margin: 8px 0 0; padding-inline-start: 18px;">
            <li>${__('Enter the correct payroll employee ID whenever it exists. Do not rely on name-only matching when an ID is available.<br>أدخل الرقم الوظيفي الصحيح متى ما كان موجوداً، ولا تعتمد على الاسم فقط إذا كان الرقم متاحاً.')}</li>
            <li>${__('If the same employee name appears more than once, separate rows using cost center and payroll ID.<br>عند تكرار الاسم نفسه يجب التفريق بين الصفوف باستخدام مركز التكلفة والرقم الوظيفي.')}</li>
            <li>${__('Rows with zero salary or zero net salary are treated as leave rows and will be skipped during import.<br>أي صف راتبه أو صافي راتبه صفر سيُعتبر إجازة وسيتم تجاهله عند الاستيراد.')}</li>
            <li>${__('Do not change the first-row column headers, merge cells, or insert notes inside the payroll data table.<br>لا تغيّر أسماء أعمدة الصف الأول، ولا تدمج الخلايا، ولا تضع ملاحظات داخل جدول البيانات نفسه.')}</li>
            <li>${__('Keep salary fields numeric only, and keep cost center filled for every repeated or split row.<br>اجعل حقول الرواتب أرقاماً فقط، واحرص على تعبئة مركز التكلفة لكل صف مكرر أو موزع.')}</li>
        </ul>
    `;
}


function _confirm_workbook_import(frm, proceed) {
    const currentRows = (frm.doc.employees || []).length;
    const rowMessage = currentRows
        ? __('Current payroll rows on this document: {0}. Importing will replace them with workbook rows.<br>عدد صفوف الرواتب الحالية في هذا المستند: {0}. الاستيراد سيستبدلها بصفوف الملف.', [currentRows])
        : __('No payroll rows are loaded yet. Importing will fill this document from the workbook.<br>لا توجد صفوف رواتب محملة حالياً. الاستيراد سيقوم بتعبئة المستند من الملف.');

    frappe.call({
        method: 'saudi_hr.saudi_hr.doctype.saudi_monthly_payroll.saudi_monthly_payroll.validate_payroll_workbook',
        args: {
            doc_name: frm.doc.name,
            file_url: frm.doc.source_workbook
        },
        freeze: true,
        freeze_message: __('Running final workbook checks before import...<br>جاري تنفيذ التحقق النهائي من الملف قبل الاستيراد...'),
        callback(r) {
            if (!r.message) {
                return;
            }

            const summary = r.message;
            if (summary.error_count || summary.critical_warning_count) {
                _show_workbook_validation_summary(summary);
                return;
            }

            const criticalItems = (summary.critical_warnings || [])
                .slice(0, 5)
                .map((warning) => `<li>${frappe.utils.escape_html(warning)}</li>`)
                .join('');
            const criticalBlock = criticalItems
                ? `<div style="margin-top: 12px; padding: 10px 12px; border-radius: 8px; background: #fff1f3; border: 1px solid #f0a3ad; color: #b42318;"><b>${__('Critical review items / نقاط حرجة للمراجعة')}</b><ul style="margin: 8px 0 0; padding-inline-start: 18px;">${criticalItems}</ul></div>`
                : '';

            frappe.confirm(
                __('Before import, confirm the workbook follows these rules:<br>قبل الاستيراد تأكد من الآتي:')
                + '<br><br>• ' + __('Payroll ID is filled whenever available.<br>تم تعبئة الرقم الوظيفي متى ما كان موجوداً.')
                + '<br>• ' + __('Repeated names are distinguished by cost center.<br>الأسماء المكررة تم التفريق بينها بمركز التكلفة.')
                + '<br>• ' + __('Zero-salary rows are intentionally leave rows.<br>الصفوف ذات الراتب الصفري مقصود بها الإجازات.')
                + '<br>• ' + __('Column headers were not changed.<br>لم يتم تغيير أسماء الأعمدة.')
                + '<br><br>' + rowMessage
                + criticalBlock,
                proceed
            );
        }
    });
}


function _show_workbook_validation_summary(summary) {
    const errorItems = (summary.errors || [])
        .slice(0, 15)
        .map((row) => `<li>${frappe.utils.escape_html(row)}</li>`)
        .join('');
    const criticalItems = (summary.critical_warnings || [])
        .slice(0, 15)
        .map((row) => `<li>${frappe.utils.escape_html(row)}</li>`)
        .join('');
    const warningItems = (summary.warnings || [])
        .slice(0, 15)
        .map((row) => `<li>${frappe.utils.escape_html(row)}</li>`)
        .join('');
    const costCenterItems = (summary.would_create_cost_centers || [])
        .slice(0, 15)
        .map((row) => `<li>${frappe.utils.escape_html(row)}</li>`)
        .join('');

    frappe.msgprint({
        title: __('Workbook Validation / التحقق من ملف الرواتب'),
        indicator: summary.error_count || summary.critical_warning_count ? 'red' : (summary.warning_count ? 'orange' : 'green'),
        wide: true,
        message: `
            <p>${__('عدد صفوف الملف')}: <b>${summary.total_rows}</b></p>
            <p>${__('عدد الأخطاء المانعة')}: <b>${summary.error_count}</b></p>
            <p>${__('عدد التحذيرات الحرجة')}: <b>${summary.critical_warning_count || 0}</b></p>
            <p>${__('عدد التحذيرات')}: <b>${summary.warning_count}</b></p>
            ${(summary.would_create_cost_centers || []).length ? `<p><b>${__('مراكز التكلفة التي سيقوم النظام بإنشائها تلقائياً')}</b></p><ul>${costCenterItems}</ul>` : ''}
            ${errorItems ? `<p><b>${__('الأخطاء التي تمنع الاستيراد')}</b></p><ul>${errorItems}</ul>` : ''}
            ${criticalItems ? `<p style="color:#b42318;"><b>${__('تحذيرات حرجة تحتاج مراجعة قبل الاستيراد')}</b></p><ul>${criticalItems}</ul>` : ''}
            ${warningItems ? `<p><b>${__('ملاحظات تحتاج مراجعة')}</b></p><ul>${warningItems}</ul>` : ''}
        `
    });
}


function _setup_payroll_grid_state(frm) {
    _ensure_payroll_grid_styles();
    _bind_payroll_grid_events(frm);
    _refresh_payroll_grid_state(frm);
}


function _ensure_payroll_grid_styles() {
    if (document.getElementById('saudi-payroll-grid-styles')) {
        return;
    }

    const style = document.createElement('style');
    style.id = 'saudi-payroll-grid-styles';
    style.textContent = `
        .form-grid .data-row.row.rm-unlinked-payroll-row,
        .form-grid .grid-row.rm-unlinked-payroll-row .data-row.row {
            background:
                linear-gradient(90deg, rgba(202, 138, 4, 0.16), rgba(202, 138, 4, 0.05));
            box-shadow: inset 3px 0 0 rgba(202, 138, 4, 0.9);
        }

        .form-grid .data-row.row.rm-unlinked-payroll-row .data-row,
        .form-grid .data-row.row.rm-unlinked-payroll-row .static-area,
        .form-grid .grid-row.rm-unlinked-payroll-row .static-area {
            background: transparent;
        }
    `;
    document.head.appendChild(style);
}


function _bind_payroll_grid_events(frm) {
    if (frm.__payroll_grid_events_bound) {
        return;
    }

    frm.__payroll_grid_events_bound = true;
    $(frm.wrapper).on('grid-row-render.saudi-payroll', function(_event, grid_row) {
        if (grid_row.grid?.df?.fieldname !== 'employees') {
            return;
        }
        _apply_unlinked_row_style(grid_row);
    });
}


function _refresh_payroll_grid_state(frm) {
    const count = _count_unlinked_payroll_rows(frm);
    const autoCreateEnabled = !!frm.doc.auto_create_missing_employees;
    const defaultGender = frm.doc.auto_create_default_gender || __('Not set / غير محدد');
    const defaultBirthDate = frm.doc.auto_create_default_date_of_birth || __('Not set / غير محدد');
    const defaultJoiningDate = frm.doc.auto_create_default_date_of_joining || frm.doc.posting_date || __('Not set / غير محدد');
    if (count > 0 && autoCreateEnabled) {
        frm.set_intro(
            __('There are {0} imported payroll rows without linked Employee records yet. Automatic employee creation is enabled and will use Gender {1}, Date of Birth {2}, and Joining Date {3}. Review the created employee masters after import.<br>يوجد {0} صف رواتب مستورد غير مرتبط بعد بسجل Employee. تم تفعيل الإنشاء التلقائي وسيستخدم الجنس {1} وتاريخ الميلاد {2} وتاريخ المباشرة {3}. يرجى مراجعة سجلات الموظفين التي سينشئها النظام بعد الاستيراد.', [count, defaultGender, defaultBirthDate, defaultJoiningDate]),
            'orange'
        );
    } else if (count > 0) {
        frm.set_intro(
            __('There are {0} imported payroll rows without linked Employee records yet. You can still review payroll values now, or use Create Basic Employees to generate master records.', [count]),
            'orange'
        );
    } else if (autoCreateEnabled) {
        frm.set_intro(
            __('Automatic employee creation is enabled for unmatched payroll rows. Defaults: Gender {0}, Date of Birth {1}, Joining Date {2}.<br>إنشاء الموظفين التلقائي مفعل لصفوف الرواتب غير المطابقة. القيم الافتراضية: الجنس {0}، تاريخ الميلاد {1}، تاريخ المباشرة {2}.', [defaultGender, defaultBirthDate, defaultJoiningDate]),
            'blue'
        );
    } else {
        frm.set_intro('');
    }

    window.setTimeout(() => {
        const gridRows = frm.fields_dict.employees?.grid?.grid_rows || [];
        gridRows.forEach((grid_row) => _apply_unlinked_row_style(grid_row));
    }, 50);
}


function _apply_unlinked_row_style(grid_row) {
    const isUnlinked = !grid_row.doc?.employee;
    $(grid_row.row).toggleClass('rm-unlinked-payroll-row', isUnlinked);
    $(grid_row.row).attr('title', isUnlinked ? __('Imported payroll row without linked Employee record') : '');
}


function _count_unlinked_payroll_rows(frm) {
    return (frm.doc.employees || []).filter((row) => !row.employee).length;
}


function _upload_employee_setup_workbook(frm, after_upload) {
    const open_uploader = function() {
        new frappe.ui.FileUploader({
            doctype: frm.doctype,
            docname: frm.doc.name,
            frm: frm,
            allow_multiple: false,
            allow_toggle_private: false,
            on_success(file_doc) {
                Promise.resolve(frm.set_value('employee_setup_workbook', file_doc.file_url)).then(() => {
                    after_upload(file_doc.file_url, file_doc);
                });
            }
        });
    };

    if (frm.is_new()) {
        frm.save().then(open_uploader);
    } else {
        open_uploader();
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
                    const skippedCount = r.message.skipped_count || 0;
                    const sourceCount = r.message.source_count || r.message.count || 0;
                    frappe.show_alert({
                        message: skippedCount
                            ? __(`Fetched ${r.message.count} of ${sourceCount} employees. Skipped ${skippedCount} with missing basic salary.`)
                            : __(`Fetched ${r.message.count} employees. Total Net: ${format_currency(r.message.total_net)}`),
                        indicator: skippedCount ? 'orange' : 'green'
                    }, 5);
                    _show_payroll_warning_list(__('Fetch Warnings / ملاحظات الجلب'), r.message.warnings || []);
                }
            }
        });
    };

    _confirm_workbook_contract_action(frm, function() {
        if (frm.is_new()) {
            frm.save().then(do_fetch);
        } else {
            do_fetch();
        }
    });
}


function _recalculate_all(frm) {
    if (!frm.doc.employees || frm.doc.employees.length === 0) {
        frappe.msgprint(__('No employees. Please fetch employees first.<br>لا يوجد موظفون. جلب الموظفين أولاً.'));
        return;
    }

    _confirm_workbook_contract_action(frm, function() {
        frappe.call({
            method: 'saudi_hr.saudi_hr.doctype.saudi_monthly_payroll.saudi_monthly_payroll.fetch_employees',
            args: { doc_name: frm.doc.name },
            freeze: true,
            freeze_message: __('Recalculating...<br>جارٍ إعادة الحساب...'),
            callback(r) {
                if (r.message) {
                    frm.reload_doc();
                    const skippedCount = r.message.skipped_count || 0;
                    frappe.show_alert({
                        message: skippedCount
                            ? __('Salaries recalculated with warnings / تمت إعادة الحساب مع ملاحظات')
                            : __('Salaries recalculated / تم إعادة الحساب'),
                        indicator: skippedCount ? 'orange' : 'blue'
                    }, 4);
                    _show_payroll_warning_list(__('Recalculation Warnings / ملاحظات إعادة الحساب'), r.message.warnings || []);
                }
            }
        });
    });
}


function _confirm_workbook_contract_action(frm, proceed) {
    if (!frm.doc.source_workbook) {
        proceed();
        return;
    }

    const rowMessage = (frm.doc.employees || []).length
        ? __('Current payroll rows: {0}.<br>عدد صفوف الرواتب الحالية: {0}.', [(frm.doc.employees || []).length])
        : __('No payroll rows are currently loaded.<br>لا توجد صفوف رواتب محملة حالياً.');

    frappe.confirm(
        __('A source workbook is attached to this payroll. Fetch Employees and Recalculate use contract data and may replace workbook-imported rows.<br>يوجد ملف رواتب مرفق بهذا المسير. جلب الموظفين وإعادة الحساب يعتمدان بيانات العقود وقد يستبدلان الصفوف المستوردة من الملف.')
        + '<br><br>' + rowMessage
        + '<br><br>' + __('Continue only if you intentionally want contract-based payroll rows.<br>تابع فقط إذا كنت تريد صفوف رواتب مبنية على العقود.'),
        proceed
    );
}


function _show_payroll_warning_list(title, warnings) {
    if (!warnings || !warnings.length) {
        return;
    }

    const warningItems = warnings
        .slice(0, 10)
        .map((warning) => `<li>${frappe.utils.escape_html(warning)}</li>`)
        .join('');
    const extraCount = Math.max(warnings.length - 10, 0);
    const extraText = extraCount ? `<p>${__('Additional warnings')}: ${extraCount}</p>` : '';

    frappe.msgprint({
        title,
        indicator: 'orange',
        message: `<ul>${warningItems}</ul>${extraText}`
    });
}


function _import_workbook(frm) {
    if (!frm.doc.company) {
        frappe.msgprint(__('Please select a Company first.<br>يرجى اختيار الشركة أولاً.'));
        return;
    }
    if (!frm.doc.month || !frm.doc.year) {
        frappe.msgprint(__('Please select Month and Year first.<br>يرجى اختيار الشهر والسنة أولاً.'));
        return;
    }
    if (!frm.doc.source_workbook) {
        frappe.msgprint(__('Attach the source payroll workbook first.<br>أرفق ملف الرواتب المصدر أولاً.'));
        return;
    }

    const do_import = function() {
        const autoCreateEnabled = !!frm.doc.auto_create_missing_employees;
        frappe.call({
            method: 'saudi_hr.saudi_hr.doctype.saudi_monthly_payroll.saudi_monthly_payroll.import_payroll_workbook',
            args: {
                doc_name: frm.doc.name,
                file_url: frm.doc.source_workbook
            },
            freeze: true,
            freeze_message: autoCreateEnabled
                ? __('Importing workbook, matching employees, and creating missing employee records...<br>جاري استيراد ملف الرواتب ومطابقة الموظفين وإنشاء سجلات الموظفين الناقصة...')
                : __('Importing workbook and matching employees...<br>جاري استيراد ملف الرواتب ومطابقة الموظفين...'),
            callback(r) {
                if (!r.message) {
                    return;
                }

                frm.reload_doc();
                frappe.show_alert({
                    message: __(`Imported ${r.message.count} payroll rows. Total Net: ${format_currency(r.message.total_net)}`),
                    indicator: 'green'
                }, 6);

                if (r.message.auto_create_enabled) {
                    frappe.msgprint({
                        title: __('Workbook Import Result / نتيجة استيراد ملف الرواتب'),
                        indicator: r.message.remaining_unlinked_rows ? 'orange' : 'green',
                        message: `
                            <p>${__('Imported payroll rows')}: <b>${r.message.count}</b></p>
                            <p>${__('Auto-created employees')}: <b>${r.message.created_count || 0}</b></p>
                            <p>${__('Linked existing rows')}: <b>${r.message.linked_count || 0}</b></p>
                            <p>${__('Remaining unlinked rows')}: <b>${r.message.remaining_unlinked_rows || 0}</b></p>
                            <p>${__('The system created basic Employee records automatically for unmatched payroll rows using the defaults shown on the form. Please review and enrich those employee records after import.')}<br>${__('أنشأ النظام سجلات Employee أساسية تلقائياً للصفوف غير المطابقة باستخدام القيم الافتراضية الظاهرة في النموذج. يرجى مراجعة هذه السجلات واستكمال بياناتها بعد الاستيراد.')}</p>
                        `
                    });
                }

                const combinedWarnings = [...(r.message.warnings || []), ...(r.message.skipped || [])];
                if (combinedWarnings.length) {
                    const warningItems = combinedWarnings
                        .slice(0, 10)
                        .map((warning) => `<li>${frappe.utils.escape_html(warning)}</li>`)
                        .join('');
                    const extraCount = Math.max(combinedWarnings.length - 10, 0);
                    const extraText = extraCount ? `<p>${__('Additional warnings')}: ${extraCount}</p>` : '';

                    frappe.msgprint({
                        title: __('Import Warnings / ملاحظات الاستيراد'),
                        indicator: 'orange',
                        message: `<ul>${warningItems}</ul>${extraText}`
                    });
                }
            }
        });
    };

    const startImport = function() {
        if (frm.is_new()) {
            frm.save().then(() => _confirm_workbook_import(frm, do_import));
            return;
        }
        _confirm_workbook_import(frm, do_import);
    };

    startImport();
}


function _analyze_workbook(frm) {
    if (!frm.doc.company) {
        frappe.msgprint(__('Please select a Company first.<br>يرجى اختيار الشركة أولاً.'));
        return;
    }
    if (!frm.doc.source_workbook) {
        frappe.msgprint(__('Attach the source payroll workbook first.<br>أرفق ملف الرواتب المصدر أولاً.'));
        return;
    }

    const do_analyze = function() {
        frappe.call({
            method: 'saudi_hr.saudi_hr.doctype.saudi_monthly_payroll.saudi_monthly_payroll.preview_payroll_workbook_import',
            args: {
                doc_name: frm.doc.name,
                file_url: frm.doc.source_workbook
            },
            freeze: true,
            freeze_message: __('Analyzing workbook and employee matching...<br>جاري تحليل الملف ومطابقة الموظفين...'),
            callback(r) {
                if (!r.message) {
                    return;
                }

                const summary = r.message;
                const unmatchedItems = (summary.sample_unmatched || [])
                    .map((row) => `<li>${frappe.utils.escape_html(row)}</li>`)
                    .join('');
                const matchedItems = (summary.sample_matched || [])
                    .map((row) => `<li>${frappe.utils.escape_html(row)}</li>`)
                    .join('');
                const criticalItems = (summary.critical_warnings || [])
                    .slice(0, 10)
                    .map((row) => `<li>${frappe.utils.escape_html(row)}</li>`)
                    .join('');

                frappe.msgprint({
                    title: __('Workbook Analysis / تحليل ملف الرواتب'),
                    indicator: summary.critical_warning_count ? 'red' : (summary.importable_rows ? 'green' : 'orange'),
                    wide: true,
                    message: `
                        <p>${__('Workbook rows')}: <b>${summary.total_rows}</b></p>
                        <p>${__('Importable rows')}: <b>${summary.importable_rows}</b></p>
                        <p>${__('Unmatched rows')}: <b>${summary.unmatched_rows}</b></p>
                        <p>${__('Critical review items')}: <b>${summary.critical_warning_count || 0}</b></p>
                        <p>${__('Employees in company')}: <b>${summary.company_employee_count}</b></p>
                        ${criticalItems ? `<p style="color:#b42318;"><b>${__('Critical rows to review before import')}</b></p><ul>${criticalItems}</ul>` : ''}
                        ${matchedItems ? `<p><b>${__('Sample matched rows')}</b></p><ul>${matchedItems}</ul>` : ''}
                        ${unmatchedItems ? `<p><b>${__('Sample unmatched rows')}</b></p><ul>${unmatchedItems}</ul>` : ''}
                    `
                });
            }
        });
    };

    if (frm.is_new()) {
        frm.save().then(do_analyze);
    } else {
        do_analyze();
    }
}


function _validate_workbook(frm) {
    if (!frm.doc.company) {
        frappe.msgprint(__('Please select a Company first.<br>يرجى اختيار الشركة أولاً.'));
        return;
    }
    if (!frm.doc.source_workbook) {
        frappe.msgprint(__('Attach the source payroll workbook first.<br>أرفق ملف الرواتب المصدر أولاً.'));
        return;
    }

    const do_validate = function() {
        frappe.call({
            method: 'saudi_hr.saudi_hr.doctype.saudi_monthly_payroll.saudi_monthly_payroll.validate_payroll_workbook',
            args: {
                doc_name: frm.doc.name,
                file_url: frm.doc.source_workbook
            },
            freeze: true,
            freeze_message: __('Validating payroll workbook before import...<br>جاري التحقق من ملف الرواتب قبل الاستيراد...'),
            callback(r) {
                if (!r.message) {
                    return;
                }

                _show_workbook_validation_summary(r.message);
            }
        });
    };

    if (frm.is_new()) {
        frm.save().then(do_validate);
    } else {
        do_validate();
    }
}


function _download_gap_report(frm) {
    if (!frm.doc.company) {
        frappe.msgprint(__('Please select a Company first.<br>يرجى اختيار الشركة أولاً.'));
        return;
    }
    if (!frm.doc.source_workbook) {
        frappe.msgprint(__('Attach the source payroll workbook first.<br>أرفق ملف الرواتب المصدر أولاً.'));
        return;
    }

    const do_download = function() {
        frappe.call({
            method: 'saudi_hr.saudi_hr.doctype.saudi_monthly_payroll.saudi_monthly_payroll.download_payroll_workbook_gap_report',
            args: {
                doc_name: frm.doc.name,
                file_url: frm.doc.source_workbook
            },
            freeze: true,
            freeze_message: __('Generating gap report...<br>جاري إنشاء تقرير الفجوات...'),
            callback(r) {
                if (!r.message || !r.message.file_url) {
                    return;
                }
                window.open(r.message.file_url, '_blank');
                frappe.show_alert({
                    message: __(`Gap report generated with ${r.message.row_count} rows.`),
                    indicator: 'green'
                }, 5);
            }
        });
    };

    if (frm.is_new()) {
        frm.save().then(do_download);
    } else {
        do_download();
    }
}


function _download_payroll_import_template(frm) {
    if (!frm.doc.company) {
        frappe.msgprint(__('Please select a Company first.<br>يرجى اختيار الشركة أولاً.'));
        return;
    }

    const do_download = function() {
        frappe.call({
            method: 'saudi_hr.saudi_hr.doctype.saudi_monthly_payroll.saudi_monthly_payroll.download_payroll_import_template',
            args: {
                doc_name: frm.doc.name
            },
            freeze: true,
            freeze_message: __('Generating payroll import template...<br>جاري إنشاء قالب رفع الرواتب...'),
            callback(r) {
                if (!r.message || !r.message.file_url) {
                    return;
                }
                window.open(r.message.file_url, '_blank');
                frappe.show_alert({
                    message: __('Payroll import template is ready / تم تجهيز قالب رفع الرواتب'),
                    indicator: 'green'
                }, 5);
            }
        });
    };

    if (frm.is_new()) {
        frm.save().then(do_download);
    } else {
        do_download();
    }
}


function _download_simple_payroll_import_template(frm) {
    if (!frm.doc.company) {
        frappe.msgprint(__('Please select a Company first.<br>يرجى اختيار الشركة أولاً.'));
        return;
    }

    const do_download = function() {
        frappe.call({
            method: 'saudi_hr.saudi_hr.doctype.saudi_monthly_payroll.saudi_monthly_payroll.download_simple_payroll_import_template',
            args: {
                doc_name: frm.doc.name
            },
            freeze: true,
            freeze_message: __('Generating simplified payroll import template...<br>جاري إنشاء قالب رفع الرواتب المبسط...'),
            callback(r) {
                if (!r.message || !r.message.file_url) {
                    return;
                }
                window.open(r.message.file_url, '_blank');
                frappe.show_alert({
                    message: __('Simple payroll template is ready / تم تجهيز قالب رفع الرواتب المبسط'),
                    indicator: 'green'
                }, 5);
            }
        });
    };

    if (frm.is_new()) {
        frm.save().then(do_download);
    } else {
        do_download();
    }
}


function _download_employee_setup_template(frm) {
    if (!frm.doc.company) {
        frappe.msgprint(__('Please select a Company first.<br>يرجى اختيار الشركة أولاً.'));
        return;
    }
    if (!frm.doc.source_workbook) {
        frappe.msgprint(__('Attach the source payroll workbook first.<br>أرفق ملف الرواتب المصدر أولاً.'));
        return;
    }

    const do_download = function() {
        frappe.call({
            method: 'saudi_hr.saudi_hr.doctype.saudi_monthly_payroll.saudi_monthly_payroll.download_employee_setup_template',
            args: {
                doc_name: frm.doc.name,
                file_url: frm.doc.source_workbook
            },
            freeze: true,
            freeze_message: __('Generating employee setup template...<br>جاري إنشاء قالب إعداد الموظفين...'),
            callback(r) {
                if (!r.message || !r.message.file_url) {
                    return;
                }
                window.open(r.message.file_url, '_blank');
                frappe.show_alert({
                    message: __(`Employee setup template generated with ${r.message.row_count} rows.`),
                    indicator: 'green'
                }, 5);
            }
        });
    };

    if (frm.is_new()) {
        frm.save().then(do_download);
    } else {
        do_download();
    }
}


function _autofill_employee_setup_names(frm) {
    if (!frm.doc.company) {
        frappe.msgprint(__('Please select a Company first.<br>يرجى اختيار الشركة أولاً.'));
        return;
    }

    const do_autofill = function(file_url) {
        frappe.call({
            method: 'saudi_hr.saudi_hr.doctype.saudi_monthly_payroll.saudi_monthly_payroll.autofill_employee_setup_workbook_names',
            args: {
                doc_name: frm.doc.name,
                file_url: file_url
            },
            freeze: true,
            freeze_message: __('Autofilling employee names...<br>جاري تعبئة أسماء الموظفين تلقائيا...'),
            callback(r) {
                if (!r.message) {
                    return;
                }

                frm.reload_doc();
                frappe.show_alert({
                    message: __(`Autofilled name fields for ${r.message.updated_count} rows.`),
                    indicator: 'green'
                }, 6);
            }
        });
    };

    _upload_employee_setup_workbook(frm, do_autofill);
}


function _import_employee_setup(frm) {
    if (!frm.doc.company) {
        frappe.msgprint(__('Please select a Company first.<br>يرجى اختيار الشركة أولاً.'));
        return;
    }

    const do_import = function(file_url) {
        frappe.call({
            method: 'saudi_hr.saudi_hr.doctype.saudi_monthly_payroll.saudi_monthly_payroll.import_employee_setup_workbook',
            args: {
                doc_name: frm.doc.name,
                file_url: file_url
            },
            freeze: true,
            freeze_message: __('Importing employee setup workbook...<br>جاري استيراد ملف إعداد الموظفين...'),
            callback(r) {
                if (!r.message) {
                    return;
                }

                const skippedItems = (r.message.skipped || [])
                    .slice(0, 10)
                    .map((warning) => `<li>${frappe.utils.escape_html(warning)}</li>`)
                    .join('');
                const extraCount = Math.max((r.message.skipped || []).length - 10, 0);
                const extraText = extraCount ? `<p>${__('Additional skipped rows')}: ${extraCount}</p>` : '';

                frappe.show_alert({
                    message: __(`Created ${r.message.created_count} employees from the setup workbook.`),
                    indicator: 'green'
                }, 6);

                if (skippedItems) {
                    frappe.msgprint({
                        title: __('Employee Setup Import / استيراد إعداد الموظفين'),
                        indicator: 'orange',
                        message: `<ul>${skippedItems}</ul>${extraText}`
                    });
                }
            }
        });
    };

    _upload_employee_setup_workbook(frm, do_import);
}


function _create_basic_employees(frm) {
    const unlinkedCount = _count_unlinked_payroll_rows(frm);
    if (!unlinkedCount) {
        frappe.msgprint(__('All payroll rows are already linked to Employee records.<br>جميع صفوف الرواتب مرتبطة بالفعل بسجلات موظفين.'));
        return;
    }

    const dialog = new frappe.ui.Dialog({
        title: __('Create Basic Employees / إنشاء موظفين أساسيين'),
        fields: [
            {
                fieldname: 'help_html',
                fieldtype: 'HTML',
                options: `
                    <div class="text-muted" style="line-height:1.7; margin-bottom: 8px;">
                        ${__('This will create placeholder Employee records for the {0} imported payroll rows that are still not linked. Review the defaults before continuing.', [unlinkedCount])}
                    </div>
                `
            },
            {
                fieldname: 'default_gender',
                fieldtype: 'Link',
                options: 'Gender',
                label: __('Default Gender / الجنس الافتراضي'),
                reqd: 1,
                default: frm.doc.auto_create_default_gender || 'Prefer not to say'
            },
            {
                fieldname: 'default_date_of_birth',
                fieldtype: 'Date',
                label: __('Default Date of Birth / تاريخ الميلاد الافتراضي'),
                reqd: 1,
                default: frm.doc.auto_create_default_date_of_birth || '1990-01-01'
            },
            {
                fieldname: 'default_date_of_joining',
                fieldtype: 'Date',
                label: __('Default Date of Joining / تاريخ المباشرة الافتراضي'),
                reqd: 1,
                default: frm.doc.auto_create_default_date_of_joining || frm.doc.posting_date || frappe.datetime.get_today()
            }
        ],
        primary_action_label: __('Create / إنشاء'),
        primary_action(values) {
            frappe.call({
                method: 'saudi_hr.saudi_hr.doctype.saudi_monthly_payroll.saudi_monthly_payroll.create_basic_employees_from_payroll',
                args: {
                    doc_name: frm.doc.name,
                    default_gender: values.default_gender,
                    default_date_of_birth: values.default_date_of_birth,
                    default_date_of_joining: values.default_date_of_joining,
                    default_status: 'Active'
                },
                freeze: true,
                freeze_message: __('Creating basic Employee records...<br>جاري إنشاء سجلات موظفين أساسية...'),
                callback(r) {
                    if (!r.message) {
                        return;
                    }

                    dialog.hide();
                    frm.reload_doc();
                    frappe.show_alert({
                        message: __(`Created ${r.message.created_count} employees and linked ${r.message.linked_count} payroll rows.`),
                        indicator: 'green'
                    }, 6);

                    if ((r.message.skipped || []).length) {
                        const skippedItems = r.message.skipped
                            .slice(0, 10)
                            .map((warning) => `<li>${frappe.utils.escape_html(warning)}</li>`)
                            .join('');
                        const extraCount = Math.max(r.message.skipped.length - 10, 0);
                        const extraText = extraCount ? `<p>${__('Additional skipped rows')}: ${extraCount}</p>` : '';

                        frappe.msgprint({
                            title: __('Basic Employee Creation / إنشاء موظفين أساسيين'),
                            indicator: 'orange',
                            message: `<ul>${skippedItems}</ul>${extraText}`
                        });
                    }
                }
            });
        }
    });

    dialog.show();
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


function _delete_draft_payroll(frm) {
    frappe.confirm(
        __('Delete this draft payroll and its attached draft files?<br>حذف مسير الرواتب هذا وهو في المسودة مع ملفاته المرفقة؟'),
        function() {
            frappe.call({
                method: 'saudi_hr.saudi_hr.doctype.saudi_monthly_payroll.saudi_monthly_payroll.delete_draft_payroll',
                args: { doc_name: frm.doc.name },
                freeze: true,
                freeze_message: __('Deleting draft payroll...<br>جارٍ حذف مسير الرواتب المسودة...'),
                callback(r) {
                    if (r.message && r.message.deleted) {
                        frappe.show_alert({
                            message: __('Draft payroll deleted / تم حذف مسير الرواتب المسودة'),
                            indicator: 'red'
                        }, 5);
                        frappe.set_route('List', 'Saudi Monthly Payroll');
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

    const total_deductions = gosi_ded + flt(row.sick_leave_deduction) + flt(row.loan_deduction) + flt(row.other_deductions);
    const net = parseFloat((gross + flt(row.overtime_addition) - total_deductions).toFixed(2));

    frappe.model.set_value(cdt, cdn, 'gross_salary', parseFloat(gross.toFixed(2)));
    frappe.model.set_value(cdt, cdn, 'gosi_employee_deduction', gosi_ded);
    frappe.model.set_value(cdt, cdn, 'total_deductions', parseFloat(total_deductions.toFixed(2)));
    frappe.model.set_value(cdt, cdn, 'net_salary', net);

    _update_totals(frm);
}


// ─── Totals ───────────────────────────────────────────────────────────────────

function _update_totals(frm) {
    let total_gross = 0, total_gosi = 0, total_sick = 0, total_loan = 0, total_other = 0, total_ot = 0, total_net = 0;
    (frm.doc.employees || []).forEach(row => {
        total_gross += flt(row.gross_salary);
        total_gosi  += flt(row.gosi_employee_deduction);
        total_sick  += flt(row.sick_leave_deduction);
        total_loan  += flt(row.loan_deduction);
        total_other += flt(row.other_deductions);
        total_ot    += flt(row.overtime_addition);
        total_net   += flt(row.net_salary);
    });
    frm.set_value('total_employees',      (frm.doc.employees || []).length);
    frm.set_value('total_gross',          parseFloat(total_gross.toFixed(2)));
    frm.set_value('total_gosi_deductions',parseFloat(total_gosi.toFixed(2)));
    frm.set_value('total_sick_deductions',parseFloat(total_sick.toFixed(2)));
    frm.set_value('total_loan_deductions',parseFloat(total_loan.toFixed(2)));
    frm.set_value('total_other_deductions',parseFloat(total_other.toFixed(2)));
    frm.set_value('total_overtime',       parseFloat(total_ot.toFixed(2)));
    frm.set_value('total_net_payable',    parseFloat(total_net.toFixed(2)));
}


function _update_period(frm) {
    if (frm.doc.month && frm.doc.year) {
        frm.set_value('period_label', `${frm.doc.month} ${frm.doc.year}`);
    }
}
