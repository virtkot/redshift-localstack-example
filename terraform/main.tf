# Example only — not production-ready or officially supported. See README.md.
#
# No LocalStack-specific values here (no endpoints, no fake credentials) —
# this file is identical whether run against LocalStack or real AWS. Every
# environment-specific value (credentials, AWS_ENDPOINT_URL_S3,
# AWS_ENDPOINT_URL_REDSHIFT, ...) lives in .env / the shell environment,
# which both the AWS provider and boto3 read natively. See .env.example.

provider "aws" {
  region = var.aws_region

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}

# Stands in for a real S3 bucket that the provisioning job
# pulls its schema config from. In production this bucket already exists
# in the real AWS account and isn't managed by this Terraform config.
resource "aws_s3_bucket" "config" {
  bucket = var.config_bucket_name
}

resource "aws_s3_object" "schema_config" {
  bucket = aws_s3_bucket.config.id
  key    = var.config_object_key
  source = "${path.module}/../config/schema.yaml"
  etag   = filemd5("${path.module}/../config/schema.yaml")
}

resource "aws_redshift_cluster" "this" {
  cluster_identifier  = var.cluster_identifier
  database_name       = var.default_database_name
  master_username     = var.master_username
  master_password     = var.master_password
  node_type           = "dc2.large"
  cluster_type        = "single-node"
  skip_final_snapshot = true
}
