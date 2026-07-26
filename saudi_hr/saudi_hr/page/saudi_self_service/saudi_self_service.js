frappe.provide("saudi_hr");

frappe.pages["saudi-self-service"].on_page_load = function (wrapper) {
	new saudi_hr.SelfServicePortal(wrapper);
};

saudi_hr.SelfServicePortal = class SelfServicePortal {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.data = null;
		this.page = frappe.ui.make_app_page({ parent: wrapper, title: "بوابة الموظف والمدير", single_column: true });
		this.ensureStyles();
		this.page.set_primary_action("تحديث ملفي", () => this.load(), "refresh");
		if ((frappe.user_roles || []).some((role) => ["HR Manager", "HR User", "System Manager"].includes(role))) {
			this.page.add_menu_item("مركز العمليات المؤسسي", () => this.open("/app/saudi-enterprise-center"));
		}
		this.renderLoading();
		this.load();
	}

	esc(value) { return frappe.utils.escape_html(String(value ?? "")); }
	money(value) { return new Intl.NumberFormat("ar-SA", { style: "currency", currency: "SAR", maximumFractionDigits: 2 }).format(Number(value || 0)); }

	ensureStyles() {
		if (document.getElementById("saudi-self-service-style")) return;
		const style = document.createElement("style");
		style.id = "saudi-self-service-style";
		style.textContent = `
			.saudi-self { --green:#0b5d4b; --ink:#13251f; --muted:#5e6d67; --paper:#f3f0e7; --sand:#d6c7a1; --line:#dce2de; --clay:#b54432; display:grid; gap:16px; padding:8px 0 32px; color:var(--ink); font-family:"Noto Sans Arabic","Tajawal",var(--font-stack); text-align:right; }
			.saudi-self *, .saudi-self *::before, .saudi-self *::after { box-sizing:border-box; }
			.saudi-self button { font:inherit; }
			.saudi-self__preview { display:flex; align-items:center; justify-content:space-between; gap:14px; padding:12px 15px; color:#6b4c0a; background:#fff8dc; border:1px solid #ead58f; border-radius:10px; font-size:12px; line-height:1.7; }
			.saudi-self__hero { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:18px; align-items:center; padding:24px; background:#fff; border:1px solid var(--line); border-top:5px solid var(--green); border-radius:14px; box-shadow:0 12px 34px rgba(19,37,31,.07); }
			.saudi-self__eyebrow { margin:0 0 5px; color:var(--green); font-size:11px; font-weight:800; }
			.saudi-self__hero h1 { margin:0; font-family:"Noto Kufi Arabic","Noto Sans Arabic",sans-serif; font-size:clamp(22px,3vw,31px); line-height:1.5; }
			.saudi-self__hero p { margin:7px 0 0; color:var(--muted); font-size:13px; line-height:1.8; }
			.saudi-self__identity { display:grid; gap:4px; min-width:190px; padding:14px 18px; background:var(--paper); border-radius:10px; }
			.saudi-self__identity strong { font-size:14px; }
			.saudi-self__identity span { color:var(--muted); font-size:11px; }
			.saudi-self__summary { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); overflow:hidden; background:var(--ink); border-radius:12px; color:#fff; }
			.saudi-self__metric { min-height:88px; padding:16px; border-left:1px solid rgba(255,255,255,.12); }
			.saudi-self__metric:last-child { border-left:0; }
			.saudi-self__metric strong { display:block; margin-bottom:5px; color:#e7dcb8; font-size:23px; }
			.saudi-self__metric span { color:#dce7e1; font-size:11px; line-height:1.5; }
			.saudi-self__actions { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:9px; }
			.saudi-self__action { min-height:58px; padding:9px 12px; color:var(--green); background:#fff; border:1px solid #b9cdc5; border-radius:10px; font-weight:700; cursor:pointer; }
			.saudi-self__action:hover { color:#fff; background:var(--green); border-color:var(--green); }
			.saudi-self button:focus-visible { outline:3px solid #38bdf8; outline-offset:3px; }
			.saudi-self__grid { display:grid; grid-template-columns:minmax(0,1.45fr) minmax(300px,.75fr); gap:16px; align-items:start; }
			.saudi-self__panel { padding:19px; background:#fff; border:1px solid var(--line); border-radius:13px; }
			.saudi-self__panel-head { display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:12px; }
			.saudi-self__panel h2 { margin:0; font-size:16px; }
			.saudi-self__count { display:inline-flex; min-width:28px; min-height:28px; align-items:center; justify-content:center; padding:2px 8px; color:#fff; background:var(--green); border-radius:999px; font-size:12px; font-weight:800; }
			.saudi-self__ack { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:12px; align-items:center; min-height:76px; padding:12px 0; border-bottom:1px solid #edf0ee; }
			.saudi-self__ack:last-child { border-bottom:0; }
			.saudi-self__ack strong { display:block; font-size:13px; }
			.saudi-self__ack p { margin:4px 0 0; color:var(--muted); font-size:11px; }
			.saudi-self__ack button { min-height:44px; padding:8px 13px; color:#fff; background:var(--green); border:0; border-radius:8px; font-weight:700; cursor:pointer; }
			.saudi-self__list { display:grid; gap:0; }
			.saudi-self__row { display:grid; grid-template-columns:minmax(0,1.4fr) minmax(90px,.55fr) auto; gap:10px; align-items:center; min-height:58px; border-bottom:1px solid #edf0ee; font-size:12px; }
			.saudi-self__row:last-child { border-bottom:0; }
			.saudi-self__row a { color:var(--green); font-weight:700; }
			.saudi-self__row span { color:var(--muted); }
			.saudi-self__status { display:inline-flex; align-items:center; min-height:26px; padding:3px 8px; color:#0b5d4b!important; background:#e5f3ed; border-radius:999px; font-size:10px; }
			.saudi-self__pay { display:grid; gap:10px; padding:15px; background:var(--paper); border-right:4px solid var(--sand); border-radius:8px; }
			.saudi-self__pay-line { display:flex; justify-content:space-between; gap:10px; color:var(--muted); font-size:12px; }
			.saudi-self__pay-line strong { color:var(--ink); }
			.saudi-self__pay-line--total { padding-top:9px; border-top:1px solid #d6d7cf; font-size:14px; }
			.saudi-self__team { display:grid; gap:8px; }
			.saudi-self__person { padding:10px 12px; background:#f8faf9; border:1px solid #e4e9e6; border-radius:8px; }
			.saudi-self__person strong { display:block; font-size:12px; }
			.saudi-self__person span { color:var(--muted); font-size:10px; }
			.saudi-self__privacy { padding:12px 15px; color:#475b53; background:#eef6f2; border:1px solid #cce0d7; border-radius:10px; font-size:11px; line-height:1.8; }
			.saudi-self__empty { padding:26px; color:var(--muted); text-align:center; }
			.saudi-self__unlinked { display:grid; justify-items:center; gap:12px; padding:44px 24px; background:#fff; border:1px solid var(--line); border-radius:14px; text-align:center; }
			.saudi-self__unlinked-mark { width:72px; height:72px; display:grid; place-items:center; color:#fff; background:var(--clay); border-radius:50%; font-size:26px; }
			.saudi-self__unlinked h1 { margin:0; font-size:21px; }
			.saudi-self__unlinked p { max-width:600px; margin:0; color:var(--muted); line-height:1.8; }
			.saudi-self__unlinked button { min-height:44px; padding:9px 16px; color:#fff; background:var(--green); border:0; border-radius:8px; }
			@media(max-width:950px) { .saudi-self__summary { grid-template-columns:repeat(3,1fr); } .saudi-self__metric:nth-child(3) { border-left:0; } .saudi-self__actions { grid-template-columns:repeat(3,1fr); } .saudi-self__grid { grid-template-columns:1fr; } }
			@media(max-width:620px) { .saudi-self { gap:12px; } .saudi-self__hero { grid-template-columns:1fr; padding:19px; } .saudi-self__identity { min-width:0; } .saudi-self__summary { grid-template-columns:repeat(2,1fr); } .saudi-self__metric, .saudi-self__metric:nth-child(3) { border-left:1px solid rgba(255,255,255,.12); } .saudi-self__metric:nth-child(even) { border-left:0; } .saudi-self__actions { grid-template-columns:repeat(2,1fr); } .saudi-self__action { min-height:54px; } .saudi-self__ack { grid-template-columns:1fr; } .saudi-self__ack button { width:100%; } .saudi-self__row { grid-template-columns:1fr auto; padding:10px 0; } .saudi-self__row span:nth-child(2) { grid-column:1; } }
			@media(prefers-reduced-motion:reduce) { .saudi-self * { transition:none!important; scroll-behavior:auto!important; } }
		`;
		document.head.appendChild(style);
	}

	renderLoading() {
		this.page.body.html(`<main class="saudi-self" dir="rtl" lang="ar" aria-busy="true"><section class="saudi-self__panel saudi-self__empty">جارٍ تجهيز ملفك وخدماتك…</section></main>`);
	}

	async load() {
		try {
			const response = await frappe.call({ method: "saudi_hr.saudi_hr.enterprise_operations.get_self_service_portal" });
			this.data = response.message || {};
			this.render();
		} catch (error) {
			this.page.body.html(`<main class="saudi-self" dir="rtl" lang="ar"><section class="saudi-self__unlinked"><span class="saudi-self__unlinked-mark">!</span><h1>تعذر تحميل البوابة</h1><p>تحقق من اتصال الخادم ثم أعد المحاولة. إذا استمرت المشكلة، تواصل مع مسؤول الموارد البشرية.</p><button data-retry>إعادة المحاولة</button></section></main>`);
			this.page.body.find("[data-retry]").on("click", () => this.load());
		}
	}

	render() {
		const d = this.data;
		if (!d.employee) return this.renderUnlinked(d);
		const e = d.employee;
		const s = d.summary || {};
		const preview = d.mode === "manager_preview" ? `<div class="saudi-self__preview"><span><strong>وضع المعاينة الإداري:</strong> لا يوجد موظف مربوط بحسابك، لذا تُعرض أول حالة متاحة للمعاينة فقط.</span><span class="saudi-self__status">لا تغييرات تلقائية</span></div>` : "";
		const actions = (d.quick_actions || []).map((action) => `<button class="saudi-self__action" data-route="${this.esc(action.route)}">${this.esc(action.label_ar)}</button>`).join("");
		const acknowledgements = (d.pending_acknowledgements || []).length ? d.pending_acknowledgements.map((item) => `<div class="saudi-self__ack"><div><strong>${this.esc(item.policy_title || item.policy_document)}</strong><p>الإصدار ${this.esc(item.policy_version || "—")} · الاستحقاق ${this.esc(item.due_date || "دون موعد")}</p></div><button data-ack="${this.esc(item.name)}">أقر بالاطلاع والفهم</button></div>`).join("") : `<div class="saudi-self__empty">لا توجد سياسات معلقة عليك الآن.</div>`;
		const requests = [
			...(d.annual_leave || []).map((row) => ({ name: row.name, label: "إجازة سنوية", meta: `${row.leave_start_date || ""} – ${row.leave_end_date || ""}`, status: row.workflow_state || row.status || "مسودة", route: `/app/saudi-annual-leave/${row.name}` })),
			...(d.sick_leave || []).map((row) => ({ name: row.name, label: "إجازة مرضية", meta: `${row.from_date || ""} – ${row.to_date || ""}`, status: Number(row.docstatus) === 1 ? "معتمدة" : "مسودة", route: `/app/saudi-sick-leave/${row.name}` })),
			...(d.overtime || []).map((row) => ({ name: row.name, label: "عمل إضافي", meta: row.date || "", status: row.approval_status || "مسودة", route: `/app/overtime-request/${row.name}` })),
		].slice(0, 10);
		const requestRows = requests.length ? requests.map((row) => `<div class="saudi-self__row"><a href="${this.esc(row.route)}">${this.esc(row.label)} · ${this.esc(row.name)}</a><span>${this.esc(row.meta)}</span><span class="saudi-self__status">${this.esc(row.status)}</span></div>`).join("") : `<div class="saudi-self__empty">لم تُسجل طلبات حديثة.</div>`;
		const pay = d.latest_payroll ? `<div class="saudi-self__pay"><div class="saudi-self__pay-line"><span>إجمالي الاستحقاق</span><strong>${this.money(d.latest_payroll.gross_salary)}</strong></div><div class="saudi-self__pay-line"><span>إجمالي الاستقطاعات</span><strong>${this.money(d.latest_payroll.total_deductions)}</strong></div><div class="saudi-self__pay-line saudi-self__pay-line--total"><span>صافي الراتب</span><strong>${this.money(d.latest_payroll.net_salary)}</strong></div></div>` : `<div class="saudi-self__empty">لا يوجد مسير راتب حديث متاح.</div>`;
		const team = (d.team || []).length ? `<div class="saudi-self__team">${d.team.map((person) => `<div class="saudi-self__person"><strong>${this.esc(person.employee_name)}</strong><span>${this.esc(person.designation || "دون مسمى")} · ${this.esc(person.department || "دون قسم")}</span></div>`).join("")}</div>` : `<div class="saudi-self__empty">لا يوجد فريق مباشر مرتبط بهذا السجل.</div>`;
		const managerPending = d.manager_pending || {};

		this.page.body.html(`<main class="saudi-self" dir="rtl" lang="ar" style="--green:${this.esc(d.branding?.brand_primary_color || "#0B5D4B")}">
			${preview}
			<section class="saudi-self__hero"><div><p class="saudi-self__eyebrow">ملفي اليوم · MY WORKDAY</p><h1>مرحباً ${this.esc(e.employee_name)}</h1><p>${this.esc(d.branding?.portal_welcome_ar || "كل ما تحتاجه للعمل والحقوق والطلبات في مسار واضح وآمن.")}</p></div><div class="saudi-self__identity"><strong>${this.esc(e.designation || "موظف")}</strong><span>${this.esc(e.company)}</span><span>${this.esc(e.department || "دون قسم")}</span></div></section>
			<section class="saudi-self__summary" aria-label="ملخص خدماتي"><div class="saudi-self__metric"><strong>${this.esc(s.pending_acknowledgements || 0)}</strong><span>إقرارات تنتظرني</span></div><div class="saudi-self__metric"><strong>${this.esc(s.recent_leave_requests || 0)}</strong><span>طلبات إجازة حديثة</span></div><div class="saudi-self__metric"><strong>${this.esc(s.recent_overtime_requests || 0)}</strong><span>طلبات إضافي حديثة</span></div><div class="saudi-self__metric"><strong>${this.esc(s.team_members || 0)}</strong><span>أعضاء الفريق المباشر</span></div><div class="saudi-self__metric"><strong>${this.esc(s.manager_pending || 0)}</strong><span>موافقات تنتظر المدير</span></div></section>
			<section aria-label="إجراءات سريعة" class="saudi-self__actions">${actions}</section>
			<section class="saudi-self__grid"><div class="saudi-self__panel"><div class="saudi-self__panel-head"><h2>سياسات تنتظر إقرارك</h2><span class="saudi-self__count">${this.esc((d.pending_acknowledgements || []).length)}</span></div>${acknowledgements}</div><div class="saudi-self__panel"><div class="saudi-self__panel-head"><h2>آخر صافي راتب</h2><span class="saudi-self__status">خاص</span></div>${pay}</div></section>
			<section class="saudi-self__grid"><div class="saudi-self__panel"><div class="saudi-self__panel-head"><h2>طلباتي الأخيرة</h2><span class="saudi-self__count">${this.esc(requests.length)}</span></div><div class="saudi-self__list">${requestRows}</div></div><div class="saudi-self__panel"><div class="saudi-self__panel-head"><h2>فريقي</h2><span class="saudi-self__status">${this.esc((managerPending.annual_leave || 0) + (managerPending.sick_leave || 0) + (managerPending.overtime || 0))} موافقات</span></div>${team}</div></section>
			<div class="saudi-self__privacy">${this.esc(d.privacy_notice_ar)}</div>
		</main>`);
		this.bind();
	}

	renderUnlinked(d) {
		this.page.body.html(`<main class="saudi-self" dir="rtl" lang="ar"><section class="saudi-self__unlinked"><span class="saudi-self__unlinked-mark">؟</span><h1>حسابك غير مربوط بملف موظف</h1><p>${this.esc(d.message_ar || "اطلب من الموارد البشرية ربط حسابك بملف الموظف.")}</p><button data-route="${this.esc(d.support_route || "/app/employee")}">فتح ملفات الموظفين</button></section></main>`);
		this.bind();
	}

	bind() {
		this.page.body.find("[data-route]").on("click", (event) => this.open(event.currentTarget.dataset.route));
		this.page.body.find("[data-ack]").on("click", (event) => this.acknowledge(event.currentTarget.dataset.ack));
	}

	open(route) {
		if (!route) return;
		if (route.startsWith("/app/")) frappe.set_route(route.replace(/^\/app\//, "").split("/"));
		else window.location.assign(route);
	}

	acknowledge(name) {
		frappe.prompt([{ fieldname: "consent", fieldtype: "Data", label: "اكتب: أقر بالاطلاع والفهم", reqd: 1, description: "سيُحفظ الوقت والمستخدم وبصمة إثبات غير قابلة للتعديل." }], async (values) => {
			try {
				const response = await frappe.call({ method: "saudi_hr.saudi_hr.enterprise_operations.acknowledge_policy", args: { acknowledgement_name: name, consent_text: values.consent }, freeze: true, freeze_message: "جارٍ تثبيت الإقرار…" });
				frappe.show_alert({ message: "تم تسجيل الإقرار الإلكتروني ببصمة إثبات.", indicator: "green" }, 6);
				this.load();
			} catch (error) {
				frappe.msgprint({ title: "لم يُسجل الإقرار", message: "اكتب عبارة الإقرار كما تظهر وتحقق أن السياسة مخصصة لسجلك.", indicator: "red" });
			}
		}, "إقرار إلكتروني", "تثبيت الإقرار");
	}
};
