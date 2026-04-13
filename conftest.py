"""
conftest.py – Configures standalone pytest path for saudi_hr unit tests.

Adds the frappe and saudi_hr app directories to sys.path so that modules can be
imported without a running Frappe site. Tests that use these paths mock all
frappe DB/document calls themselves and do NOT connect to any site.
"""
import os
import sys
from unittest.mock import MagicMock

_here = os.path.dirname(os.path.abspath(__file__))           # …/apps/saudi_hr
_apps = os.path.abspath(os.path.join(_here, ".."))           # …/apps

for _app_dir in ("frappe", "saudi_hr"):
	_path = os.path.join(_apps, _app_dir)
	if os.path.isdir(_path) and _path not in sys.path:
		sys.path.insert(0, _path)

import frappe  # noqa: E402

# frappe._ (translation) must be callable before any module-level import
if not callable(getattr(frappe, "_", None)):
	frappe._ = lambda x: x

# Set up a minimal frappe.local context so that frappe.db / frappe.flags
# can be patch.object'd in tests without a live Frappe site.
try:
	_ = frappe.local.flags  # already bound → nothing to do
except AttributeError:
	frappe.local.flags = frappe._dict(in_test=True)
	frappe.local.db = MagicMock()
	frappe.local.conf = frappe._dict()
	frappe.local.lang = "en"

# Short-circuit frappe's translation lookup so _("...") returns the original
# string without accessing frappe.cache (which is None without a site).
import frappe.translate as _ft  # noqa: E402
_ft.get_all_translations = lambda lang: {}
