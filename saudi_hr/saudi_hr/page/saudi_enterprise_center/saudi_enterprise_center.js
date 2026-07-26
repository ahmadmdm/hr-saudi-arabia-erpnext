frappe.provide("saudi_hr");

frappe.pages["saudi-enterprise-center"].on_page_load = function (wrapper) {
	new saudi_hr.EnterpriseCenter(wrapper);
};

saudi_hr.EnterpriseCenter = class EnterpriseCenter {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.data = null;
		this.company = null;
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: "مركز عمليات الموارد البشرية السعودية",
			single_column: true,
		});
		this.ensureStyles();
		this.page.set_primary_action("تحديث الحالة", () => this.load(), "refresh");
		this.page.add_menu_item("بوابة الموظف والمدير", () => this.open("/app/saudi-self-service"));
		this.page.add_menu_item("الدليل النظامي العربي", () => this.open("/app/saudi-hr-legal-guide"));
		this.renderLoading();
		this.load();
	}

	esc(value) {
		return frappe.utils.escape_html(String(value ?? ""));
	}

	ensureStyles() {
		if (document.getElementById("saudi-enterprise-center-style")) return;
		const style = document.createElement("style");
		style.id = "saudi-enterprise-center-style";
		style.textContent = `
			.saudi-enterprise {
				--registry:#0b5d4b; --palm:#13795b; --ink:#13251f; --muted:#52635d;
				--paper:#f3f0e7; --sand:#d6c7a1; --clay:#b54432; --line:#d9ddd7;
				display:grid; grid-template-columns:minmax(0,1fr); gap:16px; min-width:0; padding:8px 0 32px; color:var(--ink);
				font-family:"Noto Sans Arabic","Tajawal",var(--font-stack); text-align:right;
			}
			.saudi-enterprise *, .saudi-enterprise *::before, .saudi-enterprise *::after { box-sizing:border-box; }
			.saudi-enterprise > *, .saudi-enterprise__hero > *, .saudi-enterprise__section-head > *, .saudi-enterprise__capability > * { min-width:0; }
			.saudi-enterprise button, .saudi-enterprise select { font:inherit; }
			.saudi-enterprise__hero {
				position:relative; overflow:hidden; display:grid; grid-template-columns:minmax(0,1fr) 180px;
				gap:24px; padding:26px; color:#fff; background:var(--ink); border-radius:16px;
				box-shadow:0 16px 45px rgba(19,37,31,.16);
			}
			.saudi-enterprise__hero::after { content:""; position:absolute; inset:auto -90px -130px auto; width:310px; height:310px; border:42px solid rgba(214,199,161,.13); border-radius:50%; }
			.saudi-enterprise__eyebrow { margin:0 0 7px; color:#d6c7a1; font-size:12px; font-weight:800; letter-spacing:.03em; }
			.saudi-enterprise__title { margin:0; color:#fff; font-family:"Noto Kufi Arabic","Noto Sans Arabic",sans-serif; font-size:clamp(22px,3vw,34px); line-height:1.45; font-weight:800; }
			.saudi-enterprise__lead { max-width:760px; margin:10px 0 0; color:#dce7e1; font-size:14px; line-height:1.9; }
			.saudi-enterprise__hero-tools { position:relative; z-index:1; display:grid; align-content:space-between; justify-items:end; gap:18px; }
			.saudi-enterprise__score { width:132px; aspect-ratio:1; display:grid; place-content:center; text-align:center; border:1px solid rgba(255,255,255,.22); border-radius:50%; background:rgba(255,255,255,.07); }
			.saudi-enterprise__score strong { font-size:34px; line-height:1; }
			.saudi-enterprise__score span { margin-top:7px; font-size:11px; color:#dce7e1; }
			.saudi-enterprise__select { min-height:44px; width:100%; padding:8px 12px; color:var(--ink); background:#fff; border:1px solid #cbd5cf; border-radius:9px; }
			.saudi-enterprise__rail { position:relative; display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:0; padding:20px 16px 14px; background:#fff; border:1px solid var(--line); border-radius:14px; }
			.saudi-enterprise__rail::before { content:""; position:absolute; top:46px; right:12.5%; left:12.5%; height:2px; background:#dfe6e2; }
			.saudi-enterprise__station { position:relative; z-index:1; display:grid; justify-items:center; gap:7px; min-height:92px; padding:0 8px; border:0; background:transparent; color:var(--ink); cursor:pointer; border-radius:10px; }
			.saudi-enterprise__station:hover { background:#f5f8f6; }
			.saudi-enterprise__station:disabled { cursor:not-allowed; opacity:.55; }
			.saudi-enterprise__station:focus-visible, .saudi-enterprise button:focus-visible, .saudi-enterprise select:focus-visible { outline:3px solid #38bdf8; outline-offset:3px; }
			.saudi-enterprise__station-mark { width:52px; height:52px; display:grid; place-items:center; border:5px solid #fff; border-radius:50%; color:#fff; background:var(--registry); box-shadow:0 0 0 2px #b9c9c2; font-size:13px; font-weight:900; }
			.saudi-enterprise__station[data-ready="false"] .saudi-enterprise__station-mark { color:#765b18; background:#eadba9; }
			.saudi-enterprise__station strong { font-size:13px; }
			.saudi-enterprise__station small { color:var(--muted); font-size:11px; line-height:1.5; text-align:center; }
			.saudi-enterprise__section-head { display:flex; align-items:end; justify-content:space-between; gap:14px; margin:4px 2px 0; }
			.saudi-enterprise__section-head h2 { margin:0; font-size:18px; font-weight:800; }
			.saudi-enterprise__section-head p { margin:3px 0 0; color:var(--muted); font-size:12px; }
			.saudi-enterprise__ledger { overflow:hidden; background:#fff; border:1px solid var(--line); border-radius:14px; }
			.saudi-enterprise__capability { display:grid; grid-template-columns:38px minmax(180px,1.1fr) minmax(220px,1.6fr) minmax(105px,.45fr) 44px; gap:14px; align-items:center; width:100%; min-height:78px; padding:14px 18px; color:inherit; text-align:right; border:0; border-bottom:1px solid #e6e9e6; background:#fff; cursor:pointer; }
			.saudi-enterprise__capability:last-child { border-bottom:0; }
			.saudi-enterprise__capability:hover { background:#f8faf8; }
			.saudi-enterprise__index { font-family:ui-monospace,monospace; font-size:11px; color:#688078; }
			.saudi-enterprise__capability strong { font-size:14px; }
			.saudi-enterprise__capability p { margin:0; color:var(--muted); font-size:12px; line-height:1.7; }
			.saudi-enterprise__value { text-align:left; }
			.saudi-enterprise__value b { display:block; font-size:20px; color:var(--registry); }
			.saudi-enterprise__value small { color:var(--muted); }
			.saudi-enterprise__arrow { font-size:20px; color:#80958e; transform:rotate(180deg); }
			.saudi-enterprise__two { display:grid; grid-template-columns:minmax(0,1.45fr) minmax(300px,.75fr); gap:16px; }
			.saudi-enterprise__two > * { min-width:0; }
			.saudi-enterprise__panel { min-width:0; max-width:100%; padding:18px; background:#fff; border:1px solid var(--line); border-radius:14px; }
			.saudi-enterprise__panel h3 { margin:0 0 13px; font-size:15px; }
			.saudi-enterprise__transactions { width:100%; border-collapse:collapse; font-size:12px; }
			.saudi-enterprise__transactions th { padding:9px 8px; color:var(--muted); font-weight:700; text-align:right; border-bottom:1px solid var(--line); }
			.saudi-enterprise__transactions td { padding:11px 8px; border-bottom:1px solid #edf0ed; vertical-align:top; }
			.saudi-enterprise__transactions tr:last-child td { border-bottom:0; }
			.saudi-enterprise__fingerprint { direction:ltr; display:inline-block; max-width:100%; overflow-wrap:anywhere; word-break:break-all; vertical-align:middle; font-family:ui-monospace,monospace; color:#5b6e67; }
			.saudi-enterprise__badge { display:inline-flex; align-items:center; min-height:25px; padding:3px 8px; border-radius:999px; color:#0b5d4b; background:#e5f3ed; font-size:11px; font-weight:700; }
			.saudi-enterprise__check { display:grid; grid-template-columns:22px 1fr auto; gap:9px; align-items:center; min-height:45px; border-bottom:1px solid #edf0ed; font-size:12px; }
			.saudi-enterprise__check:last-child { border-bottom:0; }
			.saudi-enterprise__check-mark { width:18px; height:18px; display:grid; place-items:center; border-radius:50%; color:#fff; background:var(--registry); font-size:11px; }
			.saudi-enterprise__check[data-passed="false"] .saudi-enterprise__check-mark { background:var(--clay); }
			.saudi-enterprise__check button { min-width:44px; min-height:44px; padding:5px 9px; color:var(--registry); border:0; background:transparent; cursor:pointer; }
			.saudi-enterprise__notice { padding:13px 15px; color:#5f4b18; background:#fff8df; border:1px solid #ecd99a; border-radius:11px; font-size:12px; line-height:1.8; }
			.saudi-enterprise__empty { padding:28px; color:var(--muted); text-align:center; }
			.saudi-enterprise__error { padding:24px; color:#7f1d1d; background:#fff1f1; border:1px solid #fecaca; border-radius:12px; }
			.saudi-enterprise__error button { min-height:44px; margin-top:12px; padding:8px 14px; color:#fff; background:#991b1b; border:0; border-radius:8px; }
			.enterprise-preview { direction:rtl; text-align:right; font-family:"Noto Sans Arabic","Tajawal",sans-serif; }
			.enterprise-preview__summary { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-bottom:12px; }
			.enterprise-preview__metric { padding:10px; background:#f3f6f4; border-radius:8px; }
			.enterprise-preview__metric strong { display:block; font-size:18px; color:#0b5d4b; }
			.enterprise-preview__issues { max-height:140px; overflow:auto; margin:10px 0; padding:10px 28px 10px 10px; color:#7c2d12; background:#fff7ed; border-radius:8px; }
			.enterprise-preview pre { max-height:260px; overflow:auto; direction:ltr; text-align:left; padding:12px; color:#dbeae3; background:#13251f; border-radius:8px; font-size:11px; }
			@media (max-width:900px) {
				.saudi-enterprise__hero { grid-template-columns:1fr; }
				.saudi-enterprise__hero-tools { grid-template-columns:120px minmax(180px,1fr); align-items:center; justify-items:stretch; }
				.saudi-enterprise__score { width:108px; }
				.saudi-enterprise__two { grid-template-columns:minmax(0,1fr); }
				.saudi-enterprise__capability { grid-template-columns:30px minmax(150px,1fr) minmax(190px,1.2fr) 95px 30px; }
			}
			@media (max-width:650px) {
				.saudi-enterprise { gap:12px; }
				.saudi-enterprise__hero { padding:20px; border-radius:12px; }
				.saudi-enterprise__hero-tools { grid-template-columns:1fr; justify-items:start; }
				.saudi-enterprise__score { width:96px; }
				.saudi-enterprise__rail { grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }
				.saudi-enterprise__rail::before { display:none; }
				.saudi-enterprise__station { min-height:116px; padding:10px 6px; background:#f8faf8; }
				.saudi-enterprise__capability { grid-template-columns:28px minmax(0,1fr) auto; gap:8px; padding:14px; }
				.saudi-enterprise__capability p { grid-column:2 / -1; }
				.saudi-enterprise__value { grid-column:2; text-align:right; }
				.saudi-enterprise__arrow { grid-column:3; grid-row:1; }
				.saudi-enterprise__station small, .saudi-enterprise__badge, .saudi-enterprise__capability p { overflow-wrap:anywhere; }
				.saudi-enterprise__transactions { display:block; width:100%; max-width:100%; overflow-x:auto; white-space:nowrap; }
				.enterprise-preview__summary { grid-template-columns:1fr; }
			}
			@media (prefers-reduced-motion:reduce) { .saudi-enterprise *, .saudi-enterprise *::before, .saudi-enterprise *::after { scroll-behavior:auto!important; transition:none!important; } }
		`;
		document.head.appendChild(style);
	}

	renderLoading() {
		this.page.body.html(`<main class="saudi-enterprise" dir="rtl" lang="ar" aria-busy="true"><section class="saudi-enterprise__panel saudi-enterprise__empty">جارٍ بناء سجل العمليات المؤسسي…</section></main>`);
	}

	async load(company = this.company) {
		try {
			const response = await frappe.call({
				method: "saudi_hr.saudi_hr.enterprise_operations.get_enterprise_operations_center",
				args: { company: company || "" },
				freeze: false,
			});
			this.data = response.message || {};
			this.company = this.data.company;
			this.render();
		} catch (error) {
			this.renderError(error);
		}
	}

	render() {
		const d = this.data;
		const brand = d.branding || {};
		const companyOptions = (d.companies || []).map((company) => `<option value="${this.esc(company)}" ${company === d.company ? "selected" : ""}>${this.esc(company)}</option>`).join("");
		const providerStations = (d.providers || []).map((provider) => {
			const profile = (d.profiles || []).find((item) => item.provider === provider.provider);
			const ready = profile && !String(profile.configuration_status).includes("Required") && !String(profile.configuration_status).includes("Error");
			return `<button class="saudi-enterprise__station" data-profile="${this.esc(profile?.name || "")}" data-ready="${ready ? "true" : "false"}" ${profile ? "" : "disabled"}>
				<span class="saudi-enterprise__station-mark">${this.esc(provider.title_ar)}</span>
				<strong>${this.esc(provider.title_ar)}</strong>
				<small>${this.esc(profile?.configuration_status || "غير مهيأ")}</small>
			</button>`;
		}).join("");
		const capabilities = (d.capabilities || []).map((item, index) => `<button class="saudi-enterprise__capability" data-route="${this.esc(item.route)}">
			<span class="saudi-enterprise__index">${String(index + 1).padStart(2, "0")}</span>
			<strong>${this.esc(item.title_ar)}</strong>
			<p>${this.esc(item.summary_ar)}</p>
			<span class="saudi-enterprise__value"><b>${this.esc(item.value)}</b><small>${this.esc(item.unit_ar)}</small></span>
			<span class="saudi-enterprise__arrow" aria-hidden="true">←</span>
		</button>`).join("");
		const transactions = (d.transactions || []).length ? (d.transactions || []).map((row) => `<tr>
			<td><a href="/app/saudi-government-transaction/${encodeURIComponent(row.name)}">${this.esc(row.name)}</a></td>
			<td>${this.esc(row.provider)}</td><td>${this.esc(row.operation)}</td>
			<td><span class="saudi-enterprise__badge">${this.esc(row.status)}</span></td>
			<td>${this.esc(row.record_count)}</td><td><span class="saudi-enterprise__fingerprint">${this.esc(row.request_fingerprint)}</span></td>
		</tr>`).join("") : `<tr><td colspan="6" class="saudi-enterprise__empty">لا توجد معاملات مؤكدة بعد. ابدأ بمعاينة إحدى الجهات أعلاه.</td></tr>`;
		const checks = (d.readiness?.checks || []).map((check) => `<div class="saudi-enterprise__check" data-passed="${check.passed ? "true" : "false"}">
			<span class="saudi-enterprise__check-mark" aria-hidden="true">${check.passed ? "✓" : "!"}</span>
			<span>${this.esc(check.label_ar)}</span>
			<button data-route="${this.esc(check.action_route)}">${check.passed ? "عرض" : "عالج"}</button>
		</div>`).join("");

		this.page.body.html(`<main class="saudi-enterprise" dir="rtl" lang="ar" aria-busy="false" style="--registry:${this.esc(brand.brand_primary_color || "#0B5D4B")}">
			<section class="saudi-enterprise__hero">
				<div><p class="saudi-enterprise__eyebrow">سجل التشغيل المؤسسي · ENTERPRISE OPERATIONS LEDGER</p>
				<h1 class="saudi-enterprise__title">${this.esc(brand.organization_name_ar || "الموارد البشرية السعودية")}</h1>
				<p class="saudi-enterprise__lead">مسار موحّد للتكاملات الحكومية، الخدمة الذاتية، حماية الأجور، الوثائق، التحليلات، والتحديث النظامي—مع دليل تدقيق لكل إجراء.</p></div>
				<div class="saudi-enterprise__hero-tools"><div class="saudi-enterprise__score" aria-label="درجة جاهزية الإنتاج"><strong>${this.esc(d.readiness?.score || 0)}%</strong><span>جاهزية الإنتاج</span></div>
				<label><span class="sr-only">اختر الشركة</span><select class="saudi-enterprise__select" data-company>${companyOptions}</select></label></div>
			</section>
			<section aria-labelledby="provider-route-title"><div class="saudi-enterprise__section-head"><div><h2 id="provider-route-title">مسار الجهات الحكومية</h2><p>اختر جهة لمعاينة البيانات المؤهلة قبل إنشاء ملف تبادل خاص.</p></div></div><div class="saudi-enterprise__rail">${providerStations}</div></section>
			<div class="saudi-enterprise__notice">${this.esc(d.external_submission_notice_ar || "")}</div>
			<section aria-labelledby="capabilities-title"><div class="saudi-enterprise__section-head"><div><h2 id="capabilities-title">دفتر القدرات</h2><p>ثمانية مسارات تشغيلية، وكل صف يقود إلى إجراء حقيقي.</p></div><span class="saudi-enterprise__badge">${this.esc(d.legal_release?.version || "")}</span></div><div class="saudi-enterprise__ledger">${capabilities}</div></section>
			<section class="saudi-enterprise__two">
				<div class="saudi-enterprise__panel"><h3>آخر معاملات التبادل</h3><table class="saudi-enterprise__transactions"><thead><tr><th>المعاملة</th><th>الجهة</th><th>العملية</th><th>الحالة</th><th>السجلات</th><th>البصمة</th></tr></thead><tbody>${transactions}</tbody></table></div>
				<div class="saudi-enterprise__panel"><h3>قائمة جاهزية الإنتاج · ${this.esc(d.readiness?.passed || 0)}/${this.esc(d.readiness?.total || 0)}</h3>${checks}</div>
			</section>
		</main>`);
		this.bind();
	}

	bind() {
		this.page.body.find("[data-company]").on("change", (event) => {
			this.company = event.currentTarget.value;
			this.renderLoading();
			this.load(this.company);
		});
		this.page.body.find("[data-route]").on("click", (event) => this.open(event.currentTarget.dataset.route));
		this.page.body.find("[data-profile]").on("click", (event) => {
			const profile = event.currentTarget.dataset.profile;
			if (profile) this.previewProvider(profile);
		});
	}

	open(route) {
		if (!route) return;
		if (route.startsWith("/app/")) {
			frappe.set_route(route.replace(/^\/app\//, "").split("/"));
		} else {
			window.location.assign(route);
		}
	}

	async previewProvider(profileName) {
		try {
			const response = await frappe.call({
				method: "saudi_hr.saudi_hr.enterprise_operations.preview_provider_export",
				args: { profile_name: profileName },
				freeze: true,
				freeze_message: "جارٍ فحص البيانات المؤهلة…",
			});
			this.showPreview(response.message || {}, profileName);
		} catch (error) {
			frappe.msgprint({ title: "تعذرت المعاينة", message: "تحقق من صلاحيتك واكتمال بيانات الجهة ثم أعد المحاولة.", indicator: "red" });
		}
	}

	showPreview(preview, profileName) {
		const issues = [...(preview.errors || []), ...(preview.warnings || [])];
		const issueHtml = issues.length ? `<ul class="enterprise-preview__issues">${issues.map((item) => `<li>${this.esc(item.record)} — ${this.esc(item.message_ar)}</li>`).join("")}</ul>` : `<p class="text-muted">لم تظهر ملاحظات مانعة في المعاينة.</p>`;
		const dialog = new frappe.ui.Dialog({
			title: `معاينة ${this.esc(preview.provider?.title_ar || "التكامل")}`,
			fields: [{ fieldtype: "HTML", fieldname: "preview" }],
			primary_action_label: preview.can_confirm ? "إنشاء ملف تبادل خاص" : "إغلاق",
			primary_action: () => {
				if (!preview.can_confirm) return dialog.hide();
				dialog.hide();
				this.confirmExport(profileName, preview.confirmation_phrase);
			},
		});
		dialog.fields_dict.preview.$wrapper.html(`<div class="enterprise-preview">
			<div class="enterprise-preview__summary"><div class="enterprise-preview__metric"><span>السجلات</span><strong>${this.esc(preview.record_count)}</strong></div><div class="enterprise-preview__metric"><span>أخطاء مانعة</span><strong>${this.esc((preview.errors || []).length)}</strong></div><div class="enterprise-preview__metric"><span>تنبيهات</span><strong>${this.esc((preview.warnings || []).length)}</strong></div></div>
			<p>${this.esc(preview.notice_ar)}</p>${issueHtml}<h5>عينة محجوبة الحقول الحساسة</h5><pre>${this.esc(JSON.stringify(preview.sample || [], null, 2))}</pre><p class="text-muted">بصمة المعاينة: <span class="saudi-enterprise__fingerprint">${this.esc(preview.fingerprint)}</span></p>
		</div>`);
		dialog.show();
	}

	confirmExport(profileName, phrase) {
		frappe.prompt([
			{ fieldname: "confirmation_phrase", fieldtype: "Data", label: `اكتب: ${phrase}`, reqd: 1, description: "سيُنشأ ملف خاص داخل النظام وسجل تدقيق. لن يحدث إرسال خارجي." },
		], async (values) => {
			try {
				const response = await frappe.call({ method: "saudi_hr.saudi_hr.enterprise_operations.confirm_provider_export", args: { profile_name: profileName, confirmation_phrase: values.confirmation_phrase }, freeze: true, freeze_message: "جارٍ إنشاء الملف الخاص…" });
				const result = response.message || {};
				frappe.msgprint({ title: result.reused ? "ملف مطابق موجود" : "تم إنشاء ملف التبادل", message: `${this.esc(result.notice_ar)}<br><a href="${this.esc(result.file_url)}">تنزيل الملف الخاص</a>`, indicator: "green" });
				this.load();
			} catch (error) {
				frappe.msgprint({ title: "لم يُنشأ الملف", message: "راجع عبارة التأكيد وأخطاء البيانات الظاهرة في المعاينة.", indicator: "red" });
			}
		}, "تأكيد إنشاء ملف التبادل", "إنشاء الملف");
	}

	renderError(error) {
		this.page.body.html(`<main class="saudi-enterprise" dir="rtl" lang="ar"><section class="saudi-enterprise__error"><strong>تعذر تحميل مركز العمليات.</strong><p>تحقق من اتصال الخادم وصلاحياتك، ثم أعد المحاولة.</p><button data-retry>إعادة المحاولة</button></section></main>`);
		this.page.body.find("[data-retry]").on("click", () => this.load());
	}
};
