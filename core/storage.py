"""
MinIO media storage backend (official MinIO Python SDK).

Replaces the previous django-storages + boto3 stack. All user uploads
(logos, hero images, news/program covers, gallery photos, team photos,
avatars, favicons — every ImageField/FileField) are stored in a MinIO
bucket through this backend.

Design notes
------------
- The MinIO SDK talks plain S3-compatible HTTP: no aws-chunked trailing
  checksums, so the "XAmzContentSHA256Mismatch" problems boto3 >= 1.36
  caused behind buffering reverse proxies (Cloudflare, nginx/CapRover)
  cannot occur here. The AWS_* checksum env-var workarounds are gone.
- MinIO is addressed path-style by nature of the SDK, Signature V4 only.
- Overwrite behaviour mirrors FileSystemStorage: `exists()` is
  implemented, so Django's default `get_available_name()` appends a
  random suffix on name collisions instead of clobbering objects.
- URL strategy (same semantics as the old configuration):
    * `custom_domain` set  -> plain public URL on that domain
                              (bucket may be included in the domain,
                              e.g. "minio.example.com/tdx-media").
    * `querystring_auth`   -> time-limited presigned GET URL; bucket can
      True (default)          stay fully private.
    * `querystring_auth`   -> plain "<endpoint>/<bucket>/<name>" URL;
      False                   requires a public-read bucket policy.
"""

from __future__ import annotations

import logging
import mimetypes
import posixpath
from datetime import timedelta
from urllib.parse import quote, urlsplit

from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)

# S3 error codes that mean "the object is not there".
_NOT_FOUND_CODES = {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}

# S3 error codes for permission failures. A HEAD/GET on a missing object
# surfaces as one of these (403, not 404) when the credential lacks
# s3:ListBucket on the bucket.
_ACCESS_DENIED_CODES = {"AccessDenied", "AllAccessDisabled"}


def _parse_endpoint(endpoint_url: str) -> tuple[str, bool]:
    """
    Split "http(s)://host[:port]" into the (host[:port], secure) pair the
    MinIO SDK expects. Scheme-less values are assumed to be https.
    """
    if not endpoint_url.startswith(("http://", "https://")):
        endpoint_url = f"https://{endpoint_url}"
    parts = urlsplit(endpoint_url)
    if not parts.netloc:
        raise ImproperlyConfigured(
            f"MINIO_ENDPOINT_URL is not a valid URL: {endpoint_url!r}"
        )
    return parts.netloc, parts.scheme == "https"


class MinioFile(File):
    """Lazy read-only file: the object is downloaded on first access."""

    def __init__(self, name: str, storage: "MinioMediaStorage"):
        self.name = name
        self._storage = storage
        self._file = None
        self.mode = "rb"

    def _get_file(self):
        if self._file is None:
            self._file = self._storage._download(self.name)
        return self._file

    def _set_file(self, value):
        self._file = value

    file = property(_get_file, _set_file)

    @property
    def size(self) -> int:
        if self._file is not None:
            return super().size
        return self._storage.size(self.name)

    def close(self):
        if self._file is not None:
            self._file.close()
            self._file = None


@deconstructible
class MinioMediaStorage(Storage):
    """Django Storage implementation backed by the MinIO Python SDK."""

    def __init__(
        self,
        *,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region_name: str = "us-east-1",
        custom_domain: str = "",
        url_protocol: str = "https:",
        querystring_auth: bool = True,
        url_expiry_seconds: int = 3600,
        auto_create_bucket: bool = False,
        default_content_type: str = "application/octet-stream",
        # Multipart chunk size for streams of unknown length (min 5 MiB).
        multipart_part_size: int = 10 * 1024 * 1024,
    ):
        self.endpoint, self.secure = _parse_endpoint(endpoint_url)
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.custom_domain = custom_domain.strip().strip("/")
        self.url_protocol = url_protocol
        self.querystring_auth = querystring_auth
        self.url_expiry_seconds = url_expiry_seconds
        self.auto_create_bucket = auto_create_bucket
        self.default_content_type = default_content_type
        self.multipart_part_size = multipart_part_size

        self._client: Minio | None = None
        self._bucket_checked = False

    # -- client ------------------------------------------------------------

    @property
    def client(self) -> Minio:
        """Lazily construct the SDK client (safe at import/settings time)."""
        if self._client is None:
            self._client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
                region=self.region_name,
            )
        return self._client

    def _ensure_bucket(self) -> None:
        if self._bucket_checked or not self.auto_create_bucket:
            return
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
        self._bucket_checked = True

    # -- name handling -----------------------------------------------------

    def _normalize_name(self, name: str) -> str:
        """
        Collapse the path and forbid traversal outside the bucket root.
        Object keys always use forward slashes.
        """
        name = name.replace("\\", "/")
        cleaned = posixpath.normpath(name).lstrip("/")
        if cleaned in ("", ".") or cleaned.startswith(".."):
            raise ValueError(f"Invalid object name: {name!r}")
        return cleaned

    # -- core storage API --------------------------------------------------

    def _save(self, name: str, content) -> str:
        name = self._normalize_name(name)
        self._ensure_bucket()

        content_type = (
            getattr(content, "content_type", None)
            or mimetypes.guess_type(name)[0]
            or self.default_content_type
        )

        content.seek(0)
        size = getattr(content, "size", None)
        if size is None:
            # Unknown length: let the SDK do multipart streaming.
            length, part_size = -1, self.multipart_part_size
        else:
            length, part_size = size, 0

        self.client.put_object(
            self.bucket_name,
            name,
            data=content,
            length=length,
            part_size=part_size,
            content_type=content_type,
        )
        return name

    def _download(self, name: str):
        import io

        name = self._normalize_name(name)
        response = None
        try:
            response = self.client.get_object(self.bucket_name, name)
            return io.BytesIO(response.read())
        except S3Error as exc:
            if exc.code in _NOT_FOUND_CODES:
                raise FileNotFoundError(f"File does not exist: {name}") from exc
            raise
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    def _open(self, name: str, mode: str = "rb") -> File:
        if "w" in mode or "+" in mode or "a" in mode:
            raise ValueError("MinioMediaStorage only supports read mode ('rb').")
        return MinioFile(self._normalize_name(name), self)

    def delete(self, name: str) -> None:
        name = self._normalize_name(name)
        try:
            self.client.remove_object(self.bucket_name, name)
        except S3Error as exc:  # deleting a missing object is not an error
            if exc.code not in _NOT_FOUND_CODES:
                raise

    def exists(self, name: str) -> bool:
        try:
            self.client.stat_object(self.bucket_name, self._normalize_name(name))
            return True
        except S3Error as exc:
            if exc.code in _NOT_FOUND_CODES:
                return False
            if exc.code in _ACCESS_DENIED_CODES:
                # S3 semantics: a HEAD on a *missing* object returns 403
                # AccessDenied instead of 404 when the credential lacks
                # s3:ListBucket on the bucket. We can't distinguish
                # "missing" from "forbidden" here, so assume missing and
                # let put_object surface a real permission error if the
                # key truly can't write. NOTE: without s3:ListBucket the
                # collision check is blind, so identical filenames may
                # overwrite — grant s3:ListBucket to restore suffixing.
                logger.warning(
                    "MinIO stat_object('%s') returned %s — the access key "
                    "likely lacks s3:ListBucket on bucket '%s'. Treating the "
                    "object as absent; duplicate-name suffixing is disabled "
                    "until the policy is fixed.",
                    name, exc.code, self.bucket_name,
                )
                return False
            raise
        except ValueError:
            return False

    def size(self, name: str) -> int:
        try:
            stat = self.client.stat_object(
                self.bucket_name, self._normalize_name(name)
            )
        except S3Error as exc:
            if exc.code in _NOT_FOUND_CODES:
                raise FileNotFoundError(f"File does not exist: {name}") from exc
            raise
        return stat.size

    def get_modified_time(self, name: str):
        stat = self.client.stat_object(self.bucket_name, self._normalize_name(name))
        return stat.last_modified  # timezone-aware (UTC)

    get_created_time = get_modified_time
    get_accessed_time = get_modified_time

    def listdir(self, path: str = "") -> tuple[list[str], list[str]]:
        prefix = ""
        if path and path not in (".", "/"):
            prefix = self._normalize_name(path) + "/"
        dirs, files = [], []
        for obj in self.client.list_objects(
            self.bucket_name, prefix=prefix, recursive=False
        ):
            rel = obj.object_name[len(prefix):]
            if obj.is_dir:
                dirs.append(rel.rstrip("/"))
            elif rel:
                files.append(rel)
        return dirs, files

    # -- URLs ----------------------------------------------------------------

    def url(self, name: str) -> str:
        name = self._normalize_name(name)

        # Public host explicitly configured for browsers (may already
        # include the bucket, e.g. "minio.example.com/tdx-media").
        if self.custom_domain:
            return f"{self.url_protocol}//{self.custom_domain}/{quote(name)}"

        if self.querystring_auth:
            return self.client.presigned_get_object(
                self.bucket_name,
                name,
                expires=timedelta(seconds=self.url_expiry_seconds),
            )

        scheme = "https" if self.secure else "http"
        return f"{scheme}://{self.endpoint}/{self.bucket_name}/{quote(name)}"
