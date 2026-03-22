<div dir="rtl" align="right">

# نظام إدارة الموارد البشرية — المملكة العربية السعودية

**تطبيق Frappe/ERPNext متكامل لإدارة شؤون الموظفين وفق نظام العمل السعودي**  
المرسوم الملكي م/51 لعام 1426هـ وتعديلاته حتى 1446هـ

[![الإصدار](https://img.shields.io/badge/الإصدار-1.3.0-blue)](https://github.com/ahmadmdm/hr-saudi-arabia-erpnext/releases)
[![Frappe](https://img.shields.io/badge/Frappe-v15-brightgreen)](https://frappeframework.com)
[![ERPNext](https://img.shields.io/badge/ERPNext-v15-blue)](https://erpnext.com)
[![الرخصة](https://img.shields.io/badge/الرخصة-GPL--3.0-orange)](LICENSE)

</div>

---

<div dir="ltr" align="left">

# Saudi HR — Saudi Arabia Labor Law ERP Module

**A complete Frappe/ERPNext application for HR management compliant with Saudi Labor Law**  
Royal Decree No. M/51 of 1426H and its amendments through 1446H

[![Version](https://img.shields.io/badge/version-1.3.0-blue)](https://github.com/ahmadmdm/hr-saudi-arabia-erpnext/releases)
[![Frappe](https://img.shields.io/badge/Frappe-v15-brightgreen)](https://frappeframework.com)
[![ERPNext](https://img.shields.io/badge/ERPNext-v15-blue)](https://erpnext.com)
[![License](https://img.shields.io/badge/license-GPL--3.0-orange)](LICENSE)

</div>

---

## 📋 فهرس المحتويات | Table of Contents

- [نظرة عامة | Overview](#-نظرة-عامة--overview)
- [المتطلبات | Requirements](#-المتطلبات--requirements)
- [التثبيت | Installation](#-التثبيت--installation)
- [المكونات | Features](#-المكونات--features)
- [التغطية القانونية | Legal Coverage](#-التغطية-القانونية--legal-coverage)
- [الاستخدام | Usage](#-الاستخدام--usage)
- [سجل التغييرات | Changelog](#-سجل-التغييرات--changelog)
- [المساهمة | Contributing](#-المساهمة--contributing)
- [الرخصة | License](#-الرخصة--license)

---

## 🌟 نظرة عامة | Overview

<table>
<tr>
<td width="50%" dir="rtl" align="right">

### 🇸🇦 بالعربية

**saudi_hr** هو تطبيق Frappe مستقل، مبني على قمة ERPNext وHRMS، يُغطي **كامل متطلبات نظام العمل السعودي** الخاصة بإدارة الموارد البشرية.

صُمّم خصيصاً للمنشآت العاملة في المملكة العربية السعودية، بجميع أحجامها، ويشمل:

- **20 نوع بيانات** تغطي دورة حياة الموظف كاملاً
- **7 تقارير** للامتثال والرواتب والتحليل
- **5 صيغ طباعة** عربية RTL رسمية
- **2 سير عمل** معتمد للموافقات
- **4 إشعارات بريدية** تلقائية
- تكامل مع **GOSI, MLSD, Nitaqat, WPS**

</td>
<td width="50%" align="left">

### 🇬🇧 In English

**saudi_hr** is a standalone Frappe application built on ERPNext + HRMS that covers **all Saudi Labor Law requirements** for HR management.

Built for establishments of any size operating in Saudi Arabia. Includes:

- **20 DocTypes** covering the full employee lifecycle
- **7 Reports** for compliance, payroll, and analytics
- **5 Arabic RTL Print Formats** for official documents
- **2 Approval Workflows** for key transactions
- **4 Automated Email Notifications**
- Integration with **GOSI, MLSD, Nitaqat, WPS**

</td>
</tr>
</table>

---

## 💻 المتطلبات | Requirements

| المكوّن | Component | الإصدار الأدنى | Min Version |
|---------|-----------|----------------|-------------|
| Python | Python | ≥ 3.10 | ≥ 3.10 |
| Frappe Framework | Frappe Framework | ≥ 15.0.0 | ≥ 15.0.0 |
| ERPNext | ERPNext | ≥ 15.0.0 | ≥ 15.0.0 |
| HRMS | HRMS | ≥ 15.0.0 | ≥ 15.0.0 |
| MariaDB | MariaDB | ≥ 10.6 | ≥ 10.6 |
| Node.js | Node.js | ≥ 18 | ≥ 18 |

---

## ⚙️ التثبيت | Installation

```bash
# 1. احصل على التطبيق | Get the app
bench get-app https://github.com/ahmadmdm/hr-saudi-arabia-erpnext.git

# 2. ثبّت على الموقع | Install on your site
bench --site <your-site-name> install-app saudi_hr

# 3. أعد البناء وامسح الكاش | Build and clear cache
bench build --app saudi_hr
bench --site <your-site-name> clear-cache
```

> **ملاحظة:** يجب تثبيت `frappe`, `erpnext`, و`hrms` قبل هذا التطبيق.  
> **Note:** `frappe`, `erpnext`, and `hrms` must be installed first.

---

## 🧩 المكونات | Features

### أنواع البيانات | DocTypes

#### 📁 العقود والتوظيف | Contracts & Employment

| DocType | النوع | المادة | الوصف |
|---------|-------|--------|-------|
| Saudi Employment Contract | عقد العمل السعودي | م.37–46 | عقود محددة/غير محددة المدة مع تنبيهات الانتهاء التلقائية — Fixed/open-ended contracts with auto expiry alerts |
| Termination Notice | إشعار إنهاء الخدمة | م.75–76 | إشعار 30/60 يوم مع سير عمل موافقة — 30/60 day notice with approval workflow |
| Disciplinary Procedure | إجراء تأديبي | م.65–80 | تأديب تدريجي: إنذار ← توقف ← فصل — Progressive: warning → suspension → termination |
| Training Record | سجل التدريب | م.60–64 | تدريب إلزامي وبرامج السعودة والشهادات — Mandatory training, Saudization programs, certifications |
| Medical Examination | الفحص الطبي | — | ما قبل التعيين، دوري، ما بعد الإصابة — Pre-employment, periodic, post-injury |

#### 💰 الرواتب والمزايا | Payroll & Benefits

| DocType | النوع | المادة | الوصف |
|---------|-------|--------|-------|
| End of Service Benefit | مكافأة نهاية الخدمة | م.84 | احتساب EOSB تلقائي (½ و⅓ الراتب) — Auto EOSB calculation |
| GOSI Contribution | مساهمة التأمينات | GOSI | اشتراكات للسعوديين وغير السعوديين — Saudi & non-Saudi contribution rates |
| Overtime Request | طلب عمل إضافي | م.107 | احتساب 150% مع موافقة — 150% overtime with workflow |
| Saudi Monthly Payroll | مسير الرواتب الشهري | م.90–102 | مسير شامل بجدول موظفين — Full payroll with employee table |
| Annual Leave Disbursement | صرف الإجازة السنوية | م.109 | 21 يوم (أقل من 5 سنوات) / 30 يوم — 21 days (<5yr) / 30 days |

#### 🏖️ الإجازات | Leave Management

| DocType | النوع | المادة | الوصف |
|---------|-------|--------|-------|
| Saudi Sick Leave | الإجازة المرضية | م.117 | 100% ← 75% ← 0% حسب المدة — Tiered pay: 100%/75%/0% |
| Maternity Paternity Leave | إجازة الأمومة والأبوة | م.151، م.160 | 10 أسابيع للأم، 3 أيام للأب — 10 weeks mother / 3 days father |
| Special Leave | الإجازة الخاصة | م.113 | حج (15 يوم)، وفاة (5)، زواج (5) — Hajj/Bereavement/Marriage |

#### 🏛️ الامتثال | Compliance

| DocType | النوع | الجهة | الوصف |
|---------|-------|-------|-------|
| Nitaqat Record | سجل نطاقات | وزارة الموارد البشرية | تتبع نسبة السعودة والتصنيف — Saudization quota tracking & Nitaqat tier |
| Work Permit Iqama | تصريح العمل والإقامة | الجوازات | انتهاء الإقامات والتأشيرات — Iqama / visa expiry tracking |
| Work Injury | إصابة العمل | GOSI م.148–156 | إبلاغ إلزامي خلال 3 أيام — Mandatory 3-day GOSI reporting |
| Labor Dispute | نزاع عمالي | MLSD م.218–221 | تتبع قضايا وزارة العمل والمحاكم — MLSD/court case tracking |
| Monthly Attendance Record | سجل الحضور الشهري | م.102 | سجل رسمي مع تفصيل يومي وحساب تلقائي — Official monthly record with auto-totals |

---

### التقارير | Reports

| التقرير | Report | الوصف | Description |
|---------|--------|-------|-------------|
| GOSI Monthly Report | تقرير GOSI الشهري | قائمة الاشتراكات الشهرية | Monthly contributions list for GOSI portal |
| EOSB Calculation Report | تقرير احتساب EOSB | تفصيل مكافأة كل موظف | Detailed EOSB breakdown per employee |
| Work Permit Expiry Report | انتهاء التصاريح | تنبيه مسبق للإقامات | Advance warning for expiring permits |
| Nitaqat Compliance Report | امتثال نطاقات | تحليل نسبة السعودة | Current Saudization ratio analysis |
| Saudi Leave Balance Report | رصيد الإجازات | أرصدة جميع أنواع الإجازات | All leave types balances |
| Contract Expiry Report | انتهاء العقود | عقود تنتهي قريباً | Contracts expiring within a period |
| WPS Export Report | تصدير WPS | ملف SIF لنظام حماية الأجور | MLSD SIF format for Wage Protection System |

---

### صيغ الطباعة | Print Formats

| الصيغة | Print Format | الوصف |
|--------|-------------|-------|
| Saudi Employment Contract (Arabic) | عقد العمل بالعربية | نموذج RTL رسمي للعقود |
| EOSB Letter (Arabic) | خطاب مكافأة نهاية الخدمة | خطاب رسمي باللغة العربية |
| GOSI Contribution (Arabic) | نموذج التأمينات | نموذج GOSI الرسمي |
| Termination Notice (Arabic) | إشعار الإنهاء | خطاب إنهاء الخدمة الرسمي |
| Salary Certificate (Arabic) | شهادة الراتب | للبنوك والجهات الحكومية |

---

### سير العمل | Workflows

| سير العمل | Workflow | الحالات | States |
|-----------|---------|---------|--------|
| Overtime Approval | موافقة العمل الإضافي | مسودة ← قيد الموافقة ← معتمد/مرفوض | Draft → Pending → Approved/Rejected |
| Termination Approval | موافقة الإنهاء | مسودة ← مراجعة HR ← مراجعة الإدارة ← معتمد | Draft → HR → Management → Approved |

---

### التنبيهات التلقائية | Automated Notifications

| التنبيه | Alert | موعد الإرسال | When |
|---------|-------|--------------|------|
| Contract Expiry Alert | تنبيه انتهاء العقد | قبل 30 يوماً | 30 days before expiry |
| Iqama Expiry Alert | تنبيه انتهاء الإقامة | قبل 60 يوماً | 60 days before expiry |
| GOSI Contribution Due | تنبيه GOSI الشهري | أول الشهر | 1st of each month |
| Overtime Submitted Alert | تقديم عمل إضافي | عند التقديم | On submission |
| Probation End Alert *(scheduler)* | انتهاء فترة التجربة | قبل 14 يوماً — م.53 | 14 days before end — Art. 53 |

---

## ⚖️ التغطية القانونية | Legal Coverage

### مواد نظام العمل السعودي | Saudi Labor Law Articles

<table>
<tr>
<th>المادة / Article</th>
<th>الموضوع / Subject</th>
<th>المكوّن / Component</th>
</tr>
<tr><td>م.37–46</td><td>عقود العمل وشروطها / Employment contracts and terms</td><td>Saudi Employment Contract</td></tr>
<tr><td>م.53</td><td>فترة التجربة 90 يوم / Probation period 90 days</td><td>Probation End Alert (Scheduler)</td></tr>
<tr><td>م.60–64</td><td>التدريب الإلزامي / Mandatory training</td><td>Training Record</td></tr>
<tr><td>م.65–80</td><td>الجزاءات التأديبية / Disciplinary penalties</td><td>Disciplinary Procedure</td></tr>
<tr><td>م.75–76</td><td>إشعار إنهاء الخدمة / Termination notice</td><td>Termination Notice + Workflow</td></tr>
<tr><td>م.84</td><td>مكافأة نهاية الخدمة / End of Service Benefit</td><td>End of Service Benefit</td></tr>
<tr><td>م.90–102</td><td>الرواتب وسجلات الحضور / Wages and attendance</td><td>Saudi Monthly Payroll + Monthly Attendance Record</td></tr>
<tr><td>م.107</td><td>العمل الإضافي 150% / Overtime 150%</td><td>Overtime Request</td></tr>
<tr><td>م.109</td><td>الإجازة السنوية 21/30 يوم / Annual leave</td><td>Annual Leave Disbursement</td></tr>
<tr><td>م.113</td><td>الإجازات الخاصة / Special leave</td><td>Special Leave</td></tr>
<tr><td>م.117</td><td>الإجازة المرضية / Sick leave</td><td>Saudi Sick Leave</td></tr>
<tr><td>م.148–156</td><td>إصابات العمل / Work injuries</td><td>Work Injury</td></tr>
<tr><td>م.151 & 160</td><td>إجازة الأمومة والأبوة / Parental leave</td><td>Maternity Paternity Leave</td></tr>
<tr><td>م.218–221</td><td>النزاعات العمالية / Labor disputes</td><td>Labor Dispute</td></tr>
<tr><td>نظام GOSI</td><td>التأمينات الاجتماعية / Social insurance</td><td>GOSI Contribution + Report</td></tr>
<tr><td>نظام نطاقات</td><td>نسبة التوطين / Saudization quota</td><td>Nitaqat Record + Compliance Report</td></tr>
<tr><td>نظام WPS</td><td>حماية الأجور / Wage protection</td><td>WPS Export Report</td></tr>
</table>

---

## 📖 الاستخدام | Usage

### الخطوات الأولى | Getting Started

<table>
<tr>
<td width="50%" dir="rtl" align="right">

**بعد التثبيت:**

1. افتح **فضاء العمل: Saudi HR**
2. ابدأ بـ **إعدادات Saudi HR** — حدد نسب GOSI وسياسات الإجازات
3. أنشئ **سجل نطاقات** للمنشأة
4. أضف **عقود العمل** لكل موظف
5. سجّل موظفيك في **GOSI**

</td>
<td width="50%">

**After installation:**

1. Open **Saudi HR Workspace**
2. Configure **Saudi HR Settings** — set GOSI rates, leave policies
3. Create a **Nitaqat Record** for your establishment
4. Add **Employment Contracts** per employee
5. Register employees in **GOSI**

</td>
</tr>
</table>

### دورة حياة الموظف | Employee Lifecycle

```
 التعيين | Hire        →  عقد العمل + فحص طبي + تسجيل GOSI
                            Contract + Medical Exam + GOSI Registration

 أثناء العمل | Active   →  الرواتب الشهرية + الإجازات + العمل الإضافي + التدريب
                            Monthly Payroll + Leaves + Overtime + Training

 إنهاء الخدمة | Exit    →  إشعار الإنهاء + احتساب EOSB + شهادة الراتب
                            Termination Notice + EOSB Calculation + Salary Certificate
```

### التقارير الشهرية | Monthly Compliance Checklist

```bash
✅ GOSI Monthly Report      → رفعه إلى بوابة GOSI
✅ WPS Export (SIF)         → تحميله في نظام حماية الأجور
✅ Nitaqat Compliance       → مراقبة نسبة السعودة
✅ Work Permit Expiry       → متابعة الإقامات المنتهية
```

---

## 🗂️ هيكل المشروع | Project Structure

```
saudi_hr/
├── saudi_hr/
│   ├── __init__.py                         # v1.1.0
│   ├── hooks.py                            # Frappe hooks & scheduler
│   ├── tasks.py                            # Scheduled tasks (probation alerts)
│   └── saudi_hr/
│       ├── doctype/                        # 20 DocTypes
│       │   ├── annual_leave_disbursement/  # م.109
│       │   ├── disciplinary_procedure/     # م.65-80
│       │   ├── end_of_service_benefit/     # م.84
│       │   ├── gosi_contribution/          # GOSI
│       │   ├── labor_dispute/              # م.218-221
│       │   ├── maternity_paternity_leave/  # م.151,160
│       │   ├── medical_examination/        # ★ NEW v1.1.0
│       │   ├── monthly_attendance_detail/  # ★ NEW v1.1.0 (child)
│       │   ├── monthly_attendance_record/  # ★ NEW v1.1.0  م.102
│       │   ├── nitaqat_record/             # Nitaqat
│       │   ├── overtime_request/           # م.107
│       │   ├── saudi_employment_contract/  # م.37-46
│       │   ├── saudi_hr_settings/          # Settings
│       │   ├── saudi_monthly_payroll/      # م.90-102
│       │   ├── saudi_monthly_payroll_employee/ # Child table
│       │   ├── saudi_sick_leave/           # م.117
│       │   ├── special_leave/              # م.113
│       │   ├── termination_notice/         # م.75-76
│       │   ├── training_record/            # ★ NEW v1.1.0  م.60-64
│       │   ├── work_injury/               # م.148-156
│       │   └── work_permit_iqama/         # Iqama/Visa
│       ├── report/                        # 7 Reports
│       ├── print_format/                  # 5 Arabic Print Formats
│       ├── workflow/                      # 2 Workflows
│       ├── notification/                  # 4 Notifications
│       └── workspace/                    # Saudi HR Workspace
├── pyproject.toml
├── setup.py
└── README.md
```

---

## 🆕 سجل التغييرات | Changelog

### v1.3.0 — ٢٢ مارس ٢٠٢٦ *(الإصدار الحالي | Current)*

**إصلاح الأخطاء الحرجة | Critical Bug Fixes:**

| الملف | الإصلاح |
|-------|---------|
| `gosi_contribution.py` | إنشاء قيد يومي تلقائي عند الاعتماد بدلاً من `pass` |
| `end_of_service_benefit.py` | إضافة التحقق من ترتيب التواريخ + منطق الاستقالة الصحيح |
| `overtime_request.py` | إنشاء قيد يومي بدلاً من Additional Salary |
| `saudi_monthly_payroll.py` | استخدام أيام الشهر الفعلية بدلاً من الثابت 30 |
| `tasks.py` | إصلاح خطأ `docname=""` في تنبيهات الإجازة المرضية |
| `api.py` | تسجيل تحذير عند تجاوز فحص GPS |

**فصل الاعتماد عن HRMS | Partial HRMS Decoupling:**

| المكوّن | Component | التغيير |
|---------|-----------|--------|
| ★ Saudi Employee Checkin | حضور الموظف السعودي | DocType جديد يحل محل HRMS Employee Checkin |
| ★ Saudi Daily Attendance | الحضور اليومي السعودي | DocType جديد يحل محل HRMS Attendance |
| Overtime Request | طلب العمل الإضافي | قيد يومي مباشر بدلاً من Additional Salary |
| Saudi Monthly Payroll | مسير الرواتب الشهري | قيد يومي مباشر بدلاً من Payroll Entry |

**إصلاحات تقنية | Technical Fixes:**
- إصلاح أسماء الـ classes: `GOSIContribution` و `EndofServiceBenefit` لتتوافق مع توقعات Frappe وتمنع حذفها عند كل `migrate`
- إعادة تسمية دالة `create_additional_salary` → `create_overtime_journal_entry` في `hooks.py`
- تحديث حقل `linked_payroll_entry` في Annual Leave ليشير إلى `Journal Entry`

---

### v1.1.0 — ١٧ مارس ٢٠٢٦

**مكونات جديدة | New Components:**

| المكوّن | Component | الوصف |
|---------|-----------|-------|
| ★ Training Record | سجل التدريب | م.60-64: تدريب إلزامي، سعودة، شهادات |
| ★ Medical Examination | الفحص الطبي | ما قبل التعيين / دوري / ما بعد الإصابة |
| ★ Monthly Attendance Record | سجل الحضور الشهري | م.102: سجل رسمي مع حساب تلقائي للغياب والتأخير والعمل الإضافي |
| ★ Monthly Attendance Detail | تفاصيل الحضور | جدول تفصيلي يومي (child table) |
| ★ Work Injury | إصابة العمل | م.148-156: إبلاغ GOSI خلال 3 أيام |
| ★ Disciplinary Procedure | إجراء تأديبي | م.65-80: تأديب تدريجي |
| ★ Special Leave | إجازة خاصة | م.113: حج وعزاء وزواج |
| ★ Annual Leave Disbursement | صرف الإجازة السنوية | م.109: 21/30 يوم |
| ★ Labor Dispute | نزاع عمالي | م.218-221: MLSD والمحاكم |
| ★ WPS Export Report | تقرير WPS | ملف SIF لنظام حماية الأجور |
| ★ Salary Certificate Print Format | شهادة الراتب | RTL عربي للبنوك والجهات |
| ★ Probation End Alerts | تنبيه فترة التجربة | م.53: تنبيه تلقائي قبل 14 يوماً |

### v1.0.0 — *(الإصدار الأولي | Initial Release)*

- عقود العمل، EOSB، GOSI، Nitaqat، تصاريح العمل، الإجازات السنوية والمرضية، إجازة الأمومة، العمل الإضافي، مسير الرواتب الشهري
- 5 صيغ طباعة عربية، 2 سير عمل، 4 إشعارات

---

## 🤝 المساهمة | Contributing

<table>
<tr>
<td dir="rtl" align="right">

نرحب بمساهماتكم! الخطوات:

1. **Fork** المستودع
2. أنشئ فرعاً: `git checkout -b feature/اسم-الميزة`
3. اكتب الكود مع توثيق المادة القانونية المرتبطة
4. أرسل **Pull Request** مع وصف واضح

يُرجى اتباع [معايير Frappe](https://frappeframework.com/docs/user/en/contributing).

</td>
<td>

Contributions are welcome!

1. **Fork** the repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Write code with references to relevant law articles
4. Submit a **Pull Request** with a clear description

Please follow [Frappe Development Guidelines](https://frappeframework.com/docs/user/en/contributing).

</td>
</tr>
</table>

---

## 📧 الدعم | Support

- **GitHub Issues:** [github.com/ahmadmdm/hr-saudi-arabia-erpnext/issues](https://github.com/ahmadmdm/hr-saudi-arabia-erpnext/issues)
- **Email:** info@ideaorbit.net
- **Company:** IdeaOrbit — [ideaorbit.net](https://ideaorbit.net)

---

## 📄 الرخصة | License

مُرخَّص بموجب **GNU GPL v3.0** — Licensed under **GNU General Public License v3.0**

See [license.txt](license.txt) for details.

---

<div align="center">

**صُنع بـ ❤️ للمملكة العربية السعودية | Made with ❤️ for Saudi Arabia 🇸🇦**

© 2026 [IdeaOrbit](https://ideaorbit.net)

</div>
