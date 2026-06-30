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
from datetime import datetime, timedelta, timezone
from getpass import getpass
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
        help=f"Grid or tenant password (default: ${ENV_PREFIX}PASSWORD, otherwise prompt)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Key lifetime in days from now, in UTC (default: 30)",
    )
    parser.add_argument(
        "--no-delete-rejected",
        action="store_true",
        help="Do not delete rejected keys that contain blocked characters",
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
    if args.days < 0:
        missing.append("--days must be 0 or greater")

    if missing:
        raise ValueError("missing required configuration: " + ", ".join(missing))


def resolve_password(args):
    if args.password:
        return args.password

    password = getpass("StorageGRID password: ")
    if not password:
        raise ValueError("missing required configuration: --password, SG_PASSWORD, or interactive input")

    return password


def format_expiry(days):
    expires_at = datetime.now(timezone.utc) + timedelta(days=days)
    return expires_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")


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


def create_s3_key_pair(session, mgmt_endpoint, headers, expires_at):
    api_url = f"https://{mgmt_endpoint}/api/v4/org/users/current-user/s3-access-keys"
    try:
        s3_key_response = session.post(
            api_url,
            headers=headers,
            json={"expires": expires_at},
            verify=False,
            timeout=30,
        )
        s3_key_response.raise_for_status()
        s3_key_data = s3_key_response.json().get("data")
    except requests.RequestException as exc:
        raise RuntimeError(f"S3 key creation request failed: {exc}") from exc
    except ValueError as exc:
        raise RuntimeError("S3 key creation response was not valid JSON") from exc

    if not s3_key_data:
        raise RuntimeError("S3 key creation response did not include key data")

    key_id = s3_key_data.get("id")
    access_key = s3_key_data.get("accessKey")
    secret_access_key = s3_key_data.get("secretAccessKey")
    if not key_id or not access_key or not secret_access_key:
        raise RuntimeError("S3 key creation response was missing id, accessKey, or secretAccessKey")

    return key_id, access_key, secret_access_key


def delete_s3_key_pair(session, mgmt_endpoint, headers, key_id):
    api_url = f"https://{mgmt_endpoint}/api/v4/org/users/current-user/s3-access-keys/{key_id}"
    try:
        delete_response = session.delete(api_url, headers=headers, verify=False, timeout=30)
        delete_response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"S3 key deletion request failed for rejected key {key_id}: {exc}") from exc


def is_unfucked(access_key, secret_access_key):
    return not any(char in access_key for char in ELIMINATION_CRITERIA) and not any(
        char in secret_access_key for char in ELIMINATION_CRITERIA
    )


def main():
    args = parse_args()
    validate_args(args)
    password = resolve_password(args)
    expires_at = format_expiry(args.days)

    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    session = requests.Session()
    bearer_token = get_bearer_token(
        session,
        args.mgmt_endpoint,
        args.tenant_id,
        args.username,
        password,
    )
    headers = {"Authorization": "Bearer " + bearer_token, "Content-Type": "application/json"}

    attempt_count = 0
    success_probability = (62 / 64) ** 40

    while True:
        attempt_count += 1
        key_id, access_key, secret_access_key = create_s3_key_pair(
            session,
            args.mgmt_endpoint,
            headers,
            expires_at,
        )

        if is_unfucked(access_key, secret_access_key):
            print(f"Unfucked Access Key: {access_key}")
            print(f"Unfucked Secret Access Key: {secret_access_key}")
            print(f"Expires: {expires_at}")
            print(
                f"Attempts: {attempt_count} (expected clean-key success rate: {success_probability:.1%} per try)"
            )
            return 0

        if args.no_delete_rejected:
            print(f"Fucked keys generated on attempt {attempt_count}. Keeping rejected key and retrying...")
            continue

        try:
            delete_s3_key_pair(session, args.mgmt_endpoint, headers, key_id)
            print(f"Fucked keys generated on attempt {attempt_count}. Deleted rejected key and retrying...")
        except RuntimeError as exc:
            print(f"Warning: delete of fucked S3 key failed ({exc}). Continuing...", file=sys.stderr)
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

