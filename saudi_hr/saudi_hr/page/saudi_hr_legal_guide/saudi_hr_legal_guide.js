frappe.provide("saudi_hr");

frappe.pages["saudi-hr-legal-guide"].on_page_load = function (wrapper) {
	new saudi_hr.LegalGuide(wrapper);
};

saudi_hr.LegalGuide = class LegalGuide {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.data = null;
		this.query = "";
		this.timer = null;
		this.page = frappe.ui.make_app_page({ parent: wrapper, title: "الدليل النظامي للموارد البشرية", single_column: true });
		this.ensureStyles();
		this.page.set_primary_action("بحث", () => this.search(this.page.body.find("[data-search]").val() || ""), "search");
		if ((frappe.user_roles || []).some((role) => ["HR Manager", "HR User", "System Manager"].includes(role))) this.page.add_menu_item("مركز العمليات المؤسسي", () => this.open("/app/saudi-enterprise-center"));
		this.renderLoading();
		this.search("");
	}

	esc(value) { return frappe.utils.escape_html(String(value ?? "")); }

	ensureStyles() {
		if (document.getElementById("saudi-legal-guide-style")) return;
		const style = document.createElement("style");
		style.id = "saudi-legal-guide-style";
		style.textContent = `
			.saudi-legal { --green:#0b5d4b; --ink:#13251f; --paper:#f3f0e7; --sand:#d6c7a1; --line:#dce2de; --muted:#5c6b65; --clay:#b54432; display:grid; gap:15px; padding:8px 0 32px; color:var(--ink); font-family:"Noto Sans Arabic","Tajawal",var(--font-stack); text-align:right; }
			.saudi-legal *, .saudi-legal *::before, .saudi-legal *::after { box-sizing:border-box; }
			.saudi-legal button, .saudi-legal input { font:inherit; }
			.saudi-legal__hero { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:20px; align-items:end; padding:25px; background:var(--paper); border:1px solid #ddd8c8; border-radius:14px; }
			.saudi-legal__eyebrow { margin:0 0 6px; color:var(--green); font-size:11px; font-weight:900; }
			.saudi-legal__hero h1 { margin:0; font-family:"Noto Kufi Arabic","Noto Sans Arabic",sans-serif; font-size:clamp(23px,3vw,33px); line-height:1.5; }
			.saudi-legal__hero p { max-width:760px; margin:8px 0 0; color:var(--muted); font-size:13px; line-height:1.9; }
			.saudi-legal__folio { min-width:154px; padding:14px; color:#fff; background:var(--ink); border-radius:10px; }
			.saudi-legal__folio strong { display:block; font-size:18px; }
			.saudi-legal__folio span { color:#d4dfda; font-size:10px; }
			.saudi-legal__search { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:9px; padding:10px; background:#fff; border:1px solid var(--line); border-radius:12px; box-shadow:0 8px 25px rgba(19,37,31,.06); }
			.saudi-legal__search input { min-height:46px; padding:9px 13px; border:1px solid #cbd5d0; border-radius:8px; background:#fafcfb; }
			.saudi-legal__search button { min-height:46px; padding:9px 19px; color:#fff; background:var(--green); border:0; border-radius:8px; font-weight:800; cursor:pointer; }
			.saudi-legal button:focus-visible, .saudi-legal input:focus-visible { outline:3px solid #38bdf8; outline-offset:3px; }
			.saudi-legal__topics { display:flex; flex-wrap:wrap; gap:7px; }
			.saudi-legal__topic { min-height:44px; padding:8px 12px; color:var(--green); background:#fff; border:1px solid #bfd1c9; border-radius:999px; cursor:pointer; }
			.saudi-legal__topic:hover { color:#fff; background:var(--green); }
			.saudi-legal__layout { display:grid; grid-template-columns:minmax(0,1.5fr) minmax(285px,.6fr); gap:15px; align-items:start; }
			.saudi-legal__results { display:grid; gap:10px; }
			.saudi-legal__result { position:relative; overflow:hidden; padding:18px 20px 17px; background:#fff; border:1px solid var(--line); border-radius:12px; }
			.saudi-legal__result::before { content:""; position:absolute; inset:0 0 0 auto; width:4px; background:var(--green); }
			.saudi-legal__result[data-risk="critical"]::before { background:var(--clay); }
			.saudi-legal__result-head { display:flex; justify-content:space-between; gap:12px; align-items:start; }
			.saudi-legal__result h2 { margin:0; font-size:16px; line-height:1.6; }
			.saudi-legal__rule { direction:ltr; display:inline-flex; padding:4px 8px; color:#41534c; background:#eef2f0; border-radius:6px; font-family:ui-monospace,monospace; font-size:10px; white-space:nowrap; }
			.saudi-legal__guidance { margin:10px 0; color:#2d4038; font-size:13px; line-height:1.9; }
			.saudi-legal__control { padding:10px 12px; color:#345047; background:#f1f7f4; border-right:3px solid #91b6a6; border-radius:7px; font-size:11px; line-height:1.7; }
			.saudi-legal__citation { display:flex; flex-wrap:wrap; gap:8px 14px; margin-top:12px; padding-top:10px; color:var(--muted); border-top:1px solid #edf0ee; font-size:10px; }
			.saudi-legal__citation b { color:var(--ink); }
			.saudi-legal__side { display:grid; gap:12px; position:sticky; top:78px; }
			.saudi-legal__panel { padding:17px; background:#fff; border:1px solid var(--line); border-radius:12px; }
			.saudi-legal__panel h2 { margin:0 0 7px; font-size:15px; }
			.saudi-legal__panel p { margin:0 0 12px; color:var(--muted); font-size:11px; line-height:1.8; }
			.saudi-legal__drafts { display:grid; gap:7px; }
			.saudi-legal__draft { min-height:44px; padding:8px 11px; color:var(--ink); text-align:right; background:var(--paper); border:1px solid #ddd8c8; border-radius:8px; cursor:pointer; }
			.saudi-legal__draft:hover { border-color:var(--green); }
			.saudi-legal__notice { padding:13px 15px; color:#6d5314; background:#fff8df; border:1px solid #ead89b; border-radius:10px; font-size:11px; line-height:1.8; }
			.saudi-legal__empty { padding:38px 20px; color:var(--muted); text-align:center; background:#fff; border:1px solid var(--line); border-radius:12px; }
			.saudi-legal__draft-output { direction:rtl; text-align:right; }
			.saudi-legal__draft-output blockquote { margin:12px 0; padding:14px; color:#243a31; background:#f3f0e7; border-right:4px solid #0b5d4b; line-height:2; }
			@media(max-width:850px) { .saudi-legal__layout { grid-template-columns:1fr; } .saudi-legal__side { position:static; grid-template-columns:1fr 1fr; } }
			@media(max-width:600px) { .saudi-legal__hero { grid-template-columns:1fr; padding:19px; } .saudi-legal__folio { min-width:0; } .saudi-legal__search { grid-template-columns:1fr; } .saudi-legal__search button { width:100%; } .saudi-legal__side { grid-template-columns:1fr; } .saudi-legal__result-head { display:grid; } .saudi-legal__rule { justify-self:start; } }
			@media(prefers-reduced-motion:reduce) { .saudi-legal * { transition:none!important; scroll-behavior:auto!important; } }
		`;
		document.head.appendChild(style);
	}

	renderLoading() {
		this.page.body.html(`<main class="saudi-legal" dir="rtl" lang="ar" aria-busy="true"><section class="saudi-legal__empty">جارٍ فتح فهرس القواعد النظامية…</section></main>`);
	}

	async search(query) {
		this.query = String(query || "").trim();
		try {
			const response = await frappe.call({ method: "saudi_hr.saudi_hr.enterprise_operations.search_hr_guidance", args: { query: this.query, limit: 12 } });
			this.data = response.message || {};
			this.render();
		} catch (error) {
			this.page.body.html(`<main class="saudi-legal" dir="rtl" lang="ar"><section class="saudi-legal__empty">تعذر تحميل الدليل النظامي. تحقق من الاتصال ثم أعد المحاولة.</section></main>`);
		}
	}

	render() {
		const d = this.data;
		const results = (d.results || []).length ? d.results.map((item) => `<article class="saudi-legal__result" data-risk="${String(item.risk).includes("Critical") ? "critical" : "standard"}"><div class="saudi-legal__result-head"><h2>${this.esc(item.title_ar)}</h2><span class="saudi-legal__rule">${this.esc(item.rule_id)}</span></div><p class="saudi-legal__guidance">${this.esc(item.guidance_ar)}</p><div class="saudi-legal__control"><strong>ضابط التشغيل:</strong> ${this.esc(item.control_ar)}</div><div class="saudi-legal__citation"><span><b>المصدر:</b> ${this.esc(item.citation.source)}</span><span><b>صفحة PDF:</b> ${this.esc(item.citation.pdf_page)}</span><span><b>المرجع:</b> ${this.esc(item.citation.article_reference)}</span><span><b>الإصدار:</b> ${this.esc(item.citation.catalog_version)}</span></div></article>`).join("") : `<div class="saudi-legal__empty"><strong>لم أجد قاعدة مطابقة.</strong><br>جرّب عبارة أقصر مثل: إجازة مرضية، عمل إضافي، تسوية، أو فترة تجربة.</div>`;
		this.page.body.html(`<main class="saudi-legal" dir="rtl" lang="ar"><section class="saudi-legal__hero"><div><p class="saudi-legal__eyebrow">فهرس نظامي مؤرخ · GROUNDED HR GUIDE</p><h1>اسأل القاعدة، واعرف الدليل والإجراء</h1><p>بحث عربي داخل كتالوج اللائحة التنفيذية الفعّال. كل نتيجة ترتبط بقاعدة وصفحة ومصدر وإجراء تشغيلي؛ لا توجد إجابات بلا مرجع.</p></div><div class="saudi-legal__folio"><strong>28 قاعدة</strong><span>${this.esc(d.catalog_version)}</span></div></section>
			<section class="saudi-legal__search"><label><span class="sr-only">ابحث في الدليل النظامي</span><input data-search value="${this.esc(this.query)}" placeholder="مثال: احتساب الإجازة المرضية أو مهلة التسوية…" autocomplete="off"></label><button data-search-button>ابحث في القواعد</button></section>
			<div class="saudi-legal__topics" aria-label="موضوعات مقترحة">${["الإجازة المرضية", "العمل الإضافي", "فترة التجربة", "العمل المرن", "التسوية النهائية", "إجازة الوضع"].map((topic) => `<button class="saudi-legal__topic" data-topic="${topic}">${topic}</button>`).join("")}</div>
			<section class="saudi-legal__layout"><div class="saudi-legal__results" aria-live="polite">${results}</div><aside class="saudi-legal__side"><div class="saudi-legal__panel"><h2>مسودات تشغيلية آمنة</h2><p>تنشئ نصاً أولياً مع مراجع، ويظل الاعتماد النهائي مسؤولية المنشأة.</p><div class="saudi-legal__drafts"><button class="saudi-legal__draft" data-draft="policy_acknowledgement">إقرار اطلاع على سياسة</button><button class="saudi-legal__draft" data-draft="contract_review">محضر مراجعة عقد</button><button class="saudi-legal__draft" data-draft="corrective_action">خطة إجراء تصحيحي</button><button class="saudi-legal__draft" data-draft="final_settlement">قائمة تحقق التسوية</button></div></div><div class="saudi-legal__notice">${this.esc(d.notice_ar)}</div></aside></section></main>`);
		this.bind();
	}

	bind() {
		const input = this.page.body.find("[data-search]");
		this.page.body.find("[data-search-button]").on("click", () => this.search(input.val()));
		input.on("keydown", (event) => { if (event.key === "Enter") this.search(input.val()); });
		input.on("input", () => { clearTimeout(this.timer); this.timer = setTimeout(() => this.search(input.val()), 450); });
		this.page.body.find("[data-topic]").on("click", (event) => this.search(event.currentTarget.dataset.topic));
		this.page.body.find("[data-draft]").on("click", (event) => this.createDraft(event.currentTarget.dataset.draft));
	}

	async createDraft(templateType) {
		try {
			const response = await frappe.call({ method: "saudi_hr.saudi_hr.enterprise_operations.get_guided_draft", args: { template_type: templateType } });
			const draft = response.message || {};
			const citations = (draft.citations || []).map((citation) => `${citation.source} — صفحة ${citation.pdf_page}`).join("<br>");
			const dialog = new frappe.ui.Dialog({ title: this.esc(draft.title_ar), fields: [{ fieldtype: "HTML", fieldname: "draft" }], primary_action_label: "نسخ المسودة", primary_action: () => { this.copy(draft.body_ar || ""); dialog.hide(); } });
			dialog.fields_dict.draft.$wrapper.html(`<div class="saudi-legal__draft-output"><blockquote>${this.esc(draft.body_ar)}</blockquote><p><strong>المراجع:</strong><br>${citations}</p><p class="text-muted">${this.esc(draft.notice_ar)}</p></div>`);
			dialog.show();
		} catch (error) {
			frappe.msgprint({ title: "تعذر إنشاء المسودة", message: "تحقق من الاتصال وأعد المحاولة.", indicator: "red" });
		}
	}

	copy(text) {
		if (frappe.utils.copy_to_clipboard) frappe.utils.copy_to_clipboard(text);
		else navigator.clipboard?.writeText(text);
		frappe.show_alert({ message: "نُسخت المسودة للمراجعة.", indicator: "green" }, 5);
	}

	open(route) {
		frappe.set_route(route.replace(/^\/app\//, "").split("/"));
	}
};
