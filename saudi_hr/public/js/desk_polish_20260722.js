(function () {
	function install_safe_chart_removal() {
		if (Element.prototype.__saudi_hr_safe_chart_removal) {
			return;
		}

		const original_remove_child = Element.prototype.removeChild;
		Element.prototype.removeChild = function (child) {
			const is_stale_workspace_chart =
				this.classList &&
				this.classList.contains("chart-container") &&
				child &&
				child.classList &&
				child.classList.contains("frappe-chart") &&
				child.parentNode !== this;

			if (is_stale_workspace_chart) {
				return child;
			}

			return original_remove_child.call(this, child);
		};

		Object.defineProperty(Element.prototype, "__saudi_hr_safe_chart_removal", {
			value: true,
			configurable: false,
			enumerable: false,
			writable: false,
		});
	}

	function remove_undefined_tooltips() {
		document.querySelectorAll(".tooltip-content").forEach(function (tooltip) {
			if ((tooltip.textContent || "").trim() === "undefined") {
				tooltip.textContent = "";
				tooltip.setAttribute("aria-hidden", "true");
			}
		});
	}

	function initialize() {
		install_safe_chart_removal();
		remove_undefined_tooltips();
		let scheduled = false;
		new MutationObserver(function () {
			if (scheduled) {
				return;
			}
			scheduled = true;
			window.requestAnimationFrame(function () {
				scheduled = false;
				remove_undefined_tooltips();
			});
		}).observe(document.body, { childList: true, subtree: true });
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", initialize);
	} else {
		initialize();
	}
})();
