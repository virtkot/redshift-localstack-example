# Example only — not production-ready or officially supported. See README.md.

variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "config_bucket_name" {
  description = "Name of the S3 bucket that holds the schema config file. Stands in for a real S3 bucket in this example."
  type        = string
  default     = "example-redshift-config"
}

variable "config_object_key" {
  description = "Key of the schema config object inside config_bucket_name."
  type        = string
  default     = "schema.yaml"
}

variable "cluster_identifier" {
  description = "Redshift cluster identifier."
  type        = string
  default     = "example-redshift-cluster"
}

variable "default_database_name" {
  description = "Initial database created alongside the cluster. Additional databases are created later from the config file."
  type        = string
  default     = "dev"
}

variable "master_username" {
  description = "Redshift master username."
  type        = string
  default     = "admin"
}

variable "master_password" {
  description = "Redshift master password."
  type        = string
  default     = "TestPassword123"
  sensitive   = true
}
