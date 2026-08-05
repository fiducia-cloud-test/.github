#!/usr/bin/env bash
set -euo pipefail

source_script=".github/scripts/finish-declarative-e2e-v3.sh"
temporary_script="${RUNNER_TEMP:-/tmp}/finish-declarative-e2e-v4-expanded.sh"

python3 - "$source_script" "$temporary_script" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text()
old = '{"local-container", "local-process", "advisory", "protected-environment"}'
new = '{"local-container", "local-process", "advisory", "protected-environment", "mixed"}'
if source.count(old) != 1:
    raise SystemExit(f"expected exactly one integration-mode allowlist, found {source.count(old)}")
Path(sys.argv[2]).write_text(source.replace(old, new))
PY

bash -n "$temporary_script"
exec bash "$temporary_script"
