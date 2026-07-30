# Redshift cluster provisioning on LocalStack

> **Disclaimer:** This repository is an illustrative example only. It is not
> officially supported, production-ready, or maintained software. Use it as a
> reference for building your own implementation, not as a drop-in solution.

Example/test harness answering: *pull config files from a real S3 bucket,
create a Redshift cluster, and provision databases/schemas/tables from that
config* — using LocalStack for the Redshift side.

## Architecture

| Step | Where |
|---|---|
| 1. Pull config files from the real S3 bucket | [`scripts/fetch_config.py`](scripts/fetch_config.py) |
| 2. Create the Redshift cluster | [`terraform/`](terraform) |
| 3. Provision databases/schemas/tables from the config | [`scripts/provision_redshift.py`](scripts/provision_redshift.py) |

`fetch_config.py` only talks to S3. `provision_redshift.py` only talks to
Redshift (via the Redshift Data API) and only ever reads a local file — it
has no idea whether that file came from LocalStack or real AWS.

**No file in `terraform/` or `scripts/` contains any LocalStack-specific
value** — no endpoint URLs, no fake credentials, no ports. Every environment
difference (auth token, endpoint overrides, credentials) lives only in
`.env` (see `.env.example`), which both the Terraform AWS provider and boto3
read natively. That's what makes the hybrid setup below possible: point S3
at real AWS, Redshift at LocalStack, and no code or Terraform changes are
needed either way — only `.env` differs.

In this example, both S3 and Redshift point at LocalStack (via Terraform, we
upload [`config/schema.yaml`](config/schema.yaml) to a LocalStack bucket) so
the whole thing runs end-to-end offline. `config/schema.yaml` also documents
the config file format:

```yaml
databases:
  - name: analytics
    schemas:
      - name: public
        tables:
          - name: customers
            columns:
              - {name: customer_id, type: INTEGER, constraints: "NOT NULL"}
              - {name: full_name, type: "VARCHAR(255)"}
```

## Running this in production against a real S3 bucket

Drop `AWS_ENDPOINT_URL_S3` from the environment entirely so `fetch_config.py`
uses boto3's normal AWS credential chain and hits your real bucket. Keep
`AWS_ENDPOINT_URL` pointed at LocalStack so `provision_redshift.py` still
targets the local cluster. Nothing in either script or in `terraform/`
needs to change — only which variables are set in the environment.

One real-AWS difference to account for: against real Redshift, the Redshift
Data API needs either a `SecretArn` or a `DbUser` with `GetClusterCredentials`
permission to authenticate each statement — pass it via
`provision_redshift.py --db-user ...`. LocalStack's emulation doesn't enforce
this, so it's optional here.

## Prerequisites

This assumes LocalStack Pro is deployed as a container inside a Kubernetes
pod (e.g. on EKS in production), not as a bare `docker run`/Docker Compose
container. `make up` mimics that topology using **any local Kubernetes
cluster** and the official LocalStack Helm chart
([`k8s/values.yaml`](k8s/values.yaml)), so the deployment shape matches what
runs in production.

- A local Kubernetes cluster with `kubectl` already pointed at it — e.g.
  [Rancher Desktop](https://rancherdesktop.io/) or Docker Desktop with
  Kubernetes enabled, [`kind`](https://kind.sigs.k8s.io/), or
  [`k3d`](https://k3d.io/). Some of these (Rancher Desktop, Docker Desktop)
  auto-forward `NodePort`/`LoadBalancer` services to `localhost`, which is
  what makes the LocalStack chart's default node port (`31566`) directly
  reachable with no extra step. If yours doesn't, run
  `kubectl -n localstack port-forward svc/localstack 31566:4566` in a
  separate terminal after `make up`.
- `helm`
- Terraform CLI
- **LocalStack Pro** — the Redshift Data API (`ExecuteStatement`,
  `DescribeStatement`, `ListDatabases`, `ListTables`, ...) used to run the DDL
  is a Pro-only feature. Set `LOCALSTACK_AUTH_TOKEN` in `.env`.
- `pip3 install -r requirements.txt` (installs `boto3`, `pyyaml`, `pytest`)

## Running it

```bash
cp .env.example .env   # fill in LOCALSTACK_AUTH_TOKEN
set -a && source .env && set +a

make up                 # Helm-install LocalStack Pro into your local Kubernetes cluster
make apply              # terraform: create the S3 config bucket + object, and the Redshift cluster
make fetch              # step 1: pull schema.yaml from the (LocalStack) S3 bucket to /tmp/schema.yaml
make provision          # step 3: provision databases/schemas/tables from that local file

make down               # helm uninstall + delete the namespace (the cluster itself stays up)
```

Or, with `make up` already run, just run the automated end-to-end test, which
does the rest of the above (`terraform apply` → fetch → provision → assert)
and tears down the Terraform stack afterwards:

```bash
make test
make down
```

## Repo layout

```
k8s/values.yaml        Helm values for LocalStack Pro (mirrors the EKS deployment shape)
terraform/             Terraform config: S3 config bucket/object + Redshift cluster (no LocalStack-specific values)
config/schema.yaml     sample schema config (what the real S3 bucket would contain)
scripts/
  fetch_config.py       step 1: S3 -> local file
  provision_redshift.py step 3: local file -> Redshift Data API DDL
tests/
  conftest.py          spins up/tears down the Terraform stack for the test session
  test_provisioning.py runs the fetch + provision flow, asserts tables exist
.env.example           the only place any LocalStack-specific value lives
```
