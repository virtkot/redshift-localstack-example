# Example only — not production-ready or officially supported. See README.md.

import boto3

import fetch_config
import provision_redshift


def test_provisions_databases_schemas_and_tables(terraform_stack, tmp_path):
    local_config_path = tmp_path / "schema.yaml"
    fetch_config.fetch_config(
        terraform_stack["config_bucket_name"], terraform_stack["config_object_key"], local_config_path
    )

    config = provision_redshift.load_config(local_config_path)
    provision_redshift.provision(
        config, terraform_stack["cluster_identifier"], terraform_stack["default_database_name"]
    )

    client = boto3.client("redshift-data")
    cluster_identifier = terraform_stack["cluster_identifier"]

    databases = client.list_databases(ClusterIdentifier=cluster_identifier, Database=config["databases"][0]["name"])[
        "Databases"
    ]
    assert "analytics" in databases

    tables = client.list_tables(ClusterIdentifier=cluster_identifier, Database="analytics")["Tables"]
    table_names = {(t["schema"], t["name"]) for t in tables}

    assert table_names == {
        ("public", "customers"),
        ("public", "transactions"),
        ("reporting", "daily_summary"),
    }
