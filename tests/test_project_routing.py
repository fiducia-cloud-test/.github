from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profile" / "README.md"
PROJECTS = ROOT / "docs" / "PROJECTS.md"

SHARED_LINEAR_URL = (
    "https://linear.app/denman/project/githubcomfiducia-cloud-8fd5e1bec9d3"
)
CANCELED_LINEAR_URL = (
    "https://linear.app/denman/project/githubcomfiducia-cloud-test-ad993264fa5e"
)
PRODUCTION_PROJECT_URL = "https://github.com/orgs/fiducia-cloud/projects/1"
TEST_PROJECT_URL = "https://github.com/orgs/fiducia-cloud-test/projects/1"
CREDENTIAL_SHAPE = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
    r"Authorization:\s*Bearer\s+[A-Za-z0-9._-]+)"
)


class ProjectRoutingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = PROFILE.read_text(encoding="utf-8")
        cls.projects = PROJECTS.read_text(encoding="utf-8")

    def test_profile_and_contract_use_the_shared_active_linear_project(self) -> None:
        for path, content in ((PROFILE, self.profile), (PROJECTS, self.projects)):
            with self.subTest(path=path):
                self.assertIn(SHARED_LINEAR_URL, content)
                self.assertNotIn(CANCELED_LINEAR_URL, content)
                self.assertEqual(1, content.count("<!-- org-project-routing:start -->"))
                self.assertEqual(1, content.count("<!-- org-project-routing:end -->"))

    def test_test_org_keeps_its_own_github_project(self) -> None:
        self.assertIn(TEST_PROJECT_URL, self.profile)
        self.assertIn(TEST_PROJECT_URL, self.projects)
        self.assertIn(PRODUCTION_PROJECT_URL, self.profile)
        self.assertIn(PRODUCTION_PROJECT_URL, self.projects)
        self.assertNotEqual(TEST_PROJECT_URL, PRODUCTION_PROJECT_URL)

    def test_shared_planning_does_not_collapse_delivery_evidence(self) -> None:
        required = [
            "one planning project, two execution boards",
            "independently attributable",
            "workflow runs",
            "immutable source or artifact pins",
            "credential-blocked workflow never counts as passed coverage",
        ]
        lowered = self.projects.casefold()
        for phrase in required:
            self.assertIn(phrase.casefold(), lowered)

    def test_public_routing_docs_are_credential_free(self) -> None:
        for path, content in ((PROFILE, self.profile), (PROJECTS, self.projects)):
            with self.subTest(path=path):
                self.assertIsNone(CREDENTIAL_SHAPE.search(content))


if __name__ == "__main__":
    unittest.main()
