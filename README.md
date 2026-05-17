<div align="center" dir="rtl">

# Saudi HR for ERPNext

## نظام موارد بشرية سعودي مستقل لبيئات ERPNext v15

**تشغيل يومي، امتثال سعودي، رواتب، حضور، عقود، وموافقات في تجربة واحدة مصممة للمنشآت داخل المملكة.**

<br>

<a href="https://github.com/ahmadmdm/hr-saudi-arabia-erpnext/releases/tag/v1.16.4"><img alt="Version 1.16.4" src="https://img.shields.io/badge/version-1.16.4-0F766E?style=for-the-badge"></a>
<img alt="Frappe v15" src="https://img.shields.io/badge/Frappe-v15-2563EB?style=for-the-badge">
<img alt="ERPNext v15" src="https://img.shields.io/badge/ERPNext-v15-7C3AED?style=for-the-badge">
<img alt="No HRMS dependency" src="https://img.shields.io/badge/HRMS-not%20required-16A34A?style=for-the-badge">
<a href="https://github.com/ahmadmdm/hr-saudi-arabia-erpnext/actions/workflows/quality.yml"><img alt="Quality checks" src="https://img.shields.io/github/actions/workflow/status/ahmadmdm/hr-saudi-arabia-erpnext/quality.yml?branch=version-15&label=quality&style=for-the-badge"></a>
<a href="LICENSE"><img alt="GPL 3.0" src="https://img.shields.io/badge/license-GPL--3.0-EA580C?style=for-the-badge"></a>

<br><br>

<a href="#-بطاقة-المنتج--product-card">بطاقة المنتج</a>
 · <a href="#-الجولة-السريعة--quick-tour">الجولة السريعة</a>
 · <a href="#-الوثائق--docs">الوثائق</a>
 · <a href="#-التثبيت--installation">التثبيت</a>
 · <a href="#-المكونات--features">المكونات</a>
 · <a href="#-سجل-التغييرات--changelog">الإصدارات</a>

</div>

<br>

<p align="center">
  <img src="docs/images/professional-hr-hub-desktop.png" alt="Professional HR Hub desktop dashboard" width="100%">
</p>

<p align="center">
  <sub>واجهة <strong>Professional HR Hub</strong> الفعلية من الاختبار البصري: مؤشرات، إجراءات، امتثال، وتنقل سريع من شاشة واحدة.</sub>
</p>

---

## 📌 بطاقة المنتج | Product Card

<table>
<tr>
<td width="25%" align="center">
  <strong>Standalone</strong>
  <br>
  يعمل فوق <code>frappe</code> و<code>erpnext</code> فقط
  <br>
  <sub>لا يحتاج HRMS</sub>
</td>
<td width="25%" align="center">
  <strong>Saudi Compliance</strong>
  <br>
  GOSI, WPS, Nitaqat, EOSB
  <br>
  <sub>مهيأ لنظام العمل السعودي</sub>
</td>
<td width="25%" align="center">
  <strong>Operational Hub</strong>
  <br>
  واجهة Professional HR Hub
  <br>
  <sub>للعمل اليومي لا للعروض فقط</sub>
</td>
<td width="25%" align="center">
  <strong>Ready to Move</strong>
  <br>
  تبعيات موثقة واختبارات جاهزة
  <br>
  <sub>أسهل عند النقل لبيئة أخرى</sub>
</td>
</tr>
</table>

---

## 🌟 نظرة عامة | Overview

<table>
<tr>
<td width="50%" dir="rtl" align="right">

### بالعربية

**saudi_hr** ليس مجرد مجموعة DocTypes. هو مساحة تشغيل موارد بشرية سعودية متكاملة داخل ERPNext: يبدأ من متابعة اليوم، يمر بالحضور والورديات والإجازات والرواتب، وينتهي بالتقارير النظامية والوثائق الرسمية.

صُمّم التطبيق ليبقى مستقلًا عن HRMS، وهذا يجعل نقله وترقيته أوضح في البيئات التي تريد ERPNext مع طبقة موارد بشرية سعودية متخصصة فقط.

**النتيجة:** تجربة HR عملية، عربية، قابلة للتدقيق، ومتصلة بالاحتياج السعودي الحقيقي.

</td>
<td width="50%" dir="ltr" align="left">

### In English

**saudi_hr** is more than a set of DocTypes. It is a Saudi HR operating layer inside ERPNext: daily monitoring, attendance, shifts, leaves, payroll, compliance reports, and official documents in one focused experience.

The app is deliberately independent from HRMS, making deployment and upgrades clearer for teams that want ERPNext with a dedicated Saudi HR layer.

**The result:** a practical, auditable, Arabic-first HR experience for Saudi operations.

</td>
</tr>
</table>

### لماذا يلفت الانتباه؟ | Why It Stands Out

| المسار | Track | القيمة العملية |
|--------|-------|----------------|
| تجربة تشغيلية | Operational UX | يبدأ من عمل HR اليومي بدل قائمة مستندات طويلة |
| استقلالية تقنية | Technical Independence | لا يعتمد على HRMS ويعمل فوق `frappe` و`erpnext` فقط |
| امتثال سعودي | Saudi Compliance | يغطي GOSI، WPS، نطاقات، الإجازات، نهاية الخدمة، العقود، والإصابات |
| جاهزية ميدانية | Field Readiness | حضور جوال، مواقع، ورديات، مراجعة فريق، وشجرة تنظيمية |
| توثيق رسمي | Official Output | صيغ طباعة عربية ومسارات اعتماد قابلة للمراجعة |

---

## 🖼️ الجولة السريعة | Quick Tour

<p align="center">
  <img src="docs/images/saudi-hr-tour.gif" alt="Saudi HR animated product tour" width="100%">
</p>

<table>
<tr>
<td width="58%" align="center">
  <img src="docs/images/saudi-hr-workspace.png" alt="Saudi HR Workspace" width="100%">
</td>
<td width="42%" dir="rtl" align="right">
  <h3>1. ابدأ من مساحة عمل مرتبة</h3>
  <p>مساحة Saudi HR تقسم العمل حسب الاستخدام الفعلي: متابعة اليوم، عمليات الموظف، الحضور، الرواتب، السياسات، والامتثال.</p>
</td>
</tr>
<tr>
<td width="58%" align="center">
  <img src="docs/images/team-attendance-review.png" alt="Team Attendance Review report" width="100%">
</td>
<td width="42%" dir="rtl" align="right">
  <h3>2. راقب الحضور قبل أن يتحول إلى مشكلة</h3>
  <p>تقرير مراجعة الفريق يساعد المشرفين وHR على رؤية التأخير، الغياب، الحركات المفتوحة، ومشكلات التحقق من نفس الشاشة.</p>
</td>
</tr>
<tr>
<td width="58%" align="center">
  <img src="docs/images/leave-balance-report.png" alt="Saudi Leave Balance report" width="100%">
</td>
<td width="42%" dir="rtl" align="right">
  <h3>3. اربط الإجازات بالسياسات السعودية</h3>
  <p>أرصدة الإجازات تظهر بصورة قابلة للمراجعة، مع مسارات اعتماد مناسبة للموظف والمدير والموارد البشرية والمالية.</p>
</td>
</tr>
<tr>
<td width="58%" align="center">
  <img src="docs/images/employee-org-tree.png" alt="Employee Org Tree page" width="100%">
</td>
<td width="42%" dir="rtl" align="right">
  <h3>4. افهم الهيكل قبل القرار</h3>
  <p>الشجرة التنظيمية تعرض الأقسام، العلاقات الإدارية، والموافقين حتى تصبح القرارات الإدارية أسرع وأوضح.</p>
</td>
</tr>
</table>

<details>
<summary><strong>Mobile view | عرض الجوال</strong></summary>
<br>
<p align="center">
  <img src="docs/images/professional-hr-hub-mobile.png" alt="Professional HR Hub mobile" width="340">
</p>
<p align="center">
  <sub>الواجهة مصممة لتبقى قابلة للقراءة والتنقل على الجوال أثناء العمل الميداني.</sub>
</p>
</details>

---

## 🧭 الوثائق | Docs

| الدليل | Guide | متى تستخدمه؟ |
|--------|-------|--------------|
| [التثبيت](docs/installation.md) | Installation | تثبيت التطبيق على bench جديد أو موقع ERPNext v15 |
| [النقل والتشغيل](docs/deployment.md) | Deployment | نقل التطبيق إلى نظام آخر والتحقق بعد الترقية |
| [فصل HRMS](docs/hrms-decoupling.md) | HRMS Decoupling | إثبات أن التطبيق لا يحتاج HRMS ومعرفة البدائل السعودية داخله |
| [الجولة المرئية](docs/visual-tour.md) | Visual Tour | استعراض الصور، GIF، وصورة Social Preview |
| [بيانات الديمو](docs/demo-data.md) | Demo Data | إنشاء موظف ومدير وعقد وإجازة ورواتب تجريبية في بيئة اختبار |
| [التبعيات](DEPENDENCIES.md) | Dependencies | عقد التبعيات الكامل ومسار الصوت الاختياري |

---

## 💻 المتطلبات | Requirements

| المكوّن | Component | الإصدار الأدنى | Min Version |
|---------|-----------|----------------|-------------|
| Python | Python | ≥ 3.10 | ≥ 3.10 |
| Frappe Framework | Frappe Framework | ≥ 15.0.0 | ≥ 15.0.0 |
| ERPNext | ERPNext | ≥ 15.0.0 | ≥ 15.0.0 |
| MariaDB | MariaDB | ≥ 10.6 | ≥ 10.6 |
| Node.js | Node.js | ≥ 18 | ≥ 18 |

**بيئة التحقق الحالية | Verified Stack**

- Frappe `15.107.2`
- ERPNext `15.107.0`
- Saudi HR `1.16.4`
- Python `3.10`
- MariaDB `10.6+`
- Node.js `24.x`
- لا يعتمد التطبيق على HRMS، ويعمل بشكل مستقل فوق `frappe` و`erpnext` فقط

---

## ⚙️ التثبيت | Installation

```bash
# 1. احصل على التطبيق | Get the app
bench get-app --branch version-15 https://github.com/ahmadmdm/hr-saudi-arabia-erpnext.git

# 2. ثبّت على الموقع | Install on your site
bench --site <your-site-name> install-app saudi_hr

# 3. أعد البناء وامسح الكاش | Build and clear cache
bench build --app saudi_hr
bench --site <your-site-name> clear-cache
```

> **ملاحظة:** يجب تثبيت `frappe` و`erpnext` قبل هذا التطبيق. التثبيت الأساسي يحتاج `openpyxl` و`openlocationcode` فقط. وضع التحقق الصوتي الخفيف يعمل عبر نص التحدي المرسل من المتصفح ولا يسحب حزم الذكاء الاصطناعي الثقيلة. لتفعيل وضع البصمة الصوتية الكاملة ثبّت الإضافة الاختيارية `saudi_hr[voice-full]` أو استخدم `requirements-voice-cpu.txt`.
> **Note:** `frappe` and `erpnext` must be installed first. The base install only requires `openpyxl` and `openlocationcode`. Lightweight voice verification uses the browser-provided challenge transcript and does not pull the heavy AI packages. To enable full voice biometric mode, install the optional `saudi_hr[voice-full]` extra or use `requirements-voice-cpu.txt`.

### التحقق من الاعتماديات | Dependency Verification

```bash
# Verify Python package dependencies
./env/bin/python -c "import openpyxl, openlocationcode; print('base runtime dependencies ok')"

# Optional: verify full biometric voice dependencies after installing them
./env/bin/python -c "import torch, torchaudio, speechbrain, faster_whisper; print('full voice runtime dependencies ok')"

# Verify bench app test suite
bench --site <your-site-name> run-tests --app saudi_hr --skip-test-records
```

> **معلومة مهمة:** ملفات الاعتماديات موحدة في `pyproject.toml` و`setup.py` و`requirements.txt`. أضفنا أيضًا ملف `requirements-voice-cpu.txt` كخيار تشغيلي احتياطي للخوادم التي تحتاج فهرس PyTorch CPU صريح، لكن المسار الافتراضي للتثبيت يعتمد على بيانات الحزمة نفسها.  
> **Important:** Dependency declarations are aligned in `pyproject.toml`, `setup.py`, and `requirements.txt`. We also ship `requirements-voice-cpu.txt` as an operational fallback for servers that need the explicit PyTorch CPU index, but the default installation path still relies on the package metadata itself.

### نقل التطبيق إلى نظام آخر | Moving the App to Another System

```bash
# 1. داخل بيئة bench الجديدة | Inside the new bench environment
bench get-app --branch version-15 https://github.com/ahmadmdm/hr-saudi-arabia-erpnext.git

# 2. ثبّت التطبيق على الموقع | Install the app on the target site
bench --site <your-site-name> install-app saudi_hr

# 3. طبّق الترقيات | Apply schema changes
bench --site <your-site-name> migrate

# 4. تحقق من التبعيات الأساسية | Verify base runtime dependencies
./env/bin/python -c "import openpyxl, openlocationcode; print('base dependencies ok')"

# Optional fallback for CPU-only environments with restricted package indexes
./env/bin/pip install -r apps/saudi_hr/requirements-voice-cpu.txt

# Optional: verify full voice dependencies after installing voice support
./env/bin/python -c "import torch, torchaudio, speechbrain, faster_whisper; print('voice dependencies ok')"

# 5. تحقّق من أهم المسارات بعد التثبيت | Validate the key app flows after install
bench --site <your-site-name> run-tests --app saudi_hr --module saudi_hr.saudi_hr.doctype.special_leave.test_special_leave --module saudi_hr.saudi_hr.doctype.annual_leave_disbursement.test_annual_leave_disbursement --module saudi_hr.saudi_hr.report.saudi_labor_coverage_matrix.test_saudi_labor_coverage_matrix
```

> **توصية تشغيلية:** إذا كنت ستستخدم صفحة الحضور بالجوال أو مواقع Plus Code مباشرة بعد النقل، شغّل `bench restart` أو أعد تشغيل خدمات الويب والـ workers بعد `migrate` لضمان تحميل الأصول وملفات الخدمة الحديثة.  
> **Operational note:** If you will use the mobile attendance page or Plus Code locations immediately after migration, run `bench restart` or restart the web and worker processes after `migrate` so the latest assets and service worker are loaded.

راجع [DEPENDENCIES.md](DEPENDENCIES.md) لعقد التبعيات الكامل، بما في ذلك تأكيد أن `hrms` ليس اعتماداً مطلوباً.

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
| Special Leave | الإجازة الخاصة | م.113 | حج (15 يوم، مرة واحدة بعد سنتين خدمة)، وفاة (5)، زواج (5) — Hajj/Bereavement/Marriage |

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
| Annual Leave Approval | موافقة الإجازة السنوية | مسودة ← موافقة المدير ← موافقة الموارد البشرية ← موافقة المالية ← معتمد/مرفوض | Draft → Manager Approval → HR Approval → Finance Approval → Approved/Rejected |
| Sick Leave Approval | موافقة الإجازة المرضية | مسودة ← موافقة المدير ← موافقة الموارد البشرية ← معتمد/مرفوض | Draft → Manager Approval → HR Approval → Approved/Rejected |
| Overtime Approval | موافقة العمل الإضافي | مسودة ← موافقة المدير ← موافقة الموارد البشرية ← معتمد/مرفوض | Draft → Manager Approval → HR Approval → Approved/Rejected |
| Salary Adjustment Approval | موافقة تعديل الراتب | مسودة ← موافقة المدير ← موافقة الموارد البشرية ← معتمد/مرفوض | Draft → Manager Approval → HR Approval → Approved/Rejected |
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
├── docs/
│   ├── images/                             # README, release, and social preview assets
│   ├── installation.md                     # Install guide
│   ├── deployment.md                       # Transfer and production checklist
│   ├── hrms-decoupling.md                  # HRMS independence notes
│   ├── visual-tour.md                      # Visual product tour
│   └── demo-data.md                        # Demo lifecycle seed guide
├── saudi_hr/
│   ├── __init__.py                         # App version
│   ├── hooks.py                            # Frappe hooks, pages, assets, scheduler
│   ├── tasks.py                            # Scheduled alerts and compliance tasks
│   └── saudi_hr/
│       ├── doctype/                        # Saudi HR DocTypes and controllers
│       ├── page/                           # Professional HR Hub, Org Tree, Attendance Hub
│       ├── report/                         # Compliance, payroll, attendance, leave reports
│       ├── print_format/                   # Arabic RTL official documents
│       ├── workflow/                       # Approval workflows
│       ├── notification/                   # Automated alerts
│       ├── workspace/                      # Saudi HR Desk workspace
│       ├── dashboard/                      # Desk dashboards
│       ├── dashboard_chart/                # KPI charts
│       └── number_card/                    # KPI number cards
├── DEPENDENCIES.md                         # Runtime and transfer dependency contract
├── requirements.txt                        # Base Python dependencies
├── requirements-voice-cpu.txt              # Optional full voice runtime fallback
├── pyproject.toml
├── setup.py
└── README.md
```

---

## 🆕 سجل التغييرات | Changelog

### v1.16.4 — ١٧ مايو ٢٠٢٦ *(الإصدار الحالي | Current)*

**تحسين العرض العام والتوثيق الاحترافي | Presentation, Docs, and Quality Release:**

| المكوّن | Component | التحديث |
|---------|-----------|----------|
| README Polish | تحسين README | تحويل المقدمة إلى صفحة عرض منتج أوضح مع GIF قصير وروابط وثائق مباشرة |
| Social Preview | صورة المشاركة | إضافة `docs/images/social-preview.png` لاستخدامها كصورة مشاركة للمستودع |
| Animated Tour | الجولة المتحركة | إضافة `docs/images/saudi-hr-tour.gif` كاستعراض سريع لواجهات التطبيق الفعلية |
| Documentation | الوثائق | إضافة أدلة مستقلة للتثبيت، النقل، فصل HRMS، الجولة المرئية، وبيانات الديمو |
| Demo Data | بيانات الديمو | توثيق أمر إنشاء سيناريو موظف ومدير وعقد وإجازة ورواتب للاختبار |
| GitHub Actions | فحوصات GitHub | إضافة فحص جودة خفيف للتبعيات، النسخة، README، والصور داخل GitHub Actions |
| License Metadata | بيانات الرخصة | توحيد ملف `LICENSE` وبيانات Frappe مع تصريح GPL v3.0 الموجود في README |

> **تعليق الإصدار | Release Note:** هذا إصدار عرض وتوثيق يجعل المستودع أكثر جاهزية للعرض العام والمشاركة: README أجمل، أصول المشاركة موجودة داخل المستودع، الوثائق منفصلة، وفحص GitHub Actions يؤكد سلامة التبعيات الأساسية ومسارات الصور.

> **بعد الترقية | Post-upgrade:** لا توجد تغييرات مخطط قاعدة بيانات في هذا الإصدار. إذا كنت تحدّث من نسخة أقدم، يكفي `bench --site <your-site-name> migrate` ثم `bench build --app saudi_hr` و`bench --site <your-site-name> clear-cache` كإجراء قياسي.

### v1.16.3 — ١٧ مايو ٢٠٢٦

**نشر GitHub المرئي وتثبيت هوية المنتج المستقل | Visual GitHub Release and Independent Product Identity:**

| المكوّن | Component | التحديث |
|---------|-----------|----------|
| README Experience | تجربة README | إعادة صياغة المقدمة كشرح منتج احترافي ثنائي اللغة مع صور فعلية من الواجهة |
| Visual Assets | أصول الصور | إضافة لقطات `professional-hr-hub`، مساحة العمل، مراجعة الحضور، أرصدة الإجازات، والشجرة التنظيمية |
| Release Version | رقم الإصدار | رفع نسخة التطبيق إلى `1.16.3` وتجهيز وسم Git للإصدار |
| Independence Statement | استقلالية التطبيق | توثيق أوضح أن التطبيق مستقل عن HRMS ويعمل فوق `frappe` و`erpnext` فقط |
| Transfer Readiness | جاهزية النقل | توضيح أوامر التثبيت على الفرع `version-15` لتقليل أخطاء النقل بين البيئات |

> **تعليق الإصدار | Release Note:** هذا الإصدار يركز على جاهزية النشر الخارجي: README أصبح واجهة عرض احترافية للتطبيق، الصور المرفقة مأخوذة من اختبار بصري فعلي، ورقم النسخة يثبت حالة التطبيق بعد فصل HRMS وتحسين مساحة العمل وواجهة `professional-hr-hub`.

> **بعد الترقية | Post-upgrade:** شغّل `bench --site <your-site-name> migrate` ثم `bench build --app saudi_hr` و`bench --site <your-site-name> clear-cache`. عند النقل إلى نظام جديد استخدم أمر `bench get-app --branch version-15` لضمان تحميل فرع ERPNext v15 الصحيح.

### v1.16.0 — ٢٨ أبريل ٢٠٢٦

**التشغيل الحي للحضور الجوال ومسار اعتماد المالية | Live Mobile Attendance, Finance Routing, and Runtime Compatibility:**

| المكوّن | Component | التحديث |
|---------|-----------|----------|
| Mobile Attendance API | واجهات حضور الجوال الخارجية | إضافة contract موثّق وواجهات token-based لإصدار بيانات الربط، جلب الحالة، المواقع، تسجيل الحركة، وطلب الإجازة مع الحفاظ على صلاحيات المستخدم نفسه |
| Mobile Attendance UI | واجهة الحضور الجوال | استخدام `GET` للقراءات فقط وتحميل اللوحة عبر `Promise.allSettled` حتى لا يؤدي تعثر تحميل المواقع إلى إسقاط الصفحة بالكامل |
| Employee Org Tree | شجرة الارتباط الوظيفي | إضافة صفحة Desk جديدة لعرض الأقسام والتقارير المباشرة والموافقين، مع إظهارها داخل مساحة عمل Saudi HR |
| Annual Leave Workflow | سير الإجازة السنوية | إضافة مرحلة `Pending Finance Approval` وربط صلاحيات `Accounts Manager` باستعلامات وصلاحيات الإجازة السنوية |
| Voice Verification Runtime | تشغيل البصمة الصوتية | معالجة تعارض SpeechBrain مع إصدارات Torch الحالية عبر shim لتوافق `torch.amp` قبل تحميل مكتبات التحقق الصوتي |

> **تعليق الإصدار | Release Note:** هذا الإصدار يحول الإضافات الأخيرة من مجرد كود موجود داخل المستودع إلى مسارات تشغيلية قابلة للاستخدام فعليًا: حضور جوال بواجهات تكامل واضحة، شجرة تنظيمية متاحة من الـ Workspace، مسار اعتماد سنوي ينتهي بالمالية، وتوافق runtime أفضل للبصمة الصوتية في البيئات الحية.

> **بعد الترقية | Post-upgrade:** شغّل `bench --site <your-site-name> migrate` ثم `bench build --app saudi_hr` و`bench --site <your-site-name> clear-cache`. إذا كانت الـ Workspace موجودة مسبقًا في قاعدة البيانات، فتأكد من استيراد التغييرات القياسية أثناء الترقية حتى يظهر اختصار `Employee Org Tree` والمسار المحدّث للإجازة السنوية.

### v1.15.0 — ٢٧ أبريل ٢٠٢٦

**الواجهة العربية الموحّدة وتجربة العمل اليومية | Unified Arabic UX and Daily Operations Experience:**

| المكوّن | Component | التحديث |
|---------|-----------|----------|
| Saudi HR Workspace | مساحة عمل Saudi HR | إعادة تنظيم مساحة العمل إلى مسار تشغيلي أوضح يبدأ بمتابعة اليوم ثم إجراءات الموظف ثم السياسات والامتثال والمؤشرات |
| Attendance Action Hub | مركز متابعة الحضور | تحويل النصوص المختلطة داخل الصفحة إلى مفاتيح ترجمة قياسية وربطها بطبقة الترجمة العربية الاحترافية |
| Mobile Attendance | الحضور عبر الجوال | تعريب الواجهة والنصوص الديناميكية والقيم التشغيلية مثل الموقع والوردية والحالات والإجازات مع تحسين العبارات العربية الوظيفية |
| Apps Screen | شاشة التطبيقات | توحيد عناوين التطبيق واختصاراته إلى مفاتيح إنجليزية قياسية حتى تتولى طبقة الترجمة العربية إظهارها بشكل صحيح في النظام العربي |
| Publishing | النشر والكاش | رفع نسخة service worker ونسخ الأصول لضمان وصول النصوص الجديدة مباشرة في البيئة الحية دون بقايا cache قديمة |

> **تعليق الإصدار | Release Note:** هذا الإصدار يركز على صقل تجربة المستخدم العربية داخل Saudi HR في بيئة التشغيل الحية، بحيث تظهر المساحات والصفحات اليومية والاختصارات والقيم الديناميكية بلغة عربية مهنية ومتسقة بدل الصيغ المختلطة أو الحرفية.

> **بعد الترقية | Post-upgrade:** شغّل `bench --site <your-site-name> migrate` ثم `bench build --app saudi_hr` و`bench --site <your-site-name> clear-cache`، وأعد تحميل صفحة الحضور عبر الجوال لتحديث نسخة الـ service worker.

### v1.14.0 — ٢٧ أبريل ٢٠٢٦

**الحضور الذكي والتحقق الصوتي والامتثال التشغيلي | Smart Attendance, Voice Verification, and Operational Compliance:**

| المكوّن | Component | التحديث |
|---------|-----------|----------|
| Mobile Attendance | حضور الجوال | إضافة سياسة حضور مبنية على الورديات الفعلية، مع عرض وقت البداية والنهاية المتوقعين وحالة الوردية داخل صفحة الجوال |
| Voice Verification | التحقق الصوتي | إضافة تسجيل بصمة صوتية أولية إلزامية، تحدي رقمي لكل حركة، منع إعادة التسجيل الذاتي، وإتاحة إعادة التهيئة عبر الموارد البشرية فقط |
| Attendance Review | متابعة الحضور | إضافة تقرير `Team Attendance Review` وصفحة `Attendance Action Hub` للإشراف المباشر على التأخير، الغياب، الحركات المفتوحة، ومشكلات التحقق الصوتي |
| WPS Lifecycle | دورة حماية الأجور | إضافة `WPS Submission` وتقرير `WPS Submission Tracker` لتتبع الإرسال والرفض والتصحيح والقبول بدل الاكتفاء بملف التصدير فقط |
| Workspace | مساحة العمل | توسيع `Saudi HR Workspace` لإظهار إجراءات الحضور، البصمة الصوتية، إعدادات الورديات، ومسارات WPS من نفس الواجهة |
| Packaging | التغليف والتبعيات | توحيد إعلان تبعيات محرك الصوت في `pyproject.toml` و`setup.py` و`requirements.txt` لضمان تثبيتها تلقائيًا عند نقل التطبيق أو تثبيته على بيئة أخرى |

> **تعليق الإصدار | Release Note:** هذا الإصدار يحول التطبيق من طبقة HR تشغيلية أساسية إلى منصة أكثر جاهزية للاستخدام الميداني، مع حضور جوال مضبوط بالورديات، تحقق صوتي قابل للتدقيق، ولوحات متابعة للمشرفين، ودورة متابعة كاملة لحماية الأجور.

> **بعد الترقية | Post-upgrade:** شغّل `bench --site <your-site-name> migrate` ثم `bench build --app saudi_hr` و`bench --site <your-site-name> clear-cache`. وإذا كانت البيئة CPU-only أو تستخدم mirror خاص للحزم، احتفظ بملف `requirements-voice-cpu.txt` كخيار دعم تشغيلي.

### v1.13.0 — ١٧ أبريل ٢٠٢٦

**مرونة الرواتب والموافقات والواجهة الحية | Payroll Flexibility, Workflow Routing, and Live UX:**

| المكوّن | Component | التحديث |
|---------|-----------|----------|
| Saudi Monthly Payroll | مسير الرواتب الشهري | إضافة جدول `Payroll Adjustment Item` لاحتواء الزيادات والخصومات غير الثابتة لكل موظف داخل المسير نفسه مع إعادة احتساب صافي الراتب والإجماليات تلقائياً |
| Payroll APIs | واجهات الرواتب | إضافة helpers لاستيراد العمل الإضافي المعتمد إلى المسير وإضافة بنود تعديل يدوية برمجياً |
| Leave / Overtime / Salary Workflows | سير الموافقات | تفعيل مسار موظف ← مدير مباشر ← موارد بشرية لطلبات الإجازة السنوية والمرضية والعمل الإضافي وتعديل الراتب |
| Runtime Permissions | صلاحيات التشغيل | إضافة صلاحيات `Department Approver` وربطها بالصلاحيات الفعلية والاستعلامات الديناميكية مع مزامنة أدوار وصلاحيات الشركة للموافقين |
| Salary Adjustment | تعديل الراتب | جعل المستند submittable ومعالجة أخطاء المسار والحالات المفقودة حتى يعمل مع الـ workflow بدون tracebacks |
| WPS Export Report | تقرير تصدير WPS | إصلاح توليد بيانات WPS وملف SIF وتطبيع الشهر/تاريخ الدفع والهوية البنكية وتحويل فتح التقرير إلى Query Report صحيح |
| Saudi HR Workspace | مساحة العمل | إظهار قسم `سير الموافقات` داخل Workspace وربط `WPS Export Report` من الواجهة الحية إلى `/app/query-report/WPS Export Report` |

> **تعليق الإصدار | Release Note:** هذا الإصدار يرفع جاهزية التطبيق التشغيلية في بيئة العمل الحية عبر دعم التعديلات المتغيرة في الرواتب، وتثبيت مسارات الموافقات بين الموظف والمدير والموارد البشرية، وإصلاح نقطة الوصول لتقرير WPS من الواجهة نفسها.

> **بعد الترقية | Post-upgrade:** شغّل `bench --site <your-site-name> migrate` ثم `bench --site <your-site-name> clear-cache`، ويفضل `bench restart` إذا كانت بيئة الإنتاج تستخدم workers طويلة العمر.

### v1.12.0 — ١١ أبريل ٢٠٢٦

**تحصين رفع ملف الرواتب | Payroll Workbook Import Hardening:**

| المكوّن | Component | التحديث |
|---------|-----------|----------|
| Payroll Validation | التحقق قبل الاستيراد | منع الاستيراد عند غياب الأعمدة الإلزامية أو عند وجود تحذيرات حرجة مثل الأسماء المكررة بدون مركز تكلفة صريح |
| Upload Guidance | إرشادات الرفع | إضافة تعليمات ثابتة داخل نموذج المسير ورسالة مراجعة قبل تنفيذ الاستيراد |
| Workbook Analysis | تحليل الملف | إظهار التحذيرات الحرجة والصفوف الخطرة بوضوح قبل الاستيراد |
| Import Templates | قوالب الرفع | إضافة قالب رفع تفصيلي محصّن وقالب عربي مبسط مع تلوين للخانات الإلزامية وقوائم منسدلة وتحقق رقمي |
| Test Coverage | الاختبارات | توسيع اختبارات الانحدار لتغطية منع الأعمدة الناقصة، التحذيرات الحرجة، وتوليد القوالب الجديدة |

> **تعليق الإصدار | Release Note:** هذا الإصدار يجعل رفع ملفات الرواتب أكثر أمانًا ووضوحًا للمستخدم النهائي، ويمنع الاستيراد عندما تكون بيانات الملف قابلة لإحداث ربط خاطئ أو نتائج غير موثوقة.

### v1.8.0 — ٢ أبريل ٢٠٢٦

**تقوية الصلاحيات والمسارات الحرجة | Runtime Permission Hardening:**

| المكوّن | Component | التحديث |
|---------|-----------|----------|
| Mobile Attendance API | واجهات حضور الجوال | إزالة `ignore_permissions` من تسجيل الدخول/الخروج وطلبات الإجازة بالجوال، والاعتماد على صلاحيات Doctype صريحة |
| Compliance & Governance | الامتثال والحوكمة | إزالة تجاوزات الصلاحيات من إنشاء سجلات `HR Compliance Action Log`, `Policy Acknowledgement`, `Saudi Regulatory Task`, `Employee Warning Notice`, و`Disciplinary Decision Log` |
| Settings Import | إعدادات التطبيق | تشديد مزامنة دليل الفروع واستيراد القوالب مع تحقق صلاحيات صريح والتحقق من نوع/حجم ملفات Excel |

**الرواتب والامتثال المحاسبي | Payroll & Accounting Stability:**

| المكوّن | Component | التحديث |
|---------|-----------|----------|
| Saudi Monthly Payroll | مسير الرواتب | احتساب نسبي لخصم الإجازة المرضية عبر حدود الأشهر، منع الراتب الأساسي الصفري، وتسجيل ملاحظات تدقيق على الاستيراد وإنشاء الموظفين |
| Employee Loan | قروض الموظفين | حماية من خصم القسط نفسه من أكثر من مسير رواتب مع قفل منطقي قبل الخصم |
| Overtime / GOSI / Payroll JE | القيود المحاسبية | تحويل مسارات إنشاء القيود إلى صلاحيات صريحة بدل bypass داخلي |

**مكافأة نهاية الخدمة والإجازات | EOSB & Leave Rules:**

| المكوّن | Component | التحديث |
|---------|-----------|----------|
| End of Service Benefit | مكافأة نهاية الخدمة | توحيد منطق الحساب بين المستند والمعاينة والـ helpers، ورفض الخصومات السالبة أو الأعلى من المستحق |
| Saudi Annual Leave | الإجازة السنوية | منع الطلبات التي تمتد عبر سنتين أو تبدأ قبل تاريخ مباشرة الموظف |
| Leave Balance Helpers | مساعدات الإجازات | تحسين احتساب الأيام المأخوذة عند وجود تداخلات زمنية |

**الاختبارات والتبعيات | Tests & Dependencies:**

| المكوّن | Component | التحديث |
|---------|-----------|----------|
| Test Suite | حزمة الاختبارات | توسيع التغطية إلى 77 اختبارًا تشمل الجوال، الصلاحيات، الرواتب، الإجازات، و`EOSB` |
| Packaging | الحزم | التحقق من تطابق `pyproject.toml`, `setup.py`, و`requirements.txt` واستمرار الاعتماد على `openpyxl` و`openlocationcode` فقط |

> **تعليق الإصدار | Release Note:** هذا الإصدار يركز على تقوية التشغيل الفعلي والتدقيق والصلاحيات دون تغيير متطلبات التثبيت الأساسية للتطبيق.

### v1.7.0 — ١ أبريل ٢٠٢٦

**صيغة الطباعة الشاملة للموظف | Employee Complete File Print Format:**

| المكوّن | Component | التحديث |
|---------|-----------|----------|
| Print Format | صيغة طباعة | إضافة `Employee Complete File AR` — ملف شامل للموظف بتصميم احترافي (RTL/عربي، Jinja) |
| KPI Summary Bar | شريط المؤشرات | إجمالي الرواتب، أيام الإجازة، القروض، الرصيد المتبقي، العمل الإضافي في سطر واحد |
| Salary Cards | بطاقات الراتب | عرض آخر 4 أشهر كبطاقات بصرية مع تفاصيل الأساسي/الإجمالي/GOSI/الاستقطاعات |
| Loan Progress Bar | شريط تقدم القرض | شريط CSS يُظهر نسبة ومبلغ القسط المدفوع مقابل المتبقي لكل قرض |
| Empty States | حالات الفراغ | رسائل أنيقة عند غياب البيانات في أي قسم |
| Workspace Link | رابط مساحة العمل | إضافة رابط سريع من مساحة عمل Saudi HR للوصول لصيغة الطباعة |

---

### v1.6.0 — ٣١ مارس ٢٠٢٦

**الاختبارات الآلية | Automated Tests:**

| المكوّن | Component | التحديث |
|---------|-----------|----------|
| Unit Tests | اختبارات الوحدة | إضافة 12 اختبار منطقي لـ GOSI، القوالب الفارغة، صافي الراتب، وبحث الحسابات |

---

### v1.5.0 — ٢٧ مارس ٢٠٢٦

**الإصدار المستقل الكامل | Full Standalone Release:**

| المكوّن | Component | التحديث |
|---------|-----------|---------|
| Standalone Architecture | البنية المستقلة | إزالة الاعتماد التشغيلي على HRMS والإبقاء على التطبيق فوق `frappe` و`erpnext` فقط |
| README + Packaging | التوثيق والحزم | توثيق الاعتماديات الفعلية والتحقق منها، مع الحفاظ على تطابق `pyproject.toml` و`setup.py` و`requirements.txt` |

**توسعة دورة حياة الموظف | Employee Lifecycle Expansion:**

| المكوّن | Component | التحديث |
|---------|-----------|---------|
| Recruitment & Onboarding | التوظيف والتهيئة | إضافة `Hiring Requisition`, `Candidate Profile`, `Employee Onboarding` |
| Performance & Exit | الأداء وإنهاء الخدمة | إضافة `Performance Review`, `Exit Clearance` |
| Compliance & Governance | الامتثال والحوكمة | إضافة `Policy Acknowledgement`, `Saudi Regulatory Task`, `Employee Warning Notice`, `Disciplinary Decision Log` |

**القروض والخصومات | Employee Loans & Payroll Deductions:**

| المكوّن | Component | التحديث |
|---------|-----------|---------|
| Employee Loan | قروض الموظفين | إضافة القروض، جدول الأقساط، صرف القرض، واعتماد الصرف قبل القيد |
| Saudi Monthly Payroll | مسير الرواتب | ربط الخصم الشهري للقرض داخل الرواتب وتجميع خصومات القروض في المسير |
| Loan Reports & Print | التقارير والطباعة | إضافة `Outstanding Employee Loans`, `Loan Deduction Register`, `Monthly Loan Recovery Summary`, وصيغة `Employee Loan Agreement AR` |

**إصلاحات واستقرار | Stability Fixes:**

| الملف | التحديث |
|-------|---------|
| `annual_leave_disbursement.json` | إصلاح تعريفات `depends_on` غير الصالحة التي كانت تكسر واجهة النموذج |
| `install.py` + `employee_loan.py` | إضافة تسوية ما بعد الترحيل لسجلات القروض القديمة لتتوافق مع مسار الاعتماد الجديد |

### v1.4.2 — ٢٦ مارس ٢٠٢٦

**تحسينات مساحة العمل | Workspace Improvements:**

| الملف | التحديث |
|-------|---------|
| `saudi_hr/workspace/saudi_hr/saudi_hr.json` | إضافة اختصار مباشر `Mobile Attendance / حضور الجوال` داخل مساحة عمل Saudi HR لفتح صفحة `/mobile-attendance` من Desk |

---

### v1.4.1 — ٢٥ مارس ٢٠٢٦

**تحسين مساحة العمل والتكامل مع الترجمة | Workspace & Translation Integration:**

| الملف | التحديث |
|-------|---------|
| `saudi_hr/workspace/saudi_hr/saudi_hr.json` | إضافة مساحة عمل عامة لتطبيق Saudi HR حتى يظهر `/app/saudi-hr` داخل Desk بدل صفحة Not Found |
| `saudi_hr/workspace/saudi_hr/saudi_hr.json` | توسيع مساحة العمل بأقسام مختصرة وروابط تشغيلية وتقارير وshortcuts مناسبة للاستخدام اليومي |
| Desk Integration | تحسين جاهزية التطبيق للعمل مع ترجمة `arabic_pro` داخل الواجهة دون فقدان مدخل التطبيق |

---

### v1.4.0 — ٢٥ مارس ٢٠٢٦

**تجربة الجوال والحضور الذكي | Mobile Attendance & Smart Check-in:**

| المكوّن | Component | التحديث |
|---------|-----------|---------|
| ★ Mobile Attendance PWA | تطبيق حضور الجوال | صفحة حضور مستقلة تعمل كتجربة PWA مع بوابة تثبيت وصلاحيات الموقع والإشعارات |
| ★ Mobile Self Service API | واجهات الخدمة الذاتية | واجهات للحضور والانصراف، إحصائيات الحضور، طلبات الإجازة، والمواقع المتاحة |
| ★ Face / Voice Verification | التحقق بالصورة والصوت | دعم مرفقات صورة الوجه والتسجيل الصوتي مع كل حركة حضور |
| ★ Runtime Language Switching | تبديل اللغة وقت التشغيل | عرض الصفحة بالإنجليزية عندما تكون جلسة النظام باللغة الإنجليزية |

**إدارة الفروع ورفع الموظفين | Branch Directory & Bulk Import:**

| المكوّن | Component | التحديث |
|---------|-----------|---------|
| ★ Saudi HR Settings | إعدادات الموارد البشرية | إضافة دليل الموظفين والفروع داخل صفحة الإعدادات |
| ★ Branch Employee Directory Row | جدول الموظفين والفروع | Child DocType جديد لعرض الموظف وفرعه وإدارته وشركته |
| ★ Employee Branch Template | قالب رفع جماعي | تنزيل قالب Excel/HTML ورفع أسماء الموظفين وفروعهم دفعة واحدة |

**تحسينات الامتثال والتجهيز للنقل | Compliance & Packaging Improvements:**

| الملف | التحديث |
|-------|---------|
| `special_leave.py/js/json` | تصحيح إجازة الحج والزواج وربط الأهلية بمدة الخدمة والاستخدام لمرة واحدة |
| `tasks.py` + `hooks.py` | إضافة دورة تنبيه GOSI الشهرية وربطها بالمجدول |
| `pyproject.toml` + `setup.py` + `requirements.txt` | إعلان التبعيات التشغيلية الجديدة: `openpyxl` و`openlocationcode` |
| `README.md` | إضافة خطوات نقل التطبيق إلى نظام آخر والتحقق من التبعيات بعد التثبيت |

**اختبارات مضافة | Added Tests:**
- تغطية لاستخراج أنواع الإجازة السنوية المدعومة وحساب الأيام المستهلكة
- تغطية لأهلية إجازة الحج
- تغطية لمصفوفة التغطية القانونية
- تغطية لبناء قالب فروع الموظفين في الإعدادات

---

### v1.3.1 — ٢٢ مارس ٢٠٢٦

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

See [LICENSE](LICENSE) for details.

---

<div align="center">

**صُنع بـ ❤️ للمملكة العربية السعودية | Made with ❤️ for Saudi Arabia 🇸🇦**

© 2026 [IdeaOrbit](https://ideaorbit.net)

</div>
