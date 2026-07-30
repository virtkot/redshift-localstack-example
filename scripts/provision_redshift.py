#!/usr/bin/env python3
"""Provision databases, schemas, and tables on a Redshift cluster from a
local schema config file, via the Redshift Data API.

Example only — not production-ready or officially supported. See README.md.

This is the "Provision the databases, schemas, and tables" step: it only
talks to Redshift and knows nothing about S3 — it just reads the config file
that fetch_config.py already pulled down locally. No LocalStack-specific code
here — boto3 reads AWS_ENDPOINT_URL_REDSHIFT_DATA (or AWS_ENDPOINT_URL) from
the environment on its own. See .env.example.
"""
import argparse
import time

import yaml

import boto3


def load_config(config_path):
    with open(config_path) as f:
        return yaml.safe_load(f)


def run_statement(client, sql, cluster_identifier, database, db_user=None, poll_interval=1.0, timeout=60):
    kwargs = {"ClusterIdentifier": cluster_identifier, "Database": database, "Sql": sql}
    if db_user:
        kwargs["DbUser"] = db_user

    statement_id = client.execute_statement(**kwargs)["Id"]

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        description = client.describe_statement(Id=statement_id)
        status = description["Status"]
        if status == "FINISHED":
            return description
        if status in ("FAILED", "ABORTED"):
            raise RuntimeError(f"Statement failed ({status}): {sql!r} -> {description.get('Error')}")
        time.sleep(poll_interval)
    raise TimeoutError(f"Statement did not finish in time: {sql!r}")


def build_create_table_sql(schema_name, table):
    columns_sql = ", ".join(
        f"{col['name']} {col['type']}" + (f" {col['constraints']}" if col.get("constraints") else "")
        for col in table["columns"]
    )
    return f"CREATE TABLE IF NOT EXISTS {schema_name}.{table['name']} ({columns_sql})"


def provision(config, cluster_identifier, default_database, db_user=None):
    client = boto3.client("redshift-data")

    for database in config["databases"]:
        db_name = database["name"]
        if db_name != default_database:
            run_statement(client, f"CREATE DATABASE {db_name}", cluster_identifier, default_database, db_user)

        for schema in database.get("schemas", []):
            schema_name = schema["name"]
            run_statement(client, f"CREATE SCHEMA IF NOT EXISTS {schema_name}", cluster_identifier, db_name, db_user)

            for table in schema.get("tables", []):
                run_statement(client, build_create_table_sql(schema_name, table), cluster_identifier, db_name, db_user)
                print(f"Created {db_name}.{schema_name}.{table['name']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Local path to the schema config file")
    parser.add_argument("--cluster-identifier", required=True)
    parser.add_argument("--default-database", required=True, help="Database the cluster was created with")
    parser.add_argument("--db-user", default=None, help="Only needed against real AWS; LocalStack ignores it")
    args = parser.parse_args()

    config = load_config(args.config)
    provision(config, args.cluster_identifier, args.default_database, args.db_user)


if __name__ == "__main__":
    main()
