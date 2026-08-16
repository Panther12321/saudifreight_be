"""Static safeguards that run without a Frappe runtime during early repository setup."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "naqil" / "naqil"
MODULE = APP / "naqil"


class NaqilStaticContractTests(unittest.TestCase):
    def test_frappe_module_layout_is_standard(self):
        self.assertTrue((MODULE / "__init__.py").is_file())
        self.assertTrue((MODULE / "doctype").is_dir())
        self.assertTrue((MODULE / "workspace").is_dir())

    def test_doctype_json_is_valid(self):
        files = list((MODULE / "doctype").rglob("*.json"))
        self.assertGreaterEqual(len(files), 14)
        for file_path in files:
            with self.subTest(file=file_path):
                payload = json.loads(file_path.read_text(encoding="utf-8"))
                self.assertEqual(payload.get("doctype"), "DocType")

    def test_every_doctype_has_a_controller_module(self):
        for doctype_path in (MODULE / "doctype").iterdir():
            if not doctype_path.is_dir() or doctype_path.name.startswith("__"):
                continue
            controller = doctype_path / f"{doctype_path.name}.py"
            self.assertTrue(controller.is_file(), f"missing controller: {controller}")

    def test_legacy_erpnext_marketplace_doctypes_are_not_present(self):
        legacy = {
            "shipment_request",
            "carrier_bid",
            "carrier_profile",
            "customer_profile",
            "backhaul_trip",
            "naqil_settings",
        }
        current = {path.name for path in (MODULE / "doctype").iterdir() if path.is_dir()}
        self.assertFalse(legacy.intersection(current))

    def test_application_code_has_no_permission_bypass(self):
        violations = []
        for file_path in APP.rglob("*.py"):
            source = file_path.read_text(encoding="utf-8")
            if "ignore_permissions=True" in source:
                violations.append(str(file_path.relative_to(ROOT)))
        self.assertEqual(violations, [], f"permission bypass found: {violations}")

    def test_auction_logic_requires_customer_selection(self):
        source = (APP / "services" / "auction.py").read_text(encoding="utf-8")
        self.assertIn("Selection Due", source)
        self.assertIn("require_organization_access", source)
        self.assertNotIn("lowest offer wins", source.lower())


if __name__ == "__main__":
    unittest.main()
