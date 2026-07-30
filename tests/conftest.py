# Example only — not production-ready or officially supported. See README.md.

import json
import subprocess
import sys
import time
from pathlib import Path

import boto3
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TERRAFORM_DIR = REPO_ROOT / "terraform"

sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _run(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, check=True)


def _wait_for_cluster_available(cluster_identifier, timeout=120):
    client = boto3.client("redshift")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        clusters = client.describe_clusters(ClusterIdentifier=cluster_identifier)["Clusters"]
        if clusters and clusters[0]["ClusterStatus"] == "available":
            return
        time.sleep(1)
    raise TimeoutError(f"Cluster {cluster_identifier} did not become available in time")


@pytest.fixture(scope="session")
def terraform_stack():
    _run(["terraform", "init", "-input=false"], cwd=TERRAFORM_DIR)
    _run(["terraform", "apply", "-auto-approve"], cwd=TERRAFORM_DIR)

    outputs_raw = subprocess.run(
        ["terraform", "output", "-json"], cwd=TERRAFORM_DIR, check=True, capture_output=True, text=True
    ).stdout
    outputs = {key: value["value"] for key, value in json.loads(outputs_raw).items()}

    _wait_for_cluster_available(outputs["cluster_identifier"])

    yield outputs

    _run(["terraform", "destroy", "-auto-approve"], cwd=TERRAFORM_DIR)
