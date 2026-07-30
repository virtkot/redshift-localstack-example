#!/usr/bin/env python3
"""Pull the schema config file from S3 and save it locally.

Example only — not production-ready or officially supported. See README.md.

This is the "Pull the configuration files from the Real S3 bucket" step:
it only talks to S3 and knows nothing about Redshift. No LocalStack-specific
code here — boto3 reads AWS_ENDPOINT_URL_S3 from the environment on its own,
so this same code runs unmodified against real AWS or LocalStack. See
.env.example for the environment variables that make the difference.
"""
import argparse

import boto3


def fetch_config(bucket, key, output_path):
    obj = boto3.client("s3").get_object(Bucket=bucket, Key=key)
    with open(output_path, "wb") as f:
        f.write(obj["Body"].read())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", required=True, help="S3 bucket holding the schema config file")
    parser.add_argument("--key", required=True, help="S3 object key of the schema config file")
    parser.add_argument("--output", required=True, help="Local path to write the downloaded config file to")
    args = parser.parse_args()

    fetch_config(args.bucket, args.key, args.output)
    print(f"Wrote s3://{args.bucket}/{args.key} to {args.output}")


if __name__ == "__main__":
    main()
