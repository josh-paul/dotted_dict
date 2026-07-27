"""Replacement for boto2's ``get_instance_metadata``, which boto3 dropped.

Fetches the EC2 instance identity document and returns it as a DottedDict, so
the fields are reachable as attributes without declaring a model for a
document AWS owns and can extend.

Run on an EC2 instance::

    >>> instance = get_instance_metadata()
    >>> instance.availability_zone
    'us-east-1c'
    >>> instance.instance_type
    't2.micro'

Uses IMDSv2 (token-authenticated) and falls back to IMDSv1, because instances
launched with ``HttpTokens=required`` reject unauthenticated reads. Standard
library only, so the example carries no dependency the package does not.
"""

import json
import re
import urllib.error
import urllib.request

from dotted_dict import DottedDict

METADATA_HOST = "http://169.254.169.254"
IDENTITY_PATH = "/latest/dynamic/instance-identity/document"
TOKEN_PATH = "/latest/api/token"
TOKEN_TTL_SECONDS = 21600
TIMEOUT_SECONDS = 2

_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


def get_instance_metadata(timeout=TIMEOUT_SECONDS):
    """Return the instance identity document as a DottedDict.

    Args:
        timeout: Seconds to wait for the metadata service. Kept short because
            off an EC2 instance the address is unroutable and the call should
            fail quickly rather than hang.

    Returns:
        DottedDict: The identity document, keys converted from camelCase to
        snake_case.

    Raises:
        urllib.error.URLError: If the metadata service is unreachable, which
            is what you get when this is not run on an EC2 instance.
    """
    headers = {}
    token = _get_imds_token(timeout)
    if token:
        headers["X-aws-ec2-metadata-token"] = token

    request = urllib.request.Request(METADATA_HOST + IDENTITY_PATH, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        document = json.loads(response.read().decode("utf-8"))

    return DottedDict({uncamel(key): value for key, value in document.items()})


def _get_imds_token(timeout):
    """Request an IMDSv2 token.

    Returns:
        str or None: The token, or None when the service only speaks v1, in
        which case the caller proceeds without one.
    """
    request = urllib.request.Request(
        METADATA_HOST + TOKEN_PATH,
        method="PUT",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": str(TOKEN_TTL_SECONDS)},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except urllib.error.URLError:
        return None


def uncamel(name):
    """Convert a camelCase or PascalCase name to snake_case.

    Args:
        name: The key as AWS supplies it, such as ``availabilityZone``.

    Returns:
        str: The snake_case form, such as ``availability_zone``. A leading
        capital does not produce a leading underscore.
    """
    return _CAMEL_BOUNDARY.sub("_", name).lower()


if __name__ == "__main__":
    try:
        print(json.dumps(get_instance_metadata().to_dict(), indent=2, sort_keys=True))
    except urllib.error.URLError as error:
        raise SystemExit(f"metadata service unreachable (not on EC2?): {error}") from error
