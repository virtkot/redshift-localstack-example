.PHONY: up down apply destroy fetch provision test

# Example only — not production-ready or officially supported. See README.md.

NAMESPACE ?= localstack
CONFIG_LOCAL_PATH ?= /tmp/schema.yaml

# Mimics the real topology: LocalStack Pro running as a container inside a
# Kubernetes pod (e.g. EKS in production, whatever local cluster your kubectl
# context points at here). No cluster create/delete: the cluster is a
# persistent, separately-managed resource, not something this repo owns the
# lifecycle of.
#
# Port 31566 is the LocalStack Helm chart's own default NodePort (not set
# anywhere in this repo's k8s/values.yaml — we just don't override it). On
# distros that auto-forward NodePort services to localhost (Rancher Desktop,
# Docker Desktop), that's reachable with no extra step; otherwise run
# `kubectl -n localstack port-forward svc/localstack 31566:4566` yourself.
# See .env.example for where this repo's own config points at that port.
up:
	kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	kubectl -n $(NAMESPACE) create secret generic localstack-auth-token \
		--from-literal=LOCALSTACK_AUTH_TOKEN=$(LOCALSTACK_AUTH_TOKEN) \
		--dry-run=client -o yaml | kubectl apply -f -
	helm repo add localstack https://localstack.github.io/helm-charts >/dev/null 2>&1 || true
	helm repo update
	helm upgrade --install localstack localstack/localstack -n $(NAMESPACE) -f k8s/values.yaml
	kubectl -n $(NAMESPACE) rollout status deployment/localstack --timeout=180s

down:
	-helm uninstall localstack -n $(NAMESPACE)
	-kubectl delete namespace $(NAMESPACE)

apply:
	cd terraform && terraform init -input=false && terraform apply -auto-approve

destroy:
	cd terraform && terraform destroy -auto-approve

# Step 1: pull the schema config down from the (LocalStack) S3 bucket.
fetch:
	python3 scripts/fetch_config.py \
		--bucket "$$(cd terraform && terraform output -raw config_bucket_name)" \
		--key "$$(cd terraform && terraform output -raw config_object_key)" \
		--output $(CONFIG_LOCAL_PATH)

# Step 3: provision databases/schemas/tables from that local config file.
provision: fetch
	python3 scripts/provision_redshift.py --config $(CONFIG_LOCAL_PATH) \
		--cluster-identifier "$$(cd terraform && terraform output -raw cluster_identifier)" \
		--default-database "$$(cd terraform && terraform output -raw default_database_name)"

test:
	python3 -m pytest -v
