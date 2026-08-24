<div align="center" dir="rtl">

<a href="https://ahmadmdm.github.io/hr-saudi-arabia-erpnext/">
  <img src="docs/images/readme-hero.svg" alt="Saudi HR — الموظف رحلة، لا سجل" width="100%">
</a>

<br>

[![Version](https://img.shields.io/badge/version-1.19.2-49D5A2?style=flat-square&labelColor=06161C)](https://github.com/ahmadmdm/hr-saudi-arabia-erpnext/releases/tag/v1.19.2-v16)
![ERPNext](https://img.shields.io/badge/ERPNext-v16-DFA96A?style=flat-square&labelColor=06161C)
![Arabic first](https://img.shields.io/badge/Arabic-first-E9E2D0?style=flat-square&labelColor=06161C)
![HRMS](https://img.shields.io/badge/HRMS-not_required-49D5A2?style=flat-square&labelColor=06161C)
[![Quality](https://img.shields.io/github/actions/workflow/status/ahmadmdm/hr-saudi-arabia-erpnext/quality.yml?branch=version-16&style=flat-square&label=quality&labelColor=06161C)](https://github.com/ahmadmdm/hr-saudi-arabia-erpnext/actions/workflows/quality.yml)

### نظام تشغيل دورة الموظف السعودية داخل ERPNext

**[ادخل التجربة التفاعلية](https://ahmadmdm.github.io/hr-saudi-arabia-erpnext/)** &nbsp;·&nbsp; [ثبّت الآن](#التثبيت) &nbsp;·&nbsp; [اكتشف الرحلة](#مدار-الموظف) &nbsp;·&nbsp; [تواصل](#صاحب-المشروع)

</div>

---

## الموظف ليس صفًا في جدول

هو عقد يؤثر في الراتب، وحضور يؤثر في الاستحقاق، وإجازة لها سياسة، ووثيقة لها موعد، وقرار يجب أن يبقى قابلًا للتفسير.

**Saudi HR** يربط هذه الرحلة داخل ERPNext في ملف واحد وطبقة تشغيل عربية مستقلة عن HRMS. النتيجة ليست مزيدًا من النماذج؛ بل حقيقة تشغيلية واحدة يعرف منها الفريق: ماذا حدث؟ لماذا؟ ومن يملك الخطوة التالية؟

> [!IMPORTANT]
> التطبيق أداة تشغيل وامتثال مبنية على متطلبات العمل السعودي، وليس بديلًا عن الاستشارة القانونية للحالات الخاصة.

## مدار الموظف

```text
                              ┌──────── العقد ────────┐
                       الحضور │                       │ الامتثال
                              │   ملف موظف شامل      │
                       الإجازة│  هوية · عمل · أثر    │ الراتب
                              └──────── الخروج ───────┘
```

| المحطة | ما يربطه النظام | ما يتركه للمراجعة |
|:--|:--|:--|
| **التوظيف والعقد** | الطلب، المرشح، التقييم، العرض، العقد والتجربة | قرار موثق وبداية محددة |
| **التشغيل اليومي** | الوردية، الموقع، الحضور، الغياب والإجازات المخصصة | حركة واستحقاق قابلان للتفسير |
| **الراتب والالتزامات** | المسير، التسويات، القروض، GOSI، WPS ونطاقات | حساب ومخرج نظامي قابلان للمراجعة |
| **العلاقات والامتثال** | السياسات، الإقرارات، التحقيقات، التظلمات والتفتيش | مسؤول وموعد ودليل إغلاق |
| **الخروج** | الإنهاء، الإخلاء، المقابلة، EOSB والمخالصة | نهاية خدمة بلا فجوات |

## شاهد النظام وهو يعمل

<a href="https://ahmadmdm.github.io/hr-saudi-arabia-erpnext/#journey">
  <img src="docs/images/professional-hr-hub-desktop.png" alt="مركز التشغيل الاحترافي في Saudi HR" width="100%">
</a>

<p align="center" dir="rtl"><sub>مركز التشغيل الفعلي: الأولويات اليومية والملف الشامل والامتثال في منظور واحد.</sub></p>

## التثبيت

هذه الحزمة مخصصة لـ **ERPNext v16**. الحزمة المختبرة: Saudi HR `1.19.2` — الإصدار `v1.19.2-v16`.

```bash
cd ~/frappe-bench
bench get-app --branch version-16 https://github.com/ahmadmdm/hr-saudi-arabia-erpnext.git
bench --site your-site.local install-app saudi_hr
bench --site your-site.local migrate
bench build --app saudi_hr
bench restart
```

ثم ابدأ من:

```text
/app/saudi-hr                مساحة العمل
/app/professional-hr-hub     مركز التشغيل
/app/attendance-action-hub   إجراءات الحضور
/mobile-attendance           حضور الجوال
```

> [!TIP]
> تستخدم ERPNext v15؟ انتقل إلى [فرع version-15](https://github.com/ahmadmdm/hr-saudi-arabia-erpnext/tree/version-15)، أو اختر إصدارك داخل [التوتريال التفاعلي](https://ahmadmdm.github.io/hr-saudi-arabia-erpnext/#install).

## أول دورة حقيقية

1. **ابنِ الهيكل:** الشركة، الفروع، الأقسام، الوظائف، المواقع والصلاحيات.
2. **عرّف السياسات:** الورديات والإجازات والعقود وتنبيهات الوثائق.
3. **أضف موظفًا تجريبيًا:** أكمل هويته وعقده ووثائقه وراتبه.
4. **شغّل يومًا فعليًا:** حضور ثم طلب إجازة وموافقة ثم راتب تجريبي.
5. **أغلق الدورة:** راجع التقارير والتنبيهات والمخرجات ثم اختبر النسخ الاحتياطي.

ابدأ المسار الموجه حسب دورك من **[دليل التشغيل الحي](https://ahmadmdm.github.io/hr-saudi-arabia-erpnext/#tutorial)**.

## التوثيق الذي تحتاجه عند الحاجة

- [التثبيت](docs/installation.md) — المتطلبات والخطوات والتحقق.
- [النشر](docs/deployment.md) — المسارات والصلاحيات والجاهزية.
- [تخصيص الإجازات](docs/leave-policy-customization.md) — سياسة عامة أو قسم أو موظف.
- [البيانات التجريبية](docs/demo-data.md) — دورة آمنة قبل الإنتاج.
- [مصفوفة الامتثال](docs/LEGAL_COMPLIANCE_MATRIX.md) — من المتطلب إلى الوظيفة والدليل.
- [خطة الاختبار](docs/COMPREHENSIVE_TEST_PLAN.md) و[النتائج](docs/COMPREHENSIVE_TEST_RESULTS.md).
- [التعافي من الكوارث](docs/DISASTER_RECOVERY.md) و[عقد التبعيات](DEPENDENCIES.md).

## حدود واضحة

- الربط الحي مع قوى وGOSI ومدد ومقيم يحتاج بيانات اعتماد وقنوات معتمدة من الجهات.
- المخرجات الحكومية تُجهّز وتُراجع داخل النظام قبل الإرسال.
- بيانات الرواتب والملف الشامل محكومة بصلاحيات على مستوى المستند والسجل.
- المهام المجدولة تراقب العقود والإقامات والتصاريح والمهل النظامية.

## المساهمة والجودة

```bash
python scripts/validate_quality.py
ruff check saudi_hr --select F
pytest -q
git diff --check
```

أرسل المشكلة مع الإصدار، خطوات الإعادة، النتيجة المتوقعة ودليل مرئي إن وجد عبر [GitHub Issues](https://github.com/ahmadmdm/hr-saudi-arabia-erpnext/issues).

## صاحب المشروع

<div dir="rtl">

**ahmad**<br>
صاحب المشروع والمشرف على تجربة الموارد البشرية السعودية.<br>
[ahmad8@outlook.com](mailto:ahmad8@outlook.com)

</div>
---

<div align="center" dir="rtl">

**العقد يعرف الراتب · الحضور يعرف الاستحقاق · الامتثال يعرف الموعد**

[التجربة التفاعلية](https://ahmadmdm.github.io/hr-saudi-arabia-erpnext/) · [الإصدارات](https://github.com/ahmadmdm/hr-saudi-arabia-erpnext/releases) · [GPL-3.0](LICENSE)

</div>
