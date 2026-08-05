import json
import os
import sys
from pathlib import Path


def variables() -> dict[str, str]:
    values = dict(line.split("=", 1) for line in os.environ["ENV_VARS"].splitlines() if "=" in line)
    required = {"MONGO_INITDB_ROOT_USERNAME", "MONGO_INITDB_ROOT_PASSWORD", "MONGODB_URI"}
    missing = required - values.keys()
    if missing:
        raise SystemExit(f"Missing ENV_VARS: {', '.join(sorted(missing))}")
    return values


Path(sys.argv[1]).write_text(json.dumps({
    "apiVersion": "v1",
    "kind": "Secret",
    "metadata": {"name": "bus-app-secrets", "namespace": "ptm-bus"},
    "stringData": variables(),
}, indent=2), encoding="utf-8")
