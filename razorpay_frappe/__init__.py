__version__ = "0.0.1"

# ---------------------------------------------------------------------------
# Compatibility shim for Frappe Payments app (v13/v14) scheduler hook
# ---------------------------------------------------------------------------
# In the latest Payments app versions, the built-in Razorpay gateway code was
# removed but the hook reference in payments/hooks.py still points to
# `payments.payment_gateways.doctype.razorpay_settings.razorpay_settings.capture_payment`.
# This causes an `ImportError` during bench startup or when hooks are parsed.
# Until the Payments maintainers clean this up, we register a lightweight stub
# module under that dotted path at runtime so the import resolves and does
# nothing. This avoids noisy errors and allows the rest of the scheduler to
# run normally.

from types import ModuleType
import sys

_STUB_PATH = (
    "payments.payment_gateways.doctype.razorpay_settings.razorpay_settings"
)

if _STUB_PATH not in sys.modules:
    stub_mod = ModuleType(_STUB_PATH)

    def _noop(*args, **kwargs):
        """Placeholder for removed `capture_payment` implementation."""
        import frappe

        frappe.logger().debug(
            "[razorpay_frappe] Called legacy payments.capture_payment stub with args=%s kwargs=%s",
            args,
            kwargs,
        )

    # Expose the no-op so the scheduler can safely import & call it.
    stub_mod.capture_payment = _noop

    # Insert into sys.modules at each parent level so nested imports resolve.
    parent_module_path = []
    for part in _STUB_PATH.split("."):
        parent_module_path.append(part)
        module_key = ".".join(parent_module_path)
        if module_key not in sys.modules:
            sys.modules[module_key] = ModuleType(module_key)
        # Attach child to its parent so `import x.y` works progressively
        parent_mod = sys.modules[".".join(parent_module_path[:-1])] if len(parent_module_path) > 1 else None
        if parent_mod is not None:
            setattr(parent_mod, part, sys.modules[module_key])

    # Finally assign the stub implementation
    sys.modules[_STUB_PATH] = stub_mod
