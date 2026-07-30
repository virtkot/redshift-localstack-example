# Example only — not production-ready or officially supported. See README.md.

output "config_bucket_name" {
  value = aws_s3_bucket.config.id
}

output "config_object_key" {
  value = aws_s3_object.schema_config.key
}

output "cluster_identifier" {
  value = aws_redshift_cluster.this.cluster_identifier
}

output "default_database_name" {
  value = aws_redshift_cluster.this.database_name
}

output "master_username" {
  value = aws_redshift_cluster.this.master_username
}
