# s3_k3y_unfuck3r.py

Generates S3 keys that are easy to double-click on to get them selected and copied to clipboard.

Change `verify=False` if you need TLS certificate validation.

```sh
usage: s3_k3y_unfuck3r.py [-h] [--mgmt-endpoint MGMT_ENDPOINT] [--tenant-id TENANT_ID]
                          [--username USERNAME] [--password PASSWORD]

Generate StorageGRID S3 credentials until the secret key excludes selected special characters.

options:
  -h, --help            show this help message and exit
  --mgmt-endpoint MGMT_ENDPOINT
                        StorageGRID management endpoint, e.g. 192.168.1.211:443 (default:
                        $SG_MGMT_ENDPOINT)
  --tenant-id TENANT_ID
                        Tenant account ID (default: $SG_TENANT_ID)
  --username USERNAME   Grid or tenant username (default: $SG_USERNAME)
  --password PASSWORD   Grid or tenant password (default: $SG_PASSWORD)
```

Example:

```sh
$ export SG_MGMT_ENDPOINT=192.168.1.211:443
$ export SG_TENANT_ID=26296085394235545212
$ export SG_USERNAME=root
$ export SG_PASSWORD=''

$ python3 s3_k3y_unfuck3r.py
Fucked keys generated on attempt 1. Retrying...
Fucked keys generated on attempt 2. Retrying...
Fucked keys generated on attempt 3. Retrying...
Fucked keys generated on attempt 4. Retrying...
Fucked keys generated on attempt 5. Retrying...
Fucked keys generated on attempt 6. Retrying...
Fucked keys generated on attempt 7. Retrying...
Unfucked Access Key: LIOJFAYPG2O5Y04MMX3I
Unfucked Secret Access Key: j7an9h2QHiGfB1b1ZZmUlOzUGPq52oVajF8OGirN
Attempts: 8 (expected clean-key success rate: 28.1% per try)
```
