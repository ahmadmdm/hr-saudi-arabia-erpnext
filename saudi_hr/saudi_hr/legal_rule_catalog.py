"""Versioned Saudi Labor Executive Regulations catalog used by operations and tests."""

import frappe


CATALOG_VERSION = "2026.07-executive-regulations-v1"
SOURCE_DOCUMENT = "اللائحة التنفيذية لنظام العمل وملحقاتها.pdf"


def _rule(rule_id, page, topic_ar, obligation_ar, control, verification, risk="High / مرتفع", lifecycle="Strategy & Setup", category="Policy / سياسة"):
	return {
		"rule_id": rule_id,
		"source_pdf_page": page,
		"source_printed_page": max(1, page - 1),
		"reference_topic": topic_ar,
		"article_number": f"Executive Regulations PDF p.{page}",
		"obligation_summary": obligation_ar,
		"evidence_requirement": control,
		"verification_reference": verification,
		"risk_level": risk,
		"lifecycle_stage": lifecycle,
		"task_category": category,
		"automation_level": "Automated / آلي" if verification.startswith("test:") else "Guided Review / مراجعة موجّهة",
	}


LEGAL_RULES = [
	_rule("SHR-REG-015", 4, "بلاغ بيانات المنشأة", "إبلاغ مكتب العمل ببيانات المنشأة عند بدء العمل، وتحديث التغييرات خلال عشرة أيام.", "Ministry Filing Tracker", "test: Ministry Filing Tracker", lifecycle="Strategy & Setup", category="Alert / تنبيه"),
	_rule("SHR-REG-017", 4, "السجلات النظامية", "الاحتفاظ بسجلات العمال والأجور والغرامات والحضور والتدريب والفحوص والملفات العمالية.", "Statutory HR Records Register", "review: statutory records completeness", lifecycle="Reports & Analytics", category="Document / مستند"),
	_rule("SHR-REG-028", 6, "توظيف ذوي الإعاقة", "على المنشأة التي تستخدم خمسة وعشرين عاملاً فأكثر تشغيل 4% على الأقل من المؤهلين مهنياً من ذوي الإعاقة متى توافرت الأعمال المناسبة.", "Disability Employment Compliance", "test: Disability Employment Compliance", lifecycle="Onboarding & Employment"),
	_rule("SHR-REG-024", 19, "الإجازة دون أجر", "إذا تجاوزت الإجازة دون أجر عشرين يوماً توقف عقد العمل ما لم يتفق الطرفان على خلاف ذلك.", "Leave controls and legal review", "test: unpaid leave duration", lifecycle="Time, Leave & Payroll", category="Calculation / حسبة"),
	_rule("SHR-REG-025", 19, "العمل لبعض الوقت", "يكون عقد العمل لبعض الوقت مكتوباً ومحدد المدة وتقل ساعاته اليومية عن نصف ساعات المنشأة.", "Work Arrangement Control", "test: part-time eligibility", lifecycle="Onboarding & Employment"),
	_rule("SHR-REG-026", 19, "الإجازة المرضية", "خلال سنة من أول إجازة مرضية: ثلاثون يوماً بأجر كامل، وستون يوماً بثلاثة أرباع الأجر، وثلاثون يوماً دون أجر.", "Saudi Sick Leave", "test: sick leave tiers", lifecycle="Time, Leave & Payroll", category="Calculation / حسبة"),
	_rule("SHR-REG-041", 34, "دورة استحقاق الإجازة المرضية", "تحتسب شرائح الإجازة المرضية خلال سنة تبدأ من تاريخ أول إجازة مرضية، لا بحسب السنة التقويمية.", "Saudi Sick Leave", "test: rolling sick-leave benefit cycle", lifecycle="Time, Leave & Payroll", category="Calculation / حسبة"),
	_rule("SHR-REG-027", 20, "العمل المرن", "العمل المرن للسعوديين، موثق إلكترونياً، مدفوع بالساعة، ويبدأ إضافيه بعد 95 ساعة ولا يتجاوز 160 ساعة شهرياً.", "Work Arrangement Control", "test: 95 and 160 flexible-work boundaries", lifecycle="Time, Leave & Payroll", category="Calculation / حسبة"),
	_rule("SHR-REG-027-B", 20, "استحقاقات العمل المرن", "لا يستحق العامل المرن إجازة مدفوعة أو مكافأة نهاية خدمة أو فترة تجربة، وتحتسب له نقطة نطاقات عند 160 ساعة.", "Work Arrangement Control", "test: flexible entitlements and Nitaqat credit", lifecycle="Time, Leave & Payroll", category="Calculation / حسبة"),
	_rule("SHR-REG-027-C", 20, "مدة عقد العمل المرن", "لا تتجاوز مدة عقد العمل المرن سنة، ويتطلب تمديده أو تجديده موافقة العامل أو التحول إلى عقد عادي.", "Work Arrangement Control", "test: flexible contract duration and consent", lifecycle="Onboarding & Employment"),
	_rule("SHR-REG-031", 22, "فترات الرضاعة", "لا يتجاوز مجموع فترات إرضاع المولود ساعة مدفوعة يومياً لمدة أربعة وعشرين شهراً وتحسب من ساعات العمل.", "Maternity Paternity Leave", "test: nursing break limits", lifecycle="Time, Leave & Payroll", category="Calculation / حسبة"),
	_rule("SHR-REG-038", 24, "الاعتراض على العقوبات", "يجوز الاعتراض على قرار عقوبات مخالفات العمل خلال ستين يوماً من التبليغ.", "Inspection Fine SLA", "test: fine objection deadline", lifecycle="Employee Relations & Legal", category="Alert / تنبيه"),
	_rule("SHR-REG-039", 25, "إزالة المخالفة", "تزال المخالفة خلال عشرة أيام عمل من تاريخ إيقاع العقوبة، وإلا عدت متكررة وضوعفت العقوبة.", "Labor Inspection and Inspection Fine SLA", "test: violation remediation deadline", lifecycle="Employee Relations & Legal", category="Alert / تنبيه"),
	_rule("SHR-REG-PROB", 30, "فترة التجربة", "ينص على التجربة صراحة ولا تتجاوز 180 يوماً، ولا تدخل أعياد الفطر والأضحى واليوم الوطني ويوم التأسيس والإجازة المرضية في حسابها.", "Saudi Employment Contract", "test: probation duration and excluded days", lifecycle="Onboarding & Employment", category="Calculation / حسبة"),
	_rule("SHR-REG-039-L", 34, "تداخل الإجازات الرسمية", "تعالج تداخلات الإجازات الرسمية مع الراحة الأسبوعية والإجازة السنوية والمرضية وفق القواعد المحددة.", "Holiday Leave Overlap Rule", "test: Holiday Leave Overlap Rule", lifecycle="Time, Leave & Payroll", category="Calculation / حسبة"),
	_rule("SHR-REG-040", 34, "إجازات المناسبات", "تمنح إجازات الزواج والمولود والوفاة بالمدد المحددة مع مستنداتها المؤيدة.", "Special Leave", "test: special leave entitlements", lifecycle="Time, Leave & Payroll", category="Calculation / حسبة"),
	_rule("SHR-REG-067", 39, "تقادم الجزاء التأديبي", "لا يجوز توقيع جزاء إذا مضى على ثبوت المخالفة أكثر من ثلاثين يوماً.", "Disciplinary Procedure", "test: disciplinary limitation", lifecycle="Employee Relations & Legal", category="Workflow / إجراء"),
	_rule("SHR-REG-068", 39, "تبليغ الجزاء", "يبلغ العامل كتابة بالجزاء ومقداره وأثر التكرار بطريقة قابلة للإثبات.", "Disciplinary Procedure", "test: disciplinary notice evidence", lifecycle="Employee Relations & Legal", category="Document / مستند"),
	_rule("SHR-REG-071", 39, "التظلم", "يقدم التظلم خلال ثلاثين يوماً، ويبت فيه خلال خمسة عشر يوماً، مع حفظ حق الاعتراض القضائي.", "Employee Grievance", "test: grievance SLA", lifecycle="Employee Relations & Legal", category="Workflow / إجراء"),
	_rule("SHR-REG-MAT", 36, "إجازة الوضع", "إجازة الوضع اثنا عشر أسبوعاً بأجر كامل، تبدأ قبل الوضع بأربعة أسابيع كحد أقصى مع حفظ ستة أسابيع بعده.", "Maternity Paternity Leave", "test: maternity 84-day allocation", lifecycle="Time, Leave & Payroll", category="Calculation / حسبة"),
	_rule("SHR-REG-MAT-C", 36, "رعاية الطفل المريض أو ذي الإعاقة", "شهر إضافي بأجر كامل ثم شهر إضافي دون أجر عند حاجة الطفل للرعاية المستمرة.", "Maternity Paternity Leave", "test: child-care maternity extension", lifecycle="Time, Leave & Payroll", category="Calculation / حسبة"),
	_rule("SHR-REG-OT-720", 17, "الحد السنوي للعمل الإضافي", "لا يتجاوز العمل الإضافي 720 ساعة سنوياً، ويجوز التجاوز بموافقة العامل.", "Overtime Request", "test: annual overtime boundary", risk="Critical / حرج", lifecycle="Time, Leave & Payroll", category="Calculation / حسبة"),
	_rule("SHR-REG-OT-PAY", 17, "أجر العمل الإضافي", "أجر ساعة الإضافي يساوي أجر الساعة الفعلي مضافاً إليه 50% من أجر الساعة الأساسي.", "Overtime Request", "test: Article 107 overtime formula", risk="Critical / حرج", lifecycle="Time, Leave & Payroll", category="Calculation / حسبة"),
	_rule("SHR-REG-OT-LEAVE", 17, "الإجازة التعويضية", "تتطلب موافقة العامل، ولا تقل عن 1.5 ساعة لكل ساعة إضافية، وتستخدم عادة خلال 60 يوماً، ولا تتجاوز 30 يوماً سنوياً إلا باتفاق.", "Overtime Request", "test: compensatory leave factor deadline and cap", risk="Critical / حرج", lifecycle="Time, Leave & Payroll", category="Calculation / حسبة"),
	_rule("SHR-REG-OT-EXIT", 17, "تعويض رصيد الإجازة التعويضية عند المغادرة", "يعوض العامل مادياً عن رصيد الإجازة التعويضية غير المستخدم عند انتهاء العلاقة وفق أجره الفعلي.", "Final Settlement SLA", "test: unused compensatory leave exit payout", risk="Critical / حرج", lifecycle="Separation & Offboarding", category="Calculation / حسبة"),
	_rule("SHR-REG-EXIT-7", 86, "التسوية عند إنهاء صاحب العمل", "تصفى أجور العامل وحقوقه وترد وثائقه خلال أسبوع عند إنهاء صاحب العمل.", "Final Settlement SLA", "test: employer settlement and document return", risk="Critical / حرج", lifecycle="Separation & Offboarding", category="Alert / تنبيه"),
	_rule("SHR-REG-EXIT-14", 86, "التسوية عند إنهاء العامل", "تصفى الأجور والحقوق وترد الوثائق خلال أسبوعين عند إنهاء العامل للعقد.", "Final Settlement SLA", "test: employee settlement and document return", risk="Critical / حرج", lifecycle="Separation & Offboarding", category="Alert / تنبيه"),
	_rule("SHR-REG-TEMP-90", 3, "تحول العمل المؤقت أو العرضي", "إذا استمر العمل المؤقت أو العرضي أكثر من تسعين يوماً تحول العقد إلى عقد عمل عادي.", "Work Arrangement Control", "test: temporary work 90-day boundary", lifecycle="Onboarding & Employment", category="Workflow / إجراء"),
	_rule("SHR-REG-011", 7, "المهن المقصورة على السعوديين", "لا يجوز توظيف غير السعودي في ثماني عشرة مهنة محددة، ولا إسناد مهامها إليه بطريقة مباشرة أو غير مباشرة تحت أي مسمى وظيفي آخر.", "Saudi Only Profession and Expat Work Authorization Control", "test: restricted occupation detection", risk="Critical / حرج", lifecycle="Onboarding & Employment", category="Workflow / إجراء"),
	_rule("SHR-REG-029", 21, "خزانة الإسعافات الطبية", "إعداد خزانة إسعافات في مكان العمل تحتوي على الأصناف والكميات المحددة نظاماً، صالحة للاستعمال باستمرار، مع تعويض النقص، وحفظها في ظروف صحية، وتمييزها بهلال أحمر على خلفية بيضاء، وإعلان مكانها واسم المسؤول عنها.", "First Aid Cabinet Register", "test: first aid cabinet contents and signage", risk="Critical / حرج", lifecycle="Strategy & Setup", category="Document / مستند"),
	_rule("SHR-REG-023-A", 18, "الأعمال التجهيزية والتكميلية", "لا يتجاوز مجموع وقت الأعمال التجهيزية والتكميلية ثلاثين دقيقة تضاف إلى ساعات العمل، بحد أقصى خمس عشرة دقيقة لكل منهما.", "Working Time Compliance Check", "test: preparatory and complementary minute caps", lifecycle="Time, Leave & Payroll", category="Calculation / حسبة"),
	_rule("SHR-REG-023-B", 18, "العمل المتقطع بالضرورة", "تحدد ساعات العمل الفعلية بعشر ساعات يومياً تخفض إلى ثمان في رمضان، بما لا يتجاوز 48 ساعة أسبوعياً و36 في رمضان للمسلمين، مع راحة متواصلة لا تقل عن عشر ساعات خلال كل أربع وعشرين ساعة، وتمكين العمال من أداء الصلوات.", "Working Time Compliance Check", "test: intermittent work limits and rest", risk="Critical / حرج", lifecycle="Time, Leave & Payroll", category="Calculation / حسبة"),
	_rule("SHR-REG-023-C", 18, "عمال الحراسة والنظافة", "تحدد ساعات العمل الفعلية باثنتي عشرة ساعة يومياً تخفض إلى عشر في رمضان، ولا يشمل التعريف الحراسات الأمنية المدنية والصناعية، ولا يقتضي عمل النظافة الاستمرار أكثر من ست ساعات متوالية.", "Working Time Compliance Check", "test: guarding and cleaning limits", risk="Critical / حرج", lifecycle="Time, Leave & Payroll", category="Calculation / حسبة"),
	_rule("SHR-REG-032", 23, "الأعمال المحظورة على الأحداث", "يحظر تشغيل من أتم الخامسة عشرة ولم يبلغ الثامنة عشرة في المناجم والمحاجر والاستخراج تحت الأرض، والصناعات ذات المخاطر الصحية، والأعمال الشاقة، والآلات ذات المخاطر العالية، وأي عمل يعرضه لمشكلات أخلاقية أو نفسية أو جسدية.", "Juvenile Prohibited Work and Special Employment Category Control", "test: juvenile prohibited work detection", risk="Critical / حرج", lifecycle="Onboarding & Employment", category="Workflow / إجراء"),
	_rule("SHR-REG-033", 23, "الحد الأدنى لسن التشغيل", "لا يجوز بأي حال تشغيل من لم يتم الخامسة عشرة من عمره، عدا حالات التعليم والتدريب المنصوص عليها في المادة (167) من النظام.", "Special Employment Category Control", "test: minimum employment age", risk="Critical / حرج", lifecycle="Onboarding & Employment", category="Alert / تنبيه"),
	_rule("SHR-REG-035", 24, "شروط استثناء التعليم والتدريب", "لا يسري استثناء عمل الأطفال والأحداث لأغراض التعليم والتدريب إلا بإشراف مباشر من الجهة المسؤولة، وبأسلوب تدريب متدرج، ودون إعاقة التحصيل الدراسي، وألا يكون من الأعمال الخطرة، وبموافقة الوزارة والجهة المرخِّصة للنشاط.", "Special Employment Category Control", "test: Article 35 exception conditions", risk="Critical / حرج", lifecycle="Onboarding & Employment", category="Workflow / إجراء"),
	_rule("SHR-REG-034", 23, "تشغيل الأحداث ليلاً", "يحظر تشغيل الأحداث أثناء فترة من الليل لا تقل عن اثنتي عشرة ساعة متتالية، ويستثنى العمل في منشآت الأسرة والمدارس المهنية ومراكز التدريب والمخابز خارج الفترة من التاسعة مساءً حتى الرابعة صباحاً وحالات القوة القاهرة والطوارئ.", "Special Employment Category Control", "test: juvenile night work exceptions", risk="Critical / حرج", lifecycle="Time, Leave & Payroll", category="Workflow / إجراء"),
	_rule("SHR-REG-030", 22, "الأماكن البعيدة عن العمران", "تعد بعيدة عن العمران المواقع التي تبتعد أكثر من خمسين كيلومتراً بطريق معبد أو خمسة وعشرين بطريق غير معبد، أو التجمعات التي تنقصها المرافق، ويلتزم صاحب العمل على نفقته بالحوانيت ووسائل الترفيه والترتيبات الطبية للعمال وأسرهم والمدارس والمساجد وبرامج محو الأمية.", "Remote Work Site Compliance", "test: remote area thresholds and six obligations", lifecycle="Strategy & Setup", category="Policy / سياسة"),
]


def validate_catalog():
	ids = [rule["rule_id"] for rule in LEGAL_RULES]
	if len(ids) != len(set(ids)):
		raise ValueError("Duplicate legal rule identifiers found.")
	for rule in LEGAL_RULES:
		for fieldname in ("rule_id", "source_pdf_page", "reference_topic", "obligation_summary", "evidence_requirement", "verification_reference"):
			if not rule.get(fieldname):
				raise ValueError(f"{rule['rule_id']} is missing {fieldname}.")
	return True


@frappe.whitelist()
def get_legal_rule_catalog():
	validate_catalog()
	return {"version": CATALOG_VERSION, "source_document": SOURCE_DOCUMENT, "rules": LEGAL_RULES, "count": len(LEGAL_RULES)}


def sync_legal_rule_catalog(company=None):
	"""Idempotently publish the catalog for one company or every configured company."""
	validate_catalog()
	companies = [company] if company else frappe.get_all("Company", pluck="name", order_by="creation asc")
	if not companies or not frappe.db.exists("DocType", "Legal Reference Matrix"):
		return {"company": company, "companies": companies, "created": 0, "updated": 0, "skipped": len(LEGAL_RULES) * max(1, len(companies))}

	created = updated = 0
	for company_name in companies:
		for rule in LEGAL_RULES:
			values = {
				**rule,
				"law_name": "Saudi Labor Law Executive Regulations / اللائحة التنفيذية لنظام العمل",
				"company": company_name,
				"status": "Active / ساري",
				"source_document_version": CATALOG_VERSION,
				"required_control": 1,
			}
			name = frappe.db.exists("Legal Reference Matrix", {"company": company_name, "rule_id": rule["rule_id"]})
			if name:
				doc = frappe.get_doc("Legal Reference Matrix", name)
				doc.update(values)
				doc.save(ignore_permissions=True)
				updated += 1
			else:
				frappe.get_doc({"doctype": "Legal Reference Matrix", **values}).insert(ignore_permissions=True)
				created += 1
	return {
		"company": company if company else None,
		"companies": companies,
		"created": created,
		"updated": updated,
		"skipped": 0,
	}
