frappe.pages["saudi-compliance-command-center"].on_page_load = function (wrapper) {
	wrapper.saudiComplianceCenter = new SaudiComplianceCommandCenter(wrapper);
};

frappe.pages["saudi-compliance-command-center"].on_page_show = function (wrapper) {
	wrapper.saudiComplianceCenter?.load();
};

class SaudiComplianceCommandCenter {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Saudi HR Command Center / مركز قيادة الموارد البشرية السعودية"),
			single_column: true,
		});
		this.installStyles();
		this.page.set_primary_action(__("Refresh / تحديث"), () => this.load(), "refresh");
		this.page.add_menu_item(__("Professional HR Hub / مركز الموارد البشرية"), () => this.open("/app/professional-hr-hub"));
		this.renderLoading();
		this.load();
	}

	installStyles() {
		if (document.getElementById("saudi-compliance-center-styles")) return;
		const style = document.createElement("style");
		style.id = "saudi-compliance-center-styles";
		style.textContent = `
			.saudi-cc { --cc-ink:#0f172a; --cc-muted:#475569; --cc-canvas:#f8fafc; --cc-border:#cbd5e1; --cc-primary:#166534; --cc-primary-soft:#dcfce7; --cc-critical:#b91c1c; --cc-warning:#b45309; --cc-info:#0369a1; color:var(--cc-ink); font-family:"Noto Sans Arabic","Tajawal",var(--font-stack); display:grid; gap:16px; padding-block:8px 32px; }
			.saudi-cc[dir="rtl"] { text-align:right; }
			.saudi-cc__panel { background:#fff; border:1px solid var(--cc-border); border-radius:10px; padding:20px; }
			.saudi-cc__hero { background:linear-gradient(135deg,#0f172a,#14532d); color:#fff; border:0; display:grid; grid-template-columns:minmax(0,1fr) minmax(220px,.34fr); gap:24px; align-items:center; }
			.saudi-cc__eyebrow { color:#bbf7d0; font-size:12px; font-weight:800; letter-spacing:.04em; margin-block-end:8px; }
			.saudi-cc__title { color:inherit; font-size:clamp(24px,3vw,36px); line-height:1.25; margin:0 0 8px; }
			.saudi-cc__lead { color:#dbeafe; font-size:14px; line-height:1.8; margin:0; max-width:72ch; }
			.saudi-cc__score { display:grid; place-items:center; min-height:150px; border:1px solid rgba(255,255,255,.25); border-radius:10px; background:rgba(255,255,255,.08); }
			.saudi-cc__score strong { font-size:48px; line-height:1; }
			.saudi-cc__score span { color:#dbeafe; font-size:12px; margin-block-start:8px; }
			.saudi-cc__grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }
			.saudi-cc__metric { background:#fff; border:1px solid var(--cc-border); border-radius:10px; padding:16px; min-height:112px; }
			.saudi-cc__metric strong { display:block; font-size:28px; margin-block:6px; }
			.saudi-cc__label,.saudi-cc__meta { color:var(--cc-muted); font-size:12px; line-height:1.6; }
			.saudi-cc__section-head { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; margin-block-end:14px; }
			.saudi-cc__section-head h2 { font-size:18px; margin:0; }
			.saudi-cc__actions { display:grid; gap:8px; }
			.saudi-cc__action { display:grid; grid-template-columns:8px minmax(0,1fr) auto; gap:12px; align-items:center; border:1px solid var(--cc-border); border-radius:10px; padding:12px; }
			.saudi-cc__action-dot { width:8px; height:100%; min-height:46px; border-radius:999px; background:var(--cc-warning); }
			.saudi-cc__action[data-severity="critical"] .saudi-cc__action-dot { background:var(--cc-critical); }
			.saudi-cc__action-title { font-weight:800; font-size:14px; margin-block-end:3px; }
			.saudi-cc__button { min-height:44px; border:1px solid var(--cc-primary); border-radius:10px; padding:9px 14px; background:var(--cc-primary); color:#fff; font-weight:800; cursor:pointer; }
			.saudi-cc__button:hover { background:#14532d; }
			.saudi-cc__button:focus-visible,.saudi-cc a:focus-visible { outline:3px solid #38bdf8; outline-offset:2px; }
			.saudi-cc__button--quiet { color:var(--cc-primary); background:#fff; }
			.saudi-cc__journeys { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }
			.saudi-cc__journey { border:1px solid var(--cc-border); border-radius:10px; padding:16px; display:grid; gap:8px; }
			.saudi-cc__journey h3 { font-size:15px; margin:0; }
			.saudi-cc__journey p { color:var(--cc-muted); font-size:13px; line-height:1.7; margin:0; }
			.saudi-cc__quick { display:flex; flex-wrap:wrap; gap:8px; }
			.saudi-cc__empty,.saudi-cc__error { border:1px dashed var(--cc-border); border-radius:10px; padding:24px; text-align:center; color:var(--cc-muted); }
			.saudi-cc__disclaimer { background:#fffbeb; border-color:#fcd34d; color:#78350f; font-size:12px; line-height:1.8; }
			@media (max-width:1024px){ .saudi-cc__grid{grid-template-columns:repeat(2,minmax(0,1fr));} }
			@media (max-width:768px){ .saudi-cc__hero,.saudi-cc__journeys{grid-template-columns:1fr;} .saudi-cc__action{grid-template-columns:8px minmax(0,1fr);} .saudi-cc__action .saudi-cc__button{grid-column:2;} }
			@media (max-width:480px){ .saudi-cc__grid{grid-template-columns:1fr;} .saudi-cc__panel{padding:16px;} .saudi-cc__quick{display:grid;} .saudi-cc__button{width:100%;} }
			@media (prefers-reduced-motion:reduce){ .saudi-cc *{scroll-behavior:auto!important;transition:none!important;animation:none!important;} }
		`;
		document.head.appendChild(style);
	}

	renderLoading() {
		this.page.body.html(`<main class="saudi-cc" dir="rtl" aria-busy="true"><section class="saudi-cc__panel saudi-cc__empty">${__("Loading compliance priorities… / جارٍ تحميل أولويات الامتثال…")}</section></main>`);
	}

	load() {
		this.renderLoading();
		frappe.call({
			method: "saudi_hr.saudi_hr.compliance_command_center.get_compliance_command_center",
			callback: (response) => this.render(response.message || {}),
			error: () => this.renderError(),
		});
	}

	render(data) {
		const metrics = data.metrics || {};
		const actionHtml = (data.actions || []).length ? data.actions.map((action) => this.actionCard(action)).join("") : `<div class="saudi-cc__empty">${__("No urgent compliance action is waiting. / لا توجد إجراءات امتثال عاجلة بانتظار المعالجة.")}</div>`;
		this.page.body.html(`
			<main class="saudi-cc" dir="rtl">
				<section class="saudi-cc__panel saudi-cc__hero">
					<div><div class="saudi-cc__eyebrow">SAUDI HR · ${this.esc(data.catalog_version || "")}</div><h1 class="saudi-cc__title">مركز قيادة الموارد البشرية السعودية</h1><p class="saudi-cc__lead">حوّل الالتزامات النظامية إلى أولويات واضحة، مسؤوليات محددة، وأدلة جاهزة للتدقيق.</p></div>
					<div class="saudi-cc__score" aria-label="${__("Operational compliance health / صحة الامتثال التشغيلية")}"><strong>${this.esc(metrics.health_score ?? 0)}</strong><span>صحة الامتثال التشغيلية من 100</span></div>
				</section>
				<section class="saudi-cc__grid" aria-label="مؤشرات الامتثال">
					${this.metric("القواعد القانونية الموثقة", metrics.legal_rules, `${metrics.automation_percentage || 0}% مرتبطة باختبار آلي`)}
					${this.metric("المهام المفتوحة", metrics.open_tasks, `${metrics.overdue_tasks || 0} متأخرة`)}
					${this.metric("التسويات المتأخرة", metrics.overdue_settlements, "مهلة 7 أو 14 يوماً حسب صاحب الإنهاء")}
					${this.metric("ترتيبات تحتاج مراجعة", metrics.review_arrangements, "مرن، مؤقت، عرضي، أو تحويل عقد")}
				</section>
				<section class="saudi-cc__panel"><div class="saudi-cc__section-head"><div><h2>ما يحتاج إجراء الآن</h2><div class="saudi-cc__meta">الأكثر خطورة والأقرب استحقاقاً يظهر أولاً.</div></div><button class="saudi-cc__button saudi-cc__button--quiet" data-route="/app/saudi-regulatory-task">عرض كل المهام</button></div><div class="saudi-cc__actions">${actionHtml}</div></section>
				<section class="saudi-cc__panel"><div class="saudi-cc__section-head"><div><h2>رحلات عمل موجّهة</h2><div class="saudi-cc__meta">ابدأ بالنتيجة المطلوبة واتبع السجلات والأدلة المرتبطة بها.</div></div></div><div class="saudi-cc__journeys">${(data.journeys || []).map((journey) => this.journeyCard(journey)).join("")}</div></section>
				<section class="saudi-cc__panel"><div class="saudi-cc__section-head"><div><h2>إجراءات سريعة</h2><div class="saudi-cc__meta">الوصول المباشر إلى الحوكمة والتغطية القانونية.</div></div></div><div class="saudi-cc__quick">${(data.quick_actions || []).map((item) => `<button class="saudi-cc__button saudi-cc__button--quiet" data-route="${this.esc(item.route)}">${this.esc(item.label)}</button>`).join("")}</div></section>
				<aside class="saudi-cc__panel saudi-cc__disclaimer">${this.esc(data.disclaimer || "")}</aside>
			</main>`);
		this.bindRoutes();
	}

	metric(label, value, meta) { return `<article class="saudi-cc__metric"><div class="saudi-cc__label">${this.esc(label)}</div><strong>${this.esc(value ?? 0)}</strong><div class="saudi-cc__meta">${this.esc(meta)}</div></article>`; }
	actionCard(action) { return `<article class="saudi-cc__action" data-severity="${this.esc(action.severity || "warning")}"><span class="saudi-cc__action-dot" aria-hidden="true"></span><div><div class="saudi-cc__action-title">${this.esc(action.title)}</div><div class="saudi-cc__meta">${this.esc([action.status, action.due_date, action.owner].filter(Boolean).join(" · "))}</div></div><button class="saudi-cc__button" data-route="${this.esc(action.route)}">${this.esc(action.action_label || "راجع")}</button></article>`; }
	journeyCard(journey) { return `<article class="saudi-cc__journey"><h3>${this.esc(journey.title)}${journey.count ? ` · ${this.esc(journey.count)}` : ""}</h3><p>${this.esc(journey.description)}</p><div><button class="saudi-cc__button saudi-cc__button--quiet" data-route="${this.esc(journey.route)}">ابدأ الرحلة</button></div></article>`; }

	renderError() {
		this.page.body.html(`<main class="saudi-cc" dir="rtl"><section class="saudi-cc__panel saudi-cc__error"><h2>تعذّر تحميل مركز القيادة</h2><p>تحقق من اتصال الخادم وصلاحيتك، ثم أعد المحاولة.</p><button class="saudi-cc__button" data-retry>أعد المحاولة</button></section></main>`);
		this.page.body.find("[data-retry]").on("click", () => this.load());
	}

	bindRoutes() { this.page.body.find("[data-route]").on("click", (event) => this.open(event.currentTarget.dataset.route)); }
	open(route) { if (route?.startsWith("/app/")) frappe.set_route(route.slice(5).split("/")); else if (route) window.location.href = route; }
	esc(value) { return frappe.utils.escape_html(String(value ?? "")); }
}
