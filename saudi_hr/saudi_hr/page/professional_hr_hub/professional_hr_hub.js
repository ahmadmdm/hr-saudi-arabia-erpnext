frappe.provide("saudi_hr");

frappe.pages["professional-hr-hub"].on_page_load = function (wrapper) {
	new saudi_hr.ProfessionalHrHub(wrapper);
};

saudi_hr.ProfessionalHrHub = class ProfessionalHrHub {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Professional HR Hub"),
			single_column: true,
		});
		this.ensureStyles();
		this.render();
		this.page.set_primary_action(__("Mobile Attendance"), () => this.open("/mobile-attendance"));
		this.page.add_menu_item(__("Saudi HR Workspace"), () => this.open("/app/saudi-hr"));
		this.page.add_menu_item(__("Saudi HR Settings"), () => this.open("/app/saudi-hr-settings/Saudi HR Settings"));
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
				padding: 8px 0 28px;
				color: #172b4d;
			}

			.professional-hr-hub__hero {
				display: grid;
				grid-template-columns: minmax(0, 1.5fr) minmax(280px, 0.8fr);
				gap: 14px;
				align-items: stretch;
			}

			.professional-hr-hub__panel,
			.professional-hr-hub__tile,
			.professional-hr-hub__route {
				background: #ffffff;
				border: 1px solid #dfe3eb;
				border-radius: 8px;
				box-shadow: 0 8px 24px rgba(23, 43, 77, 0.06);
			}

			.professional-hr-hub__panel {
				padding: 20px;
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
			.professional-hr-hub__muted {
				font-size: 13px;
				line-height: 1.65;
				color: #5e6c84;
				margin: 0;
			}

			.professional-hr-hub__actions,
			.professional-hr-hub__quick-grid,
			.professional-hr-hub__route-grid {
				display: grid;
				gap: 10px;
			}

			.professional-hr-hub__actions {
				grid-template-columns: repeat(2, minmax(0, 1fr));
				margin-top: 16px;
			}

			.professional-hr-hub__quick-grid {
				grid-template-columns: repeat(4, minmax(0, 1fr));
			}

			.professional-hr-hub__route-grid {
				grid-template-columns: repeat(3, minmax(0, 1fr));
			}

			.professional-hr-hub__button,
			.professional-hr-hub__tile,
			.professional-hr-hub__route {
				border: 1px solid #dfe3eb;
				border-radius: 8px;
				transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
			}

			.professional-hr-hub__button {
				min-height: 42px;
				display: inline-flex;
				align-items: center;
				justify-content: center;
				gap: 8px;
				padding: 9px 12px;
				font-size: 13px;
				font-weight: 700;
				color: #123326;
				background: #eef7f1;
				cursor: pointer;
			}

			.professional-hr-hub__button--dark {
				color: #ffffff;
				background: #1f6f4a;
				border-color: #1f6f4a;
			}

			.professional-hr-hub__tile,
			.professional-hr-hub__route {
				padding: 14px;
				cursor: pointer;
			}

			.professional-hr-hub__tile:hover,
			.professional-hr-hub__route:hover,
			.professional-hr-hub__button:hover {
				border-color: #1f6f4a;
				box-shadow: 0 10px 24px rgba(31, 111, 74, 0.12);
				transform: translateY(-1px);
			}

			.professional-hr-hub__tile-title,
			.professional-hr-hub__route-title {
				font-size: 14px;
				font-weight: 700;
				margin-bottom: 5px;
				color: #172b4d;
			}

			.professional-hr-hub__tile-note,
			.professional-hr-hub__route-note {
				font-size: 12px;
				line-height: 1.5;
				color: #5e6c84;
			}

			.professional-hr-hub__section-head {
				display: flex;
				justify-content: space-between;
				gap: 12px;
				align-items: end;
				margin-bottom: 10px;
			}

			.professional-hr-hub__section-title {
				font-size: 18px;
				font-weight: 700;
				margin: 0;
			}

			.professional-hr-hub__metric {
				display: grid;
				gap: 10px;
			}

			.professional-hr-hub__metric-row {
				display: flex;
				justify-content: space-between;
				gap: 12px;
				padding-bottom: 10px;
				border-bottom: 1px solid #ebedf2;
			}

			.professional-hr-hub__metric-row:last-child {
				border-bottom: 0;
				padding-bottom: 0;
			}

			.professional-hr-hub__metric-label {
				font-size: 12px;
				color: #5e6c84;
			}

			.professional-hr-hub__metric-value {
				font-size: 13px;
				font-weight: 700;
				text-align: end;
			}

			@media (max-width: 992px) {
				.professional-hr-hub__hero,
				.professional-hr-hub__quick-grid,
				.professional-hr-hub__route-grid {
					grid-template-columns: 1fr;
				}
			}

			@media (max-width: 640px) {
				.professional-hr-hub__actions {
					grid-template-columns: 1fr;
				}

				.professional-hr-hub__title {
					font-size: 22px;
				}
			}
		`;
		document.head.appendChild(style);
	}

	render() {
		this.page.body.html(`
			<div class="professional-hr-hub">
				<section class="professional-hr-hub__hero">
					<div class="professional-hr-hub__panel">
						<div class="professional-hr-hub__eyebrow">Saudi HR</div>
						<h2 class="professional-hr-hub__title">${__("Professional HR Hub")}</h2>
						<p class="professional-hr-hub__subtitle">${__("A focused operating surface for attendance, employee actions, payroll, compliance, and Saudi labor governance without using the default ERPNext module layout.")}</p>
						<div class="professional-hr-hub__actions" data-primary-actions></div>
					</div>
					<div class="professional-hr-hub__panel">
						<div class="professional-hr-hub__section-head">
							<h3 class="professional-hr-hub__section-title">${__("Today")}</h3>
						</div>
						<div class="professional-hr-hub__metric" data-metrics></div>
					</div>
				</section>

				<section class="professional-hr-hub__panel">
					<div class="professional-hr-hub__section-head">
						<h3 class="professional-hr-hub__section-title">${__("Fast Work Queue")}</h3>
						<p class="professional-hr-hub__muted">${__("Daily operations first, setup only when needed.")}</p>
					</div>
					<div class="professional-hr-hub__quick-grid" data-fast-queue></div>
				</section>

				<section class="professional-hr-hub__panel">
					<div class="professional-hr-hub__section-head">
						<h3 class="professional-hr-hub__section-title">${__("Operating Routes")}</h3>
						<p class="professional-hr-hub__muted">${__("Structured paths for HR teams who want a curated Saudi HR system view.")}</p>
					</div>
					<div class="professional-hr-hub__route-grid" data-routes></div>
				</section>
			</div>
		`);

		this.renderPrimaryActions();
		this.renderMetrics();
		this.renderFastQueue();
		this.renderRoutes();
	}

	renderPrimaryActions() {
		this.page.body.find("[data-primary-actions]").html(
			this.getPrimaryActions().map((action) => `
				<button class="professional-hr-hub__button ${action.dark ? "professional-hr-hub__button--dark" : ""}" data-route="${frappe.utils.escape_html(action.route)}">
					${frappe.utils.escape_html(__(action.label))}
				</button>
			`).join(""),
		);

		this.page.body.find("[data-primary-actions] [data-route]").on("click", (event) => {
			this.open(event.currentTarget.dataset.route);
		});
	}

	renderMetrics() {
		this.page.body.find("[data-metrics]").html(
			this.getMetrics().map((metric) => `
				<div class="professional-hr-hub__metric-row">
					<div class="professional-hr-hub__metric-label">${frappe.utils.escape_html(__(metric.label))}</div>
					<div class="professional-hr-hub__metric-value">${frappe.utils.escape_html(__(metric.value))}</div>
				</div>
			`).join(""),
		);
	}

	renderFastQueue() {
		this.renderCollection("[data-fast-queue]", this.getFastQueue(), "tile");
	}

	renderRoutes() {
		this.renderCollection("[data-routes]", this.getRoutes(), "route");
	}

	renderCollection(selector, items, variant) {
		this.page.body.find(selector).html(
			items.map((item) => `
				<div class="professional-hr-hub__${variant}" data-route="${frappe.utils.escape_html(item.route)}">
					<div class="professional-hr-hub__${variant}-title">${frappe.utils.escape_html(__(item.title))}</div>
					<div class="professional-hr-hub__${variant}-note">${frappe.utils.escape_html(__(item.note))}</div>
				</div>
			`).join(""),
		);

		this.page.body.find(`${selector} [data-route]`).on("click", (event) => {
			this.open(event.currentTarget.dataset.route);
		});
	}

	getPrimaryActions() {
		return [
			{ label: "Mobile Attendance", route: "/mobile-attendance", dark: true },
			{ label: "Attendance Action Hub", route: "/app/attendance-action-hub" },
			{ label: "Team Attendance Review", route: "/app/query-report/Team Attendance Review" },
			{ label: "Saudi HR Settings", route: "/app/saudi-hr-settings/Saudi HR Settings" },
		];
	}

	getMetrics() {
		return [
			{ label: "Voice Mode", value: "Challenge Only" },
			{ label: "Primary Flow", value: "Attendance -> Payroll -> Compliance" },
			{ label: "Workspace", value: "Curated Saudi HR" },
			{ label: "Default ERPNext", value: "Available when needed" },
		];
	}

	getFastQueue() {
		return [
			{ title: "Attendance Command", note: "Check-ins, anomalies, daily follow-up.", route: "/app/attendance-action-hub" },
			{ title: "Mobile Attendance", note: "GPS and challenge-based voice attendance.", route: "/mobile-attendance" },
			{ title: "Saudi Annual Leave", note: "Annual leave requests and approvals.", route: "/app/saudi-annual-leave" },
			{ title: "Saudi Monthly Payroll", note: "Monthly payroll processing and deductions.", route: "/app/saudi-monthly-payroll" },
			{ title: "WPS Tracker", note: "Payroll submission follow-up.", route: "/app/query-report/WPS Submission Tracker" },
			{ title: "Employee Org Tree", note: "Departments, managers, and scope.", route: "/app/employee-org-tree" },
			{ title: "Iqama and Work Permits", note: "Residency and work permit expiry control.", route: "/app/work-permit-iqama" },
			{ title: "Legal Reference Matrix", note: "Saudi labor law governance library.", route: "/app/legal-reference-matrix" },
		];
	}

	getRoutes() {
		return [
			{ title: "Employee Lifecycle", note: "Hiring, onboarding, contracts, performance, transfers, exits.", route: "/app/employee-onboarding" },
			{ title: "Time, Leave, Payroll", note: "Attendance, leaves, overtime, loans, payroll, WPS.", route: "/app/saudi-monthly-payroll" },
			{ title: "Compliance and Legal", note: "Investigations, grievances, policies, inspections, Nitaqat.", route: "/app/legal-reference-matrix" },
			{ title: "Location and Voice", note: "Attendance locations, shift assignment, challenge-only voice settings.", route: "/app/attendance-location" },
			{ title: "Reports", note: "Operational reports without browsing ERPNext modules.", route: "/app/query-report/Team Attendance Review" },
			{ title: "System Setup", note: "Saudi HR rates, alerts, branch imports, and workflow controls.", route: "/app/saudi-hr-settings/Saudi HR Settings" },
		];
	}

	open(route) {
		if (route.startsWith("/")) {
			window.location.href = route;
			return;
		}
		frappe.set_route(route);
	}
};