__version__ = "0.0.1"

# Ensure legacy imports that reference `razorpay_integration.*` continue to work
import importlib, sys

try:
	legacy_module = importlib.import_module("razorpay_frappe.razorpay_integration")
	sys.modules.setdefault("razorpay_integration", legacy_module)
except ModuleNotFoundError:
	# The sub-package might not be present right after installation; ignore.
	pass
