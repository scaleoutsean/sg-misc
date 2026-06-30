# s3_k3y_unfuck3r.py

Generates S3 keys that are easy to double-click on to get them selected and copied to clipboard.

Rejected S3 key sets are deleted automatically by default.

**Security tips:**

- s3_k3y_unfuck3r falls back to `getpass()` (recommended) when `--password` is omitted and `SG_PASSWORD` is unset
- Using env vars is safer than passing `--password` directly in process args
- Unset `SG_PASSWORD` and close the terminal tab after use
- Change `verify=False` if you need TLS certificate validation.

```sh
usage: s3_k3y_unfuck3r.py [-h] [--mgmt-endpoint MGMT_ENDPOINT] [--tenant-id TENANT_ID]
                          [--username USERNAME] [--password PASSWORD] [--days DAYS]
                          [--no-delete-rejected]

Generate StorageGRID S3 credentials until the secret key excludes selected special characters.

options:
  -h, --help            show this help message and exit
  --mgmt-endpoint MGMT_ENDPOINT
                        StorageGRID management endpoint, e.g. 192.168.1.211:443 (default:
                        $SG_MGMT_ENDPOINT)
  --tenant-id TENANT_ID
                        Tenant account ID (default: $SG_TENANT_ID)
  --username USERNAME   Grid or tenant username (default: $SG_USERNAME)
  --password PASSWORD   Grid or tenant password (default: $SG_PASSWORD,
                        otherwise prompt)
  --days DAYS           Key lifetime in days from now, in UTC (default: 30)
  --no-delete-rejected  Do not delete rejected keys that contain blocked
                        characters
```

Example:

```sh
$ export SG_MGMT_ENDPOINT=192.168.1.211:443
$ export SG_TENANT_ID=26296085394235545212
$ export SG_USERNAME=root
$ unset SG_PASSWORD

$ python3 s3_k3y_unfuck3r.py --days 7
StorageGRID password:
Fucked keys generated on attempt 1. Deleted rejected key and retrying...
Fucked keys generated on attempt 2. Deleted rejected key and retrying...
Fucked keys generated on attempt 3. Deleted rejected key and retrying...
Fucked keys generated on attempt 4. Deleted rejected key and retrying...
Fucked keys generated on attempt 5. Deleted rejected key and retrying...
Fucked keys generated on attempt 6. Deleted rejected key and retrying...
Fucked keys generated on attempt 7. Deleted rejected key and retrying...
Unfucked Access Key: LIOJFAYPG2O5Y04MMX3I
Unfucked Secret Access Key: j7an9h2QHiGfB1b1ZZmUlOzUGPq52oVajF8OGirN
Expires: 2026-07-07T11:11:11.000Z
Attempts: 8 (expected clean-key success rate: 28.1% per try)
```

If delete of a rejected key fails, the script logs a warning and continues generating new keys.
