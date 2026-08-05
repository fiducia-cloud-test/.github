import csv
import tempfile
import unittest
from pathlib import Path

from scripts.reconcile_github_projects import (
    Decision,
    ReconcileError,
    RegistryEntry,
    decide,
    load_registry,
)


def entry(org: str = "example-org", number: int = 1) -> RegistryEntry:
    return RegistryEntry(
        portfolio_key=org.lower(),
        github_org=org,
        github_project_number=number,
        github_project_title=f"{org}-project",
        github_project_url=f"https://github.com/orgs/{org}/projects/{number}",
        linear_project_name=f"github.com/{org}",
        linear_project_url="https://linear.app/denman/project/example",
    )


class DecisionTests(unittest.TestCase):
    def test_exact_title_and_number_updates_in_place(self):
        self.assertEqual(
            decide([{"number": 1, "title": "example-org-project"}], entry()),
            Decision("update", 1, "canonical project already exists"),
        )

    def test_canonical_number_with_wrong_title_is_retitle(self):
        self.assertEqual(
            decide([{"number": 1, "title": "Old roadmap"}], entry()),
            Decision("retitle", 1, "canonical number has title 'Old roadmap'"),
        )

    def test_absent_project_is_create(self):
        self.assertEqual(
            decide([], entry()),
            Decision("create", None, "canonical project is absent"),
        )

    def test_exact_title_at_wrong_number_fails_closed(self):
        with self.assertRaisesRegex(ReconcileError, "not canonical"):
            decide([{"number": 2, "title": "example-org-project"}], entry())

    def test_duplicate_exact_titles_fail_closed(self):
        with self.assertRaisesRegex(ReconcileError, "duplicate projects"):
            decide(
                [
                    {"number": 1, "title": "example-org-project"},
                    {"number": 2, "title": "example-org-project"},
                ],
                entry(),
            )


class RegistryTests(unittest.TestCase):
    def test_registry_requires_exact_41_rows_and_canonical_names(self):
        fieldnames = [
            "portfolio_key",
            "github_org",
            "github_project_number",
            "github_project_title",
            "github_project_url",
            "linear_project_name",
            "linear_project_url",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                for index in range(41):
                    org = "dancing-dragons" if index == 0 else f"org-{index:02d}"
                    number = 4 if org == "dancing-dragons" else 1
                    writer.writerow(
                        {
                            "portfolio_key": org,
                            "github_org": org,
                            "github_project_number": number,
                            "github_project_title": f"{org}-project",
                            "github_project_url": (
                                f"https://github.com/orgs/{org}/projects/{number}"
                            ),
                            "linear_project_name": f"github.com/{org}",
                            "linear_project_url": (
                                f"https://linear.app/denman/project/{org}"
                            ),
                        }
                    )
            self.assertEqual(len(load_registry(path)), 41)

    def test_wrong_row_count_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.csv"
            path.write_text(
                "portfolio_key,github_org,github_project_number,github_project_title,"
                "github_project_url,linear_project_name,linear_project_url\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ReconcileError, "exactly 41"):
                load_registry(path)


if __name__ == "__main__":
    unittest.main()
