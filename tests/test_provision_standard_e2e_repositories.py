import unittest
from pathlib import Path

from scripts.provision_standard_e2e_repositories import (
    BRANCH,
    EXPECTED_TARGETS,
    SOURCE_SECRET,
    load_specs,
    validate_specs,
)

SPEC_PATH = Path(__file__).resolve().parents[1] / "config" / "standard-e2e-specs.json.gz.b64"


class SpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values = load_specs(SPEC_PATH)

    def test_exact_four_canonical_targets(self):
        self.assertEqual(tuple(value.target for value in self.values), EXPECTED_TARGETS)
        self.assertEqual(BRANCH, "agent/bootstrap-real-e2e")
        validate_specs(self.values)

    def test_sources_and_actions_are_immutable_and_workflows_are_read_only(self):
        for value in self.values:
            self.assertRegex(value.source_sha, r"^[0-9a-f]{40}$")
            self.assertIn(f"ref: {value.source_sha}", value.workflow)
            self.assertIn("permissions:\n  contents: read", value.workflow)
            self.assertIn("persist-credentials: false", value.workflow)
            self.assertIn("pull_request:", value.workflow)
            self.assertNotIn("@main", value.workflow)
            self.assertNotIn("@master", value.workflow)

    def test_private_sources_use_repository_scoped_deploy_keys_only(self):
        private = {"memebank/memebank-e2e", "meta-agents-demo/metacog-e2e"}
        for value in self.values:
            has_secret = f"secrets.{SOURCE_SECRET}" in value.workflow
            self.assertEqual(value.source_private, value.target in private)
            self.assertEqual(has_secret, value.source_private)
            if value.source_private:
                self.assertIn("read-only deploy key", value.readme)

    def test_each_repository_has_at_least_three_named_journeys(self):
        for value in self.values:
            count = value.tests_content.count("def test_") + value.tests_content.count("test(")
            self.assertGreaterEqual(count, 3, value.target)
            self.assertIn("three", value.workflow.lower())


if __name__ == "__main__":
    unittest.main()
