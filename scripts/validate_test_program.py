#!/usr/bin/env python3
"""Validate the Fiducia cross-organization E2E coverage catalog.

The validator intentionally uses only the Python standard library so it can run
on pull requests without dependency installation or credentials.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ISSUE_RE = re.compile(r"^DEN-\d+$")
REQUIRED_MATURITY = {"NA", "L0", "L1", "L2", "L3", "L4", "L5", "L6"}
EXPECTED_PROPOSED_STATE = "candidate-requires-catalog-gap-proof"
EXPECTED_EVIDENCE_CONTRACT = "signed-evidence-bundle-v1"


def _as_mapping(value: Any, path: str, errors: list[str]) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    errors.append(f"{path} must be an object")
    return {}


def _as_sequence(value: Any, path: str, errors: list[str]) -> Sequence[Any]:
    if isinstance(value, list):
        return value
    errors.append(f"{path} must be an array")
    return []


def _strings(value: Any, path: str, errors: list[str]) -> list[str]:
    items = _as_sequence(value, path, errors)
    result: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{path}[{index}] must be a non-empty string")
            continue
        result.append(item)
    return result


def _duplicates(values: Iterable[str]) -> list[str]:
    return sorted(name for name, count in Counter(values).items() if count > 1)


def _require_issue(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not ISSUE_RE.fullmatch(value):
        errors.append(f"{path} must be a Linear issue identifier such as DEN-2354")


def _validate_maturity(value: Any, path: str, known: set[str], errors: list[str]) -> None:
    if value not in known:
        errors.append(f"{path} must be one of {sorted(known)}; got {value!r}")


def _flatten_production(catalog: Mapping[str, Any], errors: list[str]) -> tuple[list[str], set[str]]:
    inventory = _as_mapping(catalog.get("inventory"), "inventory", errors)
    production = _as_mapping(inventory.get("production"), "inventory.production", errors)
    categories = ("governance", "active", "archived", "superseded")
    flattened: list[str] = []
    for category in categories:
        flattened.extend(_strings(production.get(category), f"inventory.production.{category}", errors))

    for duplicate in _duplicates(flattened):
        errors.append(f"production repository {duplicate!r} appears in more than one inventory category")

    declared = inventory.get("productionRepositoryCount")
    if declared != len(flattened):
        errors.append(
            "inventory.productionRepositoryCount "
            f"is {declared!r}, but the inventory contains {len(flattened)} repositories"
        )

    required = set(
        _strings(production.get("governance"), "inventory.production.governance", [])
        + _strings(production.get("active"), "inventory.production.active", [])
    )
    return flattened, required


def _flatten_tests(
    catalog: Mapping[str, Any], known_maturity: set[str], errors: list[str]
) -> tuple[list[str], set[str]]:
    inventory = _as_mapping(catalog.get("inventory"), "inventory", errors)
    test = _as_mapping(inventory.get("test"), "inventory.test", errors)

    governance = _strings(test.get("governance"), "inventory.test.governance", errors)
    language = _strings(test.get("languageSdkE2e"), "inventory.test.languageSdkE2e", errors)
    consumers = _strings(test.get("cleanConsumers"), "inventory.test.cleanConsumers", errors)
    ingestion = _strings(test.get("packageIngestion"), "inventory.test.packageIngestion", errors)

    focused = _as_mapping(test.get("focused"), "inventory.test.focused", errors)
    focused_names: list[str] = []
    for name, assessment_value in focused.items():
        if not isinstance(name, str) or not name:
            errors.append("inventory.test.focused keys must be non-empty repository names")
            continue
        focused_names.append(name)
        assessment = _as_mapping(
            assessment_value, f"inventory.test.focused.{name}", errors
        )
        _validate_maturity(
            assessment.get("currentMaturity"),
            f"inventory.test.focused.{name}.currentMaturity",
            known_maturity,
            errors,
        )
        _validate_maturity(
            assessment.get("targetMaturity"),
            f"inventory.test.focused.{name}.targetMaturity",
            known_maturity,
            errors,
        )
        if assessment.get("currentMaturity") not in {"L0", "L1"}:
            errors.append(
                f"inventory.test.focused.{name}.currentMaturity may exceed L1 only "
                "after retained evidence is represented in this catalog"
            )

    defaults = _as_mapping(test.get("groupDefaults"), "inventory.test.groupDefaults", errors)
    for group in ("governance", "languageSdkE2e", "cleanConsumers", "packageIngestion"):
        assessment = _as_mapping(
            defaults.get(group), f"inventory.test.groupDefaults.{group}", errors
        )
        _validate_maturity(
            assessment.get("currentMaturity"),
            f"inventory.test.groupDefaults.{group}.currentMaturity",
            known_maturity,
            errors,
        )
        _validate_maturity(
            assessment.get("targetMaturity"),
            f"inventory.test.groupDefaults.{group}.targetMaturity",
            known_maturity,
            errors,
        )

    flattened = governance + language + focused_names + consumers + ingestion
    for duplicate in _duplicates(flattened):
        errors.append(f"test repository {duplicate!r} appears in more than one inventory category")

    declared = inventory.get("testRepositoryCount")
    if declared != len(flattened):
        errors.append(
            "inventory.testRepositoryCount "
            f"is {declared!r}, but the inventory contains {len(flattened)} repositories"
        )

    if inventory.get("countIsSuccessMetric") is not False:
        errors.append("inventory.countIsSuccessMetric must be false")

    return flattened, set(flattened)


def validate_catalog(catalog: Mapping[str, Any]) -> list[str]:
    """Return every validation error without stopping at the first one."""

    errors: list[str] = []

    if catalog.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")

    program = _as_mapping(catalog.get("program"), "program", errors)
    for field in ("parentIssue", "catalogIssue"):
        _require_issue(program.get(field), f"program.{field}", errors)

    maturity = _as_mapping(catalog.get("maturity"), "maturity", errors)
    known_maturity = set(maturity)
    missing_maturity = REQUIRED_MATURITY - known_maturity
    if missing_maturity:
        errors.append(f"maturity is missing required levels: {sorted(missing_maturity)}")

    production, required_production = _flatten_production(catalog, errors)
    tests, required_tests = _flatten_tests(catalog, known_maturity, errors)
    production_set = set(production)
    test_set = set(tests)

    assessment = _as_mapping(catalog.get("currentAssessment"), "currentAssessment", errors)
    if assessment.get("specializedAndConsumerDefault") != "L1":
        errors.append("currentAssessment.specializedAndConsumerDefault must remain L1 until evidence is cataloged")
    if assessment.get("certificationEvidenceVerifiedByCatalog") is not False:
        errors.append("currentAssessment.certificationEvidenceVerifiedByCatalog must be false in the initial audit")
    orchestrator = _as_mapping(assessment.get("orchestrator"), "currentAssessment.orchestrator", errors)
    if orchestrator.get("repository") != "fiducia-cloud/fiducia-e2e":
        errors.append("currentAssessment.orchestrator.repository must be fiducia-cloud/fiducia-e2e")
    if orchestrator.get("maturity") != "L3":
        errors.append("currentAssessment.orchestrator.maturity must be L3 for the audited local multi-node coverage")

    proposed = _as_mapping(catalog.get("proposedRepositories"), "proposedRepositories", errors)
    _require_issue(proposed.get("issue"), "proposedRepositories.issue", errors)
    if proposed.get("state") != EXPECTED_PROPOSED_STATE:
        errors.append(
            f"proposedRepositories.state must be {EXPECTED_PROPOSED_STATE!r}"
        )
    proposed_names = _strings(proposed.get("names"), "proposedRepositories.names", errors)
    for duplicate in _duplicates(proposed_names):
        errors.append(f"proposed repository {duplicate!r} is listed more than once")
    for collision in sorted(set(proposed_names) & test_set):
        errors.append(f"proposed repository {collision!r} already exists in the live test inventory")

    domains = _as_mapping(catalog.get("coverageDomains"), "coverageDomains", errors)
    covered_production: set[str] = set()
    covered_tests: set[str] = set()
    known_contracts = set(_as_mapping(catalog.get("evidenceContracts"), "evidenceContracts", errors))

    for domain_name, domain_value in domains.items():
        domain_path = f"coverageDomains.{domain_name}"
        domain = _as_mapping(domain_value, domain_path, errors)
        _require_issue(domain.get("issue"), f"{domain_path}.issue", errors)
        _require_issue(domain.get("ownerIssue"), f"{domain_path}.ownerIssue", errors)
        if domain.get("ownerIssue") != domain.get("issue"):
            errors.append(f"{domain_path}.ownerIssue must match {domain_path}.issue")
        _validate_maturity(
            domain.get("targetMaturity"),
            f"{domain_path}.targetMaturity",
            known_maturity,
            errors,
        )

        cadence = _strings(domain.get("cadence"), f"{domain_path}.cadence", errors)
        environments = _strings(domain.get("environments"), f"{domain_path}.environments", errors)
        if not cadence:
            errors.append(f"{domain_path}.cadence must not be empty")
        if not environments:
            errors.append(f"{domain_path}.environments must not be empty")

        contract = domain.get("evidenceContract")
        if contract not in known_contracts:
            errors.append(f"{domain_path}.evidenceContract references unknown contract {contract!r}")

        prod_refs = _strings(domain.get("production"), f"{domain_path}.production", errors)
        test_refs = _strings(domain.get("tests"), f"{domain_path}.tests", errors)
        for ref in prod_refs:
            if ref not in production_set:
                errors.append(f"{domain_path}.production references unknown repository {ref!r}")
        for ref in test_refs:
            if ref not in test_set:
                errors.append(f"{domain_path}.tests references unknown repository {ref!r}")
        covered_production.update(prod_refs)
        covered_tests.update(test_refs)

        for gap in _strings(domain.get("gaps", []), f"{domain_path}.gaps", errors):
            if gap not in proposed_names:
                errors.append(f"{domain_path}.gaps references undeclared proposal {gap!r}")

    missing_production = sorted(required_production - covered_production)
    if missing_production:
        errors.append(f"active/governance production repositories lack a coverage domain: {missing_production}")
    missing_tests = sorted(required_tests - covered_tests)
    if missing_tests:
        errors.append(f"live test repositories lack a coverage domain: {missing_tests}")

    rules = _strings(catalog.get("truthfulnessRules"), "truthfulnessRules", errors)
    normalized_rules = " ".join(rules).lower()
    for term, explanation in (
        ("skip", "skipped work"),
        ("generated", "generated scaffolding"),
        ("fail", "fail-closed certification"),
        ("count", "repository-count truthfulness"),
    ):
        if term not in normalized_rules:
            errors.append(f"truthfulnessRules must explicitly address {explanation}")

    contracts = _as_mapping(catalog.get("evidenceContracts"), "evidenceContracts", errors)
    evidence = _as_mapping(
        contracts.get(EXPECTED_EVIDENCE_CONTRACT),
        f"evidenceContracts.{EXPECTED_EVIDENCE_CONTRACT}",
        errors,
    )
    _require_issue(evidence.get("issue"), f"evidenceContracts.{EXPECTED_EVIDENCE_CONTRACT}.issue", errors)
    if evidence.get("releaseMode") != "fail-closed":
        errors.append(
            f"evidenceContracts.{EXPECTED_EVIDENCE_CONTRACT}.releaseMode must be 'fail-closed'"
        )
    required_fields = _strings(
        evidence.get("requiredFields"),
        f"evidenceContracts.{EXPECTED_EVIDENCE_CONTRACT}.requiredFields",
        errors,
    )
    if len(set(required_fields)) != len(required_fields):
        errors.append(f"evidenceContracts.{EXPECTED_EVIDENCE_CONTRACT}.requiredFields contains duplicates")

    return errors


def load_catalog(path: Path) -> Mapping[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"catalog not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(parsed, Mapping):
        raise ValueError(f"catalog root must be an object: {path}")
    return parsed


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "catalog",
        nargs="?",
        type=Path,
        default=Path("test-program/catalog.json"),
        help="catalog JSON path (default: test-program/catalog.json)",
    )
    args = parser.parse_args(argv)

    try:
        catalog = load_catalog(args.catalog)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    errors = validate_catalog(catalog)
    if errors:
        print(f"ERROR: {len(errors)} test-program catalog validation error(s):", file=sys.stderr)
        for error in errors:
            print(f" - {error}", file=sys.stderr)
        return 1

    inventory = catalog["inventory"]
    print(
        "validated Fiducia E2E catalog: "
        f"{inventory['productionRepositoryCount']} production repositories, "
        f"{inventory['testRepositoryCount']} test repositories, "
        f"{len(catalog['coverageDomains'])} coverage domains; "
        "certification evidence remains conservative and fail-closed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
