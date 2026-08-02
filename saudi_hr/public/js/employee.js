const SAUDI_EMPLOYEE_PROFILE_METHOD =
	"saudi_hr.saudi_hr.employee_profile.get_employee_profile";
const SAUDI_EMPLOYEE_PRINT_FORMAT = "Employee Complete File AR";

frappe.ui.form.on("Employee", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		add_employee_complete_file_button(frm);
		render_saudi_employee_profile(frm);
	},
});

function add_employee_complete_file_button(frm) {
	frm.add_custom_button(
		__("Employee 360"),
		() => open_employee_360(frm),
		__("Saudi HR")
	);
	frm.add_custom_button(
		__("Complete Employee File"),
		() => open_employee_complete_file(frm.doc.name),
		__("Saudi HR")
	);
}

function open_employee_360(frm) {
	const $pane = frm.dashboard.parent.closest(".tab-pane");
	const paneId = $pane.attr("id");
	if (paneId) {
		const $tab = frm.layout.wrapper.find(".form-tabs .nav-link").filter(function () {
			return (
				$(this).attr("href") === `#${paneId}` ||
				$(this).attr("data-bs-target") === `#${paneId}`
			);
		});
		if ($tab.length === 1) {
			$tab.trigger("click");
		}
	}

	window.setTimeout(() => {
		const section = frm.dashboard.parent.find(".shr-employee-360-section")[0];
		if (section) {
			const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
			section.scrollIntoView({
				behavior: reducedMotion ? "auto" : "smooth",
				block: "start",
			});
		}
	}, 80);
}

function render_saudi_employee_profile(frm) {
	const employee = frm.doc.name;
	const $section = make_employee_profile_section(frm);
	$section.html(build_employee_profile_loading_html());

	frappe.call({
		method: SAUDI_EMPLOYEE_PROFILE_METHOD,
		args: { employee },
		callback: ({ message }) => {
			if (frm.doc.name !== employee) {
				return;
			}

			const profile = message || {};
			frm.__saudi_employee_profile = profile;
			$section.html(build_employee_profile_html(profile));
			bind_employee_profile_actions(frm, $section, profile);
			render_paid_payroll_history(frm, profile.currency);
		},
		error: () => {
			if (frm.doc.name !== employee) {
				return;
			}

			$section.html(build_employee_profile_error_html());
			render_paid_payroll_history(frm);
		},
	});
}

function make_employee_profile_section(frm) {
	frm.dashboard.parent.find(".shr-employee-360-section").remove();
	const $section = frm.dashboard.add_section(
		'<div class="shr-employee-360"></div>',
		__("Saudi Employee 360"),
		"shr-employee-360-section"
	);
	frm.dashboard.show();
	return $section;
}

function build_employee_profile_loading_html() {
	return `
		<div class="shr-employee-360">
			<div class="shr-employee-360__loading" role="status" aria-live="polite">
				<div class="shr-employee-360__loading-mark" aria-hidden="true"></div>
				<div class="shr-employee-360__loading-lines">
					<div class="shr-employee-360__loading-line"></div>
					<div class="shr-employee-360__loading-line"></div>
					<span class="sr-only">${__("Loading comprehensive employee file...")}</span>
				</div>
			</div>
		</div>`;
}

function build_employee_profile_error_html() {
	return `
		<div class="shr-employee-360">
			<div class="shr-employee-360__error" role="alert">
				<strong>${__("The comprehensive employee file could not be loaded.")}</strong>
				<span>${__("Refresh the page or verify that your role can read this employee's records.")}</span>
			</div>
		</div>`;
}

function build_employee_profile_html(profile) {
	const employee = profile.employee || {};
	const readiness = profile.readiness || {};
	const attendance = profile.attendance || {};
	const attendanceMonth = attendance.month || {};
	const leave = profile.leave || {};
	const contract = profile.contract || {};
	const score = clamp_number(readiness.score, 0, 100);
	const attention = Array.isArray(readiness.attention) ? readiness.attention : [];
	const state = get_readiness_state(readiness.state);
	const identityParts = [employee.designation, employee.department, employee.branch]
		.filter(Boolean)
		.map(escape_html);
	const employmentFacts = [
		profile.nationality,
		employee.date_of_joining
			? __("Joined {0}", [format_date(employee.date_of_joining)])
			: null,
	]
		.filter(Boolean)
		.map(escape_html);
	const managerLine = profile.manager_name
		? __("Reports to {0}", [escape_html(profile.manager_name)])
		: __("No reporting manager assigned");

	const contractMetric = get_contract_metric(contract);
	const leaveMetric = {
		label: __("Annual leave balance"),
		value: `${format_number(leave.balance || 0)} ${__("days")}`,
		note: leave.policy_name || __("No leave policy assigned"),
	};
	const attendanceMetric = {
		label: __("Attendance this month"),
		value: `${format_number(attendanceMonth.working_hours || 0)} ${__("hours")}`,
		note: __("{0} recorded days · {1} late days", [
			format_number(attendanceMonth.days || 0),
			format_number(attendanceMonth.late_days || 0),
		]),
	};
	const actionMetric = {
		label: __("Priority actions"),
		value: format_number(attention.length),
		note: attention.length
			? __("Review the action ledger")
			: __("The operational file is complete"),
	};

	return `
		<div class="shr-employee-360" data-schema="${escape_html(profile.schema_version || "")}">
			<section class="shr-employee-360__hero" aria-labelledby="shr-employee-name">
				<div class="shr-employee-360__identity">
					<div class="shr-employee-360__monogram" aria-hidden="true">
						${escape_html(get_initials(employee.employee_name || employee.name))}
					</div>
					<div>
						<div class="shr-employee-360__eyebrow">${__("Comprehensive employee file")}</div>
						<h3 class="shr-employee-360__name" id="shr-employee-name">
							${escape_html(employee.employee_name || employee.name || __("Employee"))}
						</h3>
						<div class="shr-employee-360__identity-line">
							${identityParts.length ? identityParts.map((part) => `<span>${part}</span>`).join("") : `<span>${__("Employment details need completion")}</span>`}
						</div>
						<div class="shr-employee-360__identity-line">
							<span>${escape_html(employee.name || "-")}</span>
							<span>${managerLine}</span>
						</div>
						${
							employmentFacts.length
								? `<div class="shr-employee-360__identity-line">${employmentFacts
										.map((part) => `<span>${part}</span>`)
										.join("")}</div>`
								: ""
						}
					</div>
				</div>
				<div class="shr-employee-360__compass" aria-label="${escape_html(
					__("File readiness: {0} percent", [score])
				)}">
					<div class="shr-employee-360__ring" style="--shr-score: ${score * 3.6}deg;">
						<div class="shr-employee-360__score">${score}<small>%</small></div>
					</div>
					<div class="shr-employee-360__readiness-copy">
						<div class="shr-employee-360__readiness-label">${__("File readiness")}</div>
						<div class="shr-employee-360__readiness-state">${state.label}</div>
						<div class="shr-employee-360__readiness-detail">
							${__("{0} of {1} operational checks complete", [
								readiness.completed || 0,
								readiness.total || 0,
							])}
						</div>
					</div>
				</div>
			</section>

			<div class="shr-employee-360__metric-strip">
				${build_metric_html(contractMetric)}
				${build_metric_html(leaveMetric)}
				${build_metric_html(attendanceMetric)}
				${build_metric_html(actionMetric)}
			</div>

			<div class="shr-employee-360__body">
				<section class="shr-employee-360__panel" aria-labelledby="shr-operational-timeline">
					<div class="shr-employee-360__panel-head">
						<div>
							<h4 class="shr-employee-360__panel-title" id="shr-operational-timeline">
								${__("Operational snapshot")}
							</h4>
							<div class="shr-employee-360__panel-kicker">
								${__("Contract, attendance, payroll and access in one view")}
							</div>
						</div>
						<span class="shr-employee-360__badge">${escape_html(employee.status || "-")}</span>
					</div>
					<div class="shr-employee-360__timeline">
						${build_operational_events(profile)}
					</div>
				</section>

				<section class="shr-employee-360__panel shr-employee-360__panel--attention" aria-labelledby="shr-action-ledger">
					<div class="shr-employee-360__panel-head">
						<div>
							<h4 class="shr-employee-360__panel-title" id="shr-action-ledger">
								${__("Next-action ledger")}
							</h4>
							<div class="shr-employee-360__panel-kicker">
								${__("Prioritized from the employee's live records")}
							</div>
						</div>
						<span class="shr-employee-360__badge ${
							attention.length ? "shr-employee-360__badge--warning" : ""
						}">${format_number(attention.length)}</span>
					</div>
					<div class="shr-employee-360__actions">
						${build_attention_html(attention)}
					</div>
					<div class="shr-employee-360__quick">
						${build_quick_actions_html(profile)}
					</div>
					<div class="shr-employee-360__notice">
						${escape_html(readiness.notice || "")}
					</div>
				</section>
			</div>
		</div>`;
}

function build_metric_html(metric) {
	return `
		<div class="shr-employee-360__metric">
			<div class="shr-employee-360__metric-label">${escape_html(metric.label || "-")}</div>
			<div class="shr-employee-360__metric-value">${escape_html(metric.value || "-")}</div>
			<div class="shr-employee-360__metric-note" title="${escape_html(metric.note || "-")}">
				${escape_html(metric.note || "-")}
			</div>
		</div>`;
}

function get_contract_metric(contract) {
	if (!contract || !contract.name) {
		return {
			label: __("Contract horizon"),
			value: __("Not available"),
			note: __("Create or link an employment contract"),
		};
	}

	const remaining = contract.days_remaining;
	let value = __("Open ended");
	if (remaining !== null && remaining !== undefined) {
		value =
			remaining < 0
				? __("Expired")
				: __("{0} days", [format_number(remaining)]);
	}

	return {
		label: __("Contract horizon"),
		value,
		note: contract.contract_status || contract.contract_type || contract.name,
	};
}

function build_operational_events(profile) {
	const employee = profile.employee || {};
	const contract = profile.contract || {};
	const attendance = profile.attendance || {};
	const today = attendance.today || {};
	const lastCheckin = attendance.last_checkin || {};
	const payroll = profile.payroll || {};
	const currency = payroll.currency || profile.currency || "SAR";
	const counts = profile.counts || {};
	const events = [];

	events.push({
		title: __("Employment contract"),
		detail: contract.name
			? [contract.contract_type, contract.contract_status].filter(Boolean).join(" · ")
			: __("No visible contract record"),
		value: contract.end_date ? format_date(contract.end_date) : __("Open ended"),
		active: Boolean(contract.name),
	});

	events.push({
		title: __("Today's attendance"),
		detail: today.name
			? [today.status, __("{0} working hours", [format_number(today.working_hours || 0)])]
					.filter(Boolean)
					.join(" · ")
			: lastCheckin.time
				? __("Last movement: {0}", [lastCheckin.log_type || "-"])
				: __("No attendance movement recorded today"),
		value: today.out_time
			? format_time(today.out_time)
			: lastCheckin.time
				? format_time(lastCheckin.time)
				: "-",
		active: Boolean(today.name || lastCheckin.time),
	});

	events.push({
		title: __("Latest paid payroll"),
		detail: payroll.name
			? payroll.period_label || payroll.name
			: profile.visibility && profile.visibility.payroll
				? __("No paid payroll record")
				: __("Hidden by your payroll permissions"),
		value: payroll.name ? format_money(payroll.net_salary, currency) : "-",
		active: Boolean(payroll.name),
	});

	events.push({
		title: __("Access and records"),
		detail: employee.user_id
			? __("Linked to {0}", [employee.user_id])
			: __("No system user linked"),
		value:
			profile.visibility && profile.visibility.documents
				? __("{0} held documents", [format_number(counts.document_custody || 0)])
				: __("Documents hidden"),
		active: Boolean(employee.user_id),
	});

	return events
		.map(
			(event) => `
			<div class="shr-employee-360__event">
				<span class="shr-employee-360__event-dot ${
					event.active ? "" : "shr-employee-360__event-dot--muted"
				}" aria-hidden="true"></span>
				<div>
					<div class="shr-employee-360__event-title">${escape_html(event.title)}</div>
					<div class="shr-employee-360__event-detail">${escape_html(event.detail || "-")}</div>
				</div>
				<div class="shr-employee-360__event-value">${escape_html(event.value || "-")}</div>
			</div>`
		)
		.join("");
}

function build_attention_html(attention) {
	if (!attention.length) {
		return `<div class="shr-employee-360__empty">${__(
			"No urgent operational gaps were detected in this employee file."
		)}</div>`;
	}

	return attention
		.slice(0, 5)
		.map((item, index) => {
			const copy = get_attention_copy(item);
			return `
				<button type="button"
					class="shr-employee-360__action ${
						item.status === "action" ? "shr-employee-360__action--critical" : ""
					}"
					data-attention-index="${index}">
					<span>
						<span class="shr-employee-360__action-title">${escape_html(copy.title)}</span>
						<span class="shr-employee-360__action-detail">${escape_html(copy.detail)}</span>
					</span>
					<span class="shr-employee-360__action-mark" aria-hidden="true"></span>
				</button>`;
		})
		.join("");
}

function get_attention_copy(item) {
	const copies = {
		employment_status: {
			title: __("Review employment status"),
			detail: __("The employee is not currently marked as active."),
		},
		profile_details: {
			title: __("Complete core profile data"),
			detail: __("Add the department, designation, branch and contact details."),
		},
		user_access: {
			title: __("Link an enabled system user"),
			detail: __("Enable secure self-service and attendance access for this employee."),
		},
		contract: {
			title: __("Complete the employment contract"),
			detail: __("Create, renew or review the visible Saudi employment contract."),
		},
		leave_policy: {
			title: __("Assign a leave policy"),
			detail: __("Apply the correct policy to this employee or their department."),
		},
		attendance_setup: {
			title: __("Complete attendance setup"),
			detail: __("Assign an active shift and a branch attendance location."),
		},
		permit: {
			title: __("Review work authorization"),
			detail: __("Add or renew the expatriate employee's Iqama and work permit."),
		},
	};
	return (
		copies[item.code] || {
			title: __("Review employee record"),
			detail: __("This item needs an HR review."),
		}
	);
}

function build_quick_actions_html(profile) {
	const visibility = profile.visibility || {};
	const actions = [
		["attendance", __("Attendance")],
		["leave", __("New leave request")],
		["mobile", __("Mobile attendance")],
		["print", __("Complete file")],
	];

	if (visibility.contract) {
		actions.unshift(["contract", __("Employment contract")]);
	}
	if (visibility.leave) {
		actions.push(["policy", __("Leave policy")]);
	}

	return actions
		.map(
			([key, label]) =>
				`<button type="button" class="shr-employee-360__quick-button" data-quick-action="${key}">${escape_html(
					label
				)}</button>`
		)
		.join("");
}

function bind_employee_profile_actions(frm, $section, profile) {
	const attention = Array.isArray(profile.readiness && profile.readiness.attention)
		? profile.readiness.attention
		: [];

	$section
		.off(".saudiEmployeeProfile")
		.on("click.saudiEmployeeProfile", "[data-attention-index]", function () {
			const index = Number($(this).attr("data-attention-index"));
			const item = attention[index];
			if (item && item.route) {
				open_profile_route(item.route, frm.doc.name);
			}
		})
		.on("click.saudiEmployeeProfile", "[data-quick-action]", function () {
			open_quick_action($(this).attr("data-quick-action"), frm, profile);
		});
}

function open_profile_route(route, employee) {
	if (!Array.isArray(route) || !route.length) {
		return;
	}

	if (route[0] === "new" && route[1]) {
		frappe.new_doc(route[1], { employee: route[2] || employee });
		return;
	}

	if (route[0] === "List" && route[1]) {
		frappe.route_options = { employee };
	}
	frappe.set_route(...route);
}

function open_quick_action(action, frm, profile) {
	const employee = frm.doc.name;

	if (action === "contract") {
		if (profile.contract && profile.contract.name) {
			frappe.set_route("Form", "Saudi Employment Contract", profile.contract.name);
		} else {
			frappe.new_doc("Saudi Employment Contract", {
				employee,
				company: frm.doc.company,
			});
		}
		return;
	}

	if (action === "leave") {
		frappe.new_doc("Saudi Annual Leave", { employee });
		return;
	}

	if (action === "attendance") {
		frappe.route_options = { employee };
		frappe.set_route("List", "Saudi Daily Attendance");
		return;
	}

	if (action === "policy") {
		frappe.route_options = { employee };
		frappe.set_route("List", "Saudi Leave Policy Assignment");
		return;
	}

	if (action === "mobile") {
		window.open("/mobile-attendance", "_blank", "noopener,noreferrer");
		return;
	}

	if (action === "print") {
		open_employee_complete_file(employee);
	}
}

function open_employee_complete_file(employee) {
	const params = new URLSearchParams({
		doctype: "Employee",
		name: employee,
		format: SAUDI_EMPLOYEE_PRINT_FORMAT,
		no_letterhead: "0",
		_lang: (frappe.boot && frappe.boot.lang) || "ar",
	});
	window.open(`/printview?${params.toString()}`, "_blank", "noopener,noreferrer");
}

function get_readiness_state(state) {
	const states = {
		ready: { label: __("Operationally ready") },
		review: { label: __("Ready with follow-up") },
		incomplete: { label: __("Action required") },
	};
	return states[state] || states.incomplete;
}

function get_initials(value) {
	const words = String(value || "")
		.trim()
		.split(/\s+/)
		.filter(Boolean);
	if (!words.length) {
		return "HR";
	}
	return words
		.slice(0, 2)
		.map((word) => word.charAt(0))
		.join("")
		.toUpperCase();
}

function clamp_number(value, minimum, maximum) {
	const numeric = Number(value);
	if (!Number.isFinite(numeric)) {
		return minimum;
	}
	return Math.min(maximum, Math.max(minimum, Math.round(numeric)));
}

function escape_html(value) {
	return frappe.utils.escape_html(String(value === null || value === undefined ? "" : value));
}

function format_date(value) {
	if (!value) {
		return "-";
	}
	try {
		return frappe.datetime.str_to_user(String(value).slice(0, 10));
	} catch (error) {
		return String(value);
	}
}

function format_time(value) {
	if (!value) {
		return "-";
	}
	const parts = String(value).split(" ");
	return parts.length > 1 ? parts.slice(1).join(" ").slice(0, 5) : String(value);
}

function format_number(value) {
	const numeric = Number(value || 0);
	const locale =
		frappe.boot && String(frappe.boot.lang || "").startsWith("ar") ? "ar-SA" : "en-SA";
	try {
		return new Intl.NumberFormat(locale, { maximumFractionDigits: 2 }).format(numeric);
	} catch (error) {
		return String(numeric);
	}
}

function format_money(value, currency) {
	const numeric = Number(value || 0);
	const safeCurrency = currency || "SAR";
	const locale =
		frappe.boot && String(frappe.boot.lang || "").startsWith("ar") ? "ar-SA" : "en-SA";
	try {
		return new Intl.NumberFormat(locale, {
			style: "currency",
			currency: safeCurrency,
			maximumFractionDigits: 2,
		}).format(numeric);
	} catch (error) {
		return format_currency(numeric, safeCurrency);
	}
}

function render_paid_payroll_history(frm, currency) {
	const field = frm.get_field("salary_mode");
	if (!field || !field.$wrapper || frm.is_new()) {
		return;
	}

	const $section = get_paid_payroll_section(field.$wrapper);
	if (!$section.length) {
		return;
	}

	$section.html(`<div class="text-muted small">${__("Loading paid payroll history...")}</div>`);

	frappe.call({
		method: "saudi_hr.saudi_hr.api.get_employee_paid_payroll_history",
		args: {
			employee: frm.doc.name,
			limit: 12,
		},
		callback: ({ message }) => {
			const rows = Array.isArray(message) ? message : [];
			$section.html(
				build_paid_payroll_history_html(
					rows,
					currency ||
						(frappe.boot &&
							frappe.boot.sysdefaults &&
							frappe.boot.sysdefaults.currency) ||
						"SAR"
				)
			);
		},
		error: () => {
			$section.html(
				`<div class="text-danger small">${__("Unable to load paid payroll history right now.")}</div>`
			);
		},
	});
}

function get_paid_payroll_section($fieldWrapper) {
	const $sectionBody = $fieldWrapper.closest(".section-body");
	if (!$sectionBody.length) {
		return $();
	}

	let $section = $sectionBody.find(".employee-paid-payroll-history");

	if ($section.length) {
		return $section.find(".employee-paid-payroll-history-body");
	}

	$section = $(
		`<div class="employee-paid-payroll-history" style="margin-top: 24px;">
			<div class="form-dashboard-section">
				<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px;">
					<h5 style="margin:0;">${__("Paid Payroll History")}</h5>
				</div>
				<div class="employee-paid-payroll-history-body"></div>
			</div>
		</div>`
	);

	$sectionBody.append($section);
	return $section.find(".employee-paid-payroll-history-body");
}

function build_paid_payroll_history_html(rows, currency) {
	if (!rows.length) {
		return `<div class="text-muted small">${__("No paid payroll records were found for this employee.")}</div>`;
	}

	const tableRows = rows
		.map((row) => {
			const payrollLink = frappe.utils.get_form_link("Saudi Monthly Payroll", row.payroll, true);
			const journalLink = row.journal_entry
				? frappe.utils.get_form_link("Journal Entry", row.journal_entry, true)
				: '<span class="text-muted">-</span>';
			const postingDate = row.posting_date ? format_date(row.posting_date) : "-";
			const salaryMode = escape_html(row.salary_mode || "-");
			return `
				<tr>
					<td>${payrollLink}<div class="text-muted small">${escape_html(row.period_label || "-")}</div></td>
					<td>${escape_html(postingDate)}</td>
					<td>${escape_html(format_money(row.net_salary, currency))}</td>
					<td>${escape_html(format_money(row.gross_salary, currency))}</td>
					<td>${escape_html(format_money(row.total_deductions, currency))}</td>
					<td>${salaryMode}</td>
					<td>${journalLink}</td>
				</tr>`;
		})
		.join("");

	return `
		<div class="table-responsive">
			<table class="table table-bordered" style="margin-bottom: 0;">
				<thead>
					<tr>
						<th>${__("Payroll")}</th>
						<th>${__("Posting Date")}</th>
						<th>${__("Net Salary")}</th>
						<th>${__("Gross Salary")}</th>
						<th>${__("Deductions")}</th>
						<th>${__("Salary Mode")}</th>
						<th>${__("Journal Entry")}</th>
					</tr>
				</thead>
				<tbody>${tableRows}</tbody>
			</table>
		</div>`;
}
