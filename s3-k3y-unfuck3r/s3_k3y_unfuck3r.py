#!/usr/bin/env python

# SYNOPSIS
# This script obtains unfucked tenant Access Key and Secret Access Key 
# Unfucked keys are those without special signs 
# Unfucked: 8JZ7VXF3FPWI4V8YIBP5, sAE1y_UBRXPmZBGAcsCtnWeUUtW7UI0wp5AFAhkc
# Fucked: sAE1y+UBRXPmZBGAcsCtnWeUUtW7UI0wp5AFAhkc
# TLDR; the purpose is to enable double-clicking on the keys in a terminal window without selecting or defining extra characters in XTerm properties
# (c) scaleoutSean, 2026
# License: MIT License 

import argparse
import os
import sys
import requests

ELIMINATION_CRITERIA = ["+", "/"]

ENV_PREFIX = "SG_"

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate StorageGRID S3 credentials until the secret key excludes selected special characters."
    )
    parser.add_argument(
        "--mgmt-endpoint",
        default=os.getenv(f"{ENV_PREFIX}MGMT_ENDPOINT"),
        help=f"StorageGRID management endpoint, e.g. 192.168.1.211:443 (default: ${ENV_PREFIX}MGMT_ENDPOINT)",
    )
    parser.add_argument(
        "--tenant-id",
        default=os.getenv(f"{ENV_PREFIX}TENANT_ID"),
        help=f"Tenant account ID (default: ${ENV_PREFIX}TENANT_ID)",
    )
    parser.add_argument(
        "--username",
        default=os.getenv(f"{ENV_PREFIX}USERNAME"),
        help=f"Grid or tenant username (default: ${ENV_PREFIX}USERNAME)",
    )
    parser.add_argument(
        "--password",
        default=os.getenv(f"{ENV_PREFIX}PASSWORD"),
        help=f"Grid or tenant password (default: ${ENV_PREFIX}PASSWORD)",
    )
    return parser.parse_args()


def validate_args(args):
    missing = []
    if not args.mgmt_endpoint:
        missing.append("--mgmt-endpoint or SG_MGMT_ENDPOINT")
    if not args.tenant_id:
        missing.append("--tenant-id or SG_TENANT_ID")
    if not args.username:
        missing.append("--username or SG_USERNAME")
    if not args.password:
        missing.append("--password or SG_PASSWORD")

    if missing:
        raise ValueError("missing required configuration: " + ", ".join(missing))


def get_bearer_token(session, mgmt_endpoint, tenant_id, username, password):
    api_url = f"https://{mgmt_endpoint}/api/v4/authorize"
    auth_payload = {
        "accountId": tenant_id,
        "username": username,
        "password": password,
        "cookie": False,
    }
    try:
        auth_response = session.post(api_url, json=auth_payload, verify=False, timeout=30)
        auth_response.raise_for_status()
        bearer_token = auth_response.json().get("data")
    except requests.RequestException as exc:
        raise RuntimeError(f"authentication request failed: {exc}") from exc
    except ValueError as exc:
        raise RuntimeError("authentication response was not valid JSON") from exc

    if not bearer_token:
        raise RuntimeError("authentication response did not include a bearer token")

    return bearer_token


def create_s3_key_pair(session, mgmt_endpoint, headers):
    api_url = f"https://{mgmt_endpoint}/api/v4/org/users/current-user/s3-access-keys"
    try:
        s3_key_response = session.post(api_url, headers=headers, json={"expires": None}, verify=False, timeout=30)
        s3_key_response.raise_for_status()
        s3_key_data = s3_key_response.json().get("data")
    except requests.RequestException as exc:
        raise RuntimeError(f"S3 key creation request failed: {exc}") from exc
    except ValueError as exc:
        raise RuntimeError("S3 key creation response was not valid JSON") from exc

    if not s3_key_data:
        raise RuntimeError("S3 key creation response did not include key data")

    access_key = s3_key_data.get("accessKey")
    secret_access_key = s3_key_data.get("secretAccessKey")
    if not access_key or not secret_access_key:
        raise RuntimeError("S3 key creation response was missing accessKey or secretAccessKey")

    return access_key, secret_access_key


def is_unfucked(access_key, secret_access_key):
    return not any(char in access_key for char in ELIMINATION_CRITERIA) and not any(
        char in secret_access_key for char in ELIMINATION_CRITERIA
    )


def main():
    args = parse_args()
    validate_args(args)

    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    session = requests.Session()
    bearer_token = get_bearer_token(
        session,
        args.mgmt_endpoint,
        args.tenant_id,
        args.username,
        args.password,
    )
    headers = {"Authorization": "Bearer " + bearer_token, "Content-Type": "application/json"}

    attempt_count = 0
    success_probability = (62 / 64) ** 40

    while True:
        attempt_count += 1
        access_key, secret_access_key = create_s3_key_pair(session, args.mgmt_endpoint, headers)

        if is_unfucked(access_key, secret_access_key):
            print(f"Unfucked Access Key: {access_key}")
            print(f"Unfucked Secret Access Key: {secret_access_key}")
            print(
                f"Attempts: {attempt_count} (expected clean-key success rate: {success_probability:.1%} per try)"
            )
            return 0

        print(f"Fucked keys generated on attempt {attempt_count}. Retrying...")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

