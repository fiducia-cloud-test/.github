from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "test-program" / "catalog.json"
VALIDATOR_PATH = ROOT / "scripts" / "validate_test_program.py"

SPEC = importlib.util.spec_from_file_location("validate_test_program", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load validator from {VALIDATOR_PATH}")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def load_valid_catalog():
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


class TestProgramCatalogValidation(unittest.TestCase):
    def assertHasError(self, catalog, fragment: str) -> None:
        errors = VALIDATOR.validate_catalog(catalog)
        self.assertTrue(
            any(fragment in error for error in errors),
            f"expected error containing {fragment!r}; got {errors!r}",
        )

    def test_repository_catalog_is_valid(self):
        self.assertEqual([], VALIDATOR.validate_catalog(load_valid_catalog()))

    def test_duplicate_repository_is_rejected(self):
        catalog = load_valid_catalog()
        catalog["inventory"]["test"]["cleanConsumers"].append(
            catalog["inventory"]["test"]["languageSdkE2e"][0]
        )
        catalog["inventory"]["testRepositoryCount"] += 1
        self.assertHasError(catalog, "appears in more than one inventory category")

    def test_declared_count_drift_is_rejected(self):
        catalog = load_valid_catalog()
        catalog["inventory"]["productionRepositoryCount"] = 999
        self.assertHasError(catalog, "productionRepositoryCount")

    def test_uncovered_active_production_repository_is_rejected(self):
        catalog = load_valid_catalog()
        target = "fiducia-customer.rs"
        for domain in catalog["coverageDomains"].values():
            domain["production"] = [
                repository for repository in domain["production"] if repository != target
            ]
        self.assertHasError(catalog, "lack a coverage domain")

    def test_unknown_test_reference_is_rejected(self):
        catalog = load_valid_catalog()
        catalog["coverageDomains"]["governance-and-test-platform"]["tests"].append(
            "repository-that-does-not-exist"
        )
        self.assertHasError(catalog, "references unknown repository")

    def test_proposed_repository_cannot_already_be_live(self):
        catalog = load_valid_catalog()
        catalog["proposedRepositories"]["names"].append("api-contract-e2e")
        self.assertHasError(catalog, "already exists in the live test inventory")

    def test_repository_count_cannot_be_a_success_metric(self):
        catalog = load_valid_catalog()
        catalog["inventory"]["countIsSuccessMetric"] = True
        self.assertHasError(catalog, "countIsSuccessMetric must be false")

    def test_current_maturity_cannot_claim_uncataloged_certification(self):
        catalog = load_valid_catalog()
        catalog["inventory"]["test"]["focused"]["api-contract-e2e"][
            "currentMaturity"
        ] = "L4"
        self.assertHasError(catalog, "may exceed L1 only after retained evidence")


if __name__ == "__main__":
    unittest.main()
