frappe.provide("saudi_hr");

frappe.pages["professional-hr-hub"].on_page_load = function (wrapper) {
	new saudi_hr.ProfessionalHrHub(wrapper);
};

saudi_hr.ProfessionalHrHub = class ProfessionalHrHub {
	constructor(wrapper) {
		this.wrapper = wrapper;
		// Saudi HR is deliberately Arabic-first; English remains supporting copy.
		this.isArabic = true;
		this.catalog = { categories: [], features: [] };
		this.activeCategory = "all";
		this.searchText = "";
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: this.isArabic ? "مركز الموارد البشرية الاحترافي" : __("Professional HR Hub"),
			single_column: true,
		});
		this.ensureStyles();
		this.renderShell();
		this.loadCatalog();
		this.page.set_primary_action(this.isArabic ? "افتح مركز القيادة" : __("Open Command Center"), () => this.open("/app/saudi-compliance-command-center"));
		this.page.add_menu_item(this.isArabic ? "الحضور عبر الجوال" : __("Mobile Attendance"), () => this.open("/mobile-attendance"));
		this.page.add_menu_item("مساحة عمل Saudi HR", () => this.open("/app/saudi-hr"));
		this.page.add_menu_item("إعدادات Saudi HR", () => this.open("/app/saudi-hr-settings/Saudi HR Settings"));
	}

	ensureStyles() {
		if (document.getElementById("professional-hr-hub-style")) {
			return;
		}

		const style = document.createElement("style");
		style.id = "professional-hr-hub-style";
		style.textContent = `
			.professional-hr-hub {
				display: grid;
				gap: 18px;
				padding: 8px 0 30px;
				color: #0f172a;
				font-family: "Noto Sans Arabic", "Tajawal", var(--font-stack);
			}

			.professional-hr-hub[dir="rtl"] { text-align: right; }

			.professional-hr-hub[dir="rtl"] .professional-hr-hub__secondary {
				direction: ltr;
				text-align: right;
				unicode-bidi: plaintext;
			}

			.professional-hr-hub__panel,
			.professional-hr-hub__feature,
			.professional-hr-hub__category {
				background: #ffffff;
				border: 1px solid #cbd5e1;
				border-radius: 10px;
				box-shadow: 0 8px 24px rgba(23, 43, 77, 0.06);
			}

			.professional-hr-hub__panel {
				padding: 20px;
			}

			.professional-hr-hub__hero {
				display: grid;
				grid-template-columns: minmax(0, 1.35fr) minmax(300px, 0.65fr);
				gap: 14px;
			}

			.professional-hr-hub__eyebrow {
				font-size: 12px;
				font-weight: 700;
				text-transform: uppercase;
				color: #216e4e;
				margin-bottom: 8px;
			}

			.professional-hr-hub__title {
				font-size: 26px;
				font-weight: 700;
				line-height: 1.25;
				margin: 0 0 8px;
			}

			.professional-hr-hub__subtitle,
			.professional-hr-hub__muted,
			.professional-hr-hub__feature-note,
			.professional-hr-hub__category-note {
				font-size: 13px;
				line-height: 1.6;
				color: #5e6c84;
				margin: 0;
			}

			.professional-hr-hub__stats {
				display: grid;
				gap: 10px;
			}

			.professional-hr-hub__stat {
				display: flex;
				justify-content: space-between;
				gap: 12px;
				padding-bottom: 10px;
				border-bottom: 1px solid #ebedf2;
			}

			.professional-hr-hub__stat:last-child {
				border-bottom: 0;
				padding-bottom: 0;
			}

			.professional-hr-hub__stat-label {
				font-size: 12px;
				color: #5e6c84;
			}

			.professional-hr-hub__stat-value {
				font-size: 14px;
				font-weight: 700;
				text-align: end;
			}

			.professional-hr-hub__toolbar {
				display: grid;
				grid-template-columns: minmax(260px, 1fr) auto;
				gap: 10px;
				align-items: center;
			}

			.professional-hr-hub__search {
				width: 100%;
				min-height: 40px;
				border: 1px solid #dfe3eb;
				border-radius: 10px;
				padding: 9px 12px;
				font-size: 13px;
				background: #f7f9fb;
			}

			.professional-hr-hub__button {
				min-height: 40px;
				display: inline-flex;
				align-items: center;
				justify-content: center;
				padding: 9px 12px;
				border: 1px solid #1f6f4a;
				border-radius: 8px;
				font-size: 13px;
				font-weight: 700;
				color: #ffffff;
				background: #1f6f4a;
				cursor: pointer;
			}

			.professional-hr-hub button:focus-visible,
			.professional-hr-hub input:focus-visible {
				outline: 3px solid #38bdf8;
				outline-offset: 2px;
			}

			.professional-hr-hub__category-grid,
			.professional-hr-hub__feature-grid {
				display: grid;
				gap: 10px;
			}

			.professional-hr-hub__category-grid {
				grid-template-columns: repeat(4, minmax(0, 1fr));
			}

			.professional-hr-hub__feature-grid {
				grid-template-columns: repeat(3, minmax(0, 1fr));
			}

			.professional-hr-hub__category,
			.professional-hr-hub__feature {
				transition: border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
			}

			.professional-hr-hub__category {
				padding: 13px;
				cursor: pointer;
			}

			.professional-hr-hub__feature {
				display: grid;
				gap: 10px;
				min-height: 170px;
				padding: 14px;
			}

			.professional-hr-hub__category.is-active,
			.professional-hr-hub__category:hover,
			.professional-hr-hub__feature:hover {
				border-color: #1f6f4a;
				box-shadow: 0 10px 24px rgba(31, 111, 74, 0.12);
				transform: translateY(-1px);
			}

			.professional-hr-hub__category-title,
			.professional-hr-hub__feature-title {
				font-size: 14px;
				font-weight: 700;
				margin-bottom: 5px;
				color: #172b4d;
			}

			.professional-hr-hub__feature-meta,
			.professional-hr-hub__feature-actions {
				display: flex;
				gap: 8px;
				align-items: center;
			}

			.professional-hr-hub__feature-meta {
				justify-content: space-between;
			}

			.professional-hr-hub__feature-actions {
				margin-top: auto;
			}

			.professional-hr-hub__badge {
				display: inline-flex;
				align-items: center;
				min-height: 22px;
				padding: 3px 8px;
				border-radius: 999px;
				font-size: 11px;
				font-weight: 700;
				background: #eef7f1;
				color: #216e4e;
			}

			.professional-hr-hub__link {
				border: 0;
				background: transparent;
				padding: 0;
				font-size: 12px;
				font-weight: 700;
				color: #1f6f4a;
				cursor: pointer;
			}

			.professional-hr-hub__empty {
				padding: 22px;
				text-align: center;
				border: 1px dashed #c9d1dd;
				border-radius: 8px;
				color: #5e6c84;
			}

			@media (max-width: 1100px) {
				.professional-hr-hub__category-grid,
				.professional-hr-hub__feature-grid {
					grid-template-columns: repeat(2, minmax(0, 1fr));
				}
			}

			@media (max-width: 760px) {
				.professional-hr-hub__hero,
				.professional-hr-hub__toolbar,
				.professional-hr-hub__category-grid,
				.professional-hr-hub__feature-grid {
					grid-template-columns: 1fr;
				}

				.professional-hr-hub__title {
					font-size: 22px;
				}
			}

			@media (prefers-reduced-motion: reduce) {
				.professional-hr-hub * { transition: none !important; animation: none !important; }
			}
		`;
		document.head.appendChild(style);
	}

	renderShell() {
		this.page.body.html(`
			<div class="professional-hr-hub" dir="rtl" lang="ar">
				<section class="professional-hr-hub__hero">
					<div class="professional-hr-hub__panel">
						<div class="professional-hr-hub__eyebrow">SAUDI HR · الموارد البشرية السعودية</div>
						<h2 class="professional-hr-hub__title">${this.isArabic ? "مركز الموارد البشرية الاحترافي" : __("Professional HR Hub")}</h2>
						<p class="professional-hr-hub__subtitle">${this.isArabic ? "دليل تشغيلي موحّد يربط رحلات الموظفين والرواتب والامتثال بالأدلة والإجراءات المطلوبة." : __("A complete Saudi HR operating catalog with dedicated professional pages for every feature, while the default ERPNext screens remain available when needed.")}</p>
					</div>
					<div class="professional-hr-hub__panel">
						<div class="professional-hr-hub__eyebrow">التغطية التشغيلية</div>
						<div class="professional-hr-hub__stats" data-stats></div>
					</div>
				</section>

				<section class="professional-hr-hub__panel">
					<div class="professional-hr-hub__toolbar">
						<label class="sr-only" for="saudi-hr-feature-search">${this.isArabic ? "ابحث في خدمات الموارد البشرية" : __("Search HR services")}</label>
						<input id="saudi-hr-feature-search" class="professional-hr-hub__search" data-search placeholder="${frappe.utils.escape_html(this.isArabic ? "ابحث عن خدمة أو تقرير أو إجراء…" : __("Search features, reports, workflows, leave, payroll, compliance..."))}">
						<button class="professional-hr-hub__button" data-route="/app/saudi-compliance-command-center">${this.isArabic ? "مركز القيادة" : __("Command Center")}</button>
					</div>
				</section>

				<section class="professional-hr-hub__panel" data-category-panel>
					<div class="professional-hr-hub__category-grid" data-categories></div>
				</section>

				<section class="professional-hr-hub__panel">
					<div class="professional-hr-hub__feature-grid" data-features></div>
				</section>
			</div>
		`);

		this.page.body.find("[data-search]").on("input", (event) => {
			this.searchText = this.normalizeSearchText(event.currentTarget.value);
			this.page.body.find("[data-category-panel]").toggle(!this.searchText);
			this.renderFeatures();
		});

		this.page.body.find("[data-route]").on("click", (event) => {
			this.open(event.currentTarget.dataset.route);
		});
	}

	loadCatalog() {
		this.page.body.find("[data-features]").html(`<div class="professional-hr-hub__empty">جارٍ تحميل خدمات الموارد البشرية السعودية…</div>`);
		frappe.call({
			method: "saudi_hr.saudi_hr.professional_hr_catalog.get_professional_hr_catalog",
			callback: (response) => {
				this.catalog = response.message || { categories: [], features: [] };
				this.cacheCatalog();
				this.renderStats();
				this.renderCategories();
				this.renderFeatures();
			},
			error: () => {
				this.page.body.find("[data-features]").html(`<div class="professional-hr-hub__empty">تعذر تحميل دليل الخدمات. أعد المحاولة أو افتح مركز القيادة.</div>`);
			},
		});
	}

	cacheCatalog() {
		try {
			localStorage.setItem("professional_hr_catalog", JSON.stringify(this.catalog));
		} catch (error) {
		}
	}

	renderStats() {
		const stats = [
			{ label: this.isArabic ? "الخدمات والصفحات" : "Feature Pages", value: this.catalog.total_features || this.catalog.features.length },
			{ label: this.isArabic ? "مجالات التشغيل" : "Operating Areas", value: this.catalog.categories.length },
			{ label: this.isArabic ? "الإجراءات الرئيسية" : "Primary Actions", value: this.catalog.primary_features || 0 },
			{ label: this.isArabic ? "النمط" : "Navigation", value: this.isArabic ? "عربي أولاً · ERPNext متاح" : "Custom first, ERPNext ready" },
		];

		this.page.body.find("[data-stats]").html(stats.map((stat) => `
			<div class="professional-hr-hub__stat">
				<div class="professional-hr-hub__stat-label">${frappe.utils.escape_html(__(stat.label))}</div>
				<div class="professional-hr-hub__stat-value">${frappe.utils.escape_html(__(String(stat.value)))}</div>
			</div>
		`).join(""));
	}

	renderCategories() {
		const categories = [{ id: "all", title: "All Features", title_ar: "كل الخدمات", count: this.catalog.features.length }, ...this.catalog.categories];
		this.page.body.find("[data-categories]").html(categories.map((category) => `
			<div class="professional-hr-hub__category ${this.activeCategory === category.id ? "is-active" : ""}" data-category="${frappe.utils.escape_html(category.id)}">
				<div class="professional-hr-hub__category-title">${frappe.utils.escape_html(this.isArabic ? category.title_ar : __(category.title))}</div>
				<p class="professional-hr-hub__category-note professional-hr-hub__secondary" lang="en">${frappe.utils.escape_html(category.title || "")}</p>
				<span class="professional-hr-hub__badge">${frappe.utils.escape_html(String(category.count || 0))}</span>
			</div>
		`).join(""));

		this.page.body.find("[data-category]").on("click", (event) => {
			this.activeCategory = event.currentTarget.dataset.category;
			this.renderCategories();
			this.renderFeatures();
		});
	}

	renderFeatures() {
		const filtered = this.catalog.features.filter((feature) => {
			const categoryMatch = this.activeCategory === "all" || feature.category === this.activeCategory;
			const haystack = this.normalizeSearchText(
				[feature.title, feature.title_ar, feature.summary, feature.summary_ar, feature.target_type, feature.target].join(" ")
			);
			const queryTokens = this.searchText.split(" ").filter(Boolean);
			return categoryMatch && queryTokens.every((token) => haystack.includes(token));
		});

		if (!filtered.length) {
			this.page.body.find("[data-features]").html(`<div class="professional-hr-hub__empty">لا توجد خدمات مطابقة. غيّر عبارة البحث أو اختر «كل الخدمات».</div>`);
			return;
		}

		this.page.body.find("[data-features]").html(filtered.map((feature) => `
			<article class="professional-hr-hub__feature">
				<div class="professional-hr-hub__feature-meta">
					<span class="professional-hr-hub__badge">${frappe.utils.escape_html(this.arabicType(feature.target_type))}</span>
					${feature.priority ? `<span class="professional-hr-hub__badge">${frappe.utils.escape_html(this.arabicPriority(feature.priority))}</span>` : ""}
				</div>
				<div>
					<div class="professional-hr-hub__feature-title">${frappe.utils.escape_html(this.isArabic ? feature.title_ar : __(feature.title))}</div>
					<p class="professional-hr-hub__feature-note professional-hr-hub__secondary" lang="en">${frappe.utils.escape_html(feature.title || "")}</p>
				</div>
				<p class="professional-hr-hub__feature-note">${frappe.utils.escape_html(this.isArabic ? feature.summary_ar : __(feature.summary))}</p>
				<div class="professional-hr-hub__feature-actions">
					<button class="professional-hr-hub__link" data-feature-id="${frappe.utils.escape_html(feature.id)}">${this.isArabic ? "افتح صفحة الخدمة" : __("Open Feature Page")}</button>
					<button class="professional-hr-hub__link" data-route="${frappe.utils.escape_html(feature.route)}">${frappe.utils.escape_html(this.isArabic ? "افتح السجل" : __(feature.action_label || "ERPNext View"))}</button>
				</div>
			</article>
		`).join(""));

		this.page.body.find("[data-feature-id]").on("click", (event) => this.openFeature(event.currentTarget.dataset.featureId));
		this.page.body.find("[data-route]").on("click", (event) => this.open(event.currentTarget.dataset.route));
	}

	openFeature(featureId) {
		const feature = this.catalog.features.find((item) => item.id === featureId);
		if (feature) {
			try {
				localStorage.setItem("professional_hr_selected_feature_id", featureId);
			} catch (error) {
			}
			this.open(feature.detail_route);
		}
	}

	arabicType(value) {
		return ({ DocType: "سجل", Page: "صفحة", Report: "تقرير", URL: "رابط" })[value] || value || "خدمة";
	}

	arabicPriority(value) {
		return ({ Primary: "رئيسي" })[value] || value || "";
	}

	normalizeSearchText(value) {
		return String(value || "")
			.normalize("NFKD")
			.toLowerCase()
			.replace(/[\u064b-\u065f\u0670\u0640]/g, "")
			.replace(/[أإآ]/g, "ا")
			.replace(/ى/g, "ي")
			.replace(/ة/g, "ه")
			.replace(/[^\p{L}\p{N}]+/gu, " ")
			.trim()
			.split(/\s+/)
			.map((token) => (token.startsWith("ال") && token.length > 4 ? token.slice(2) : token))
			.join(" ");
	}

	open(route) {
		if (route.startsWith("/app/")) {
			frappe.set_route(route.slice(5).split("/"));
			return;
		}
		if (route.startsWith("/")) {
			window.location.href = route;
			return;
		}
		frappe.set_route(route);
	}
};
