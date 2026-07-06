"""
Diagnose MinIO media-storage connectivity and permissions.

Runs every operation the storage backend needs — stat (HEAD), put, get,
presign, delete — against the configured bucket using a throwaway test
object, and reports exactly which one fails and with which S3 error code.

Usage:
    python manage.py check_minio
"""

import io
import uuid

from django.core.files import storage as storage_registry
from django.core.management.base import BaseCommand, CommandError

from minio.error import S3Error

from core.storage import MinioMediaStorage


class Command(BaseCommand):
    help = "Check MinIO media storage: connectivity and per-operation permissions."

    def _step(self, label, fn):
        try:
            result = fn()
        except S3Error as exc:
            self.stdout.write(self.style.ERROR(
                f"  FAIL  {label}: S3 code={exc.code} message={exc.message}"
            ))
            return False, exc
        except Exception as exc:  # noqa: BLE001 — report anything (DNS, TLS, ...)
            self.stdout.write(self.style.ERROR(
                f"  FAIL  {label}: {type(exc).__name__}: {exc}"
            ))
            return False, exc
        self.stdout.write(self.style.SUCCESS(f"  OK    {label}"))
        return True, result

    def handle(self, *args, **options):
        st = storage_registry.storages["default"]
        if not isinstance(st, MinioMediaStorage):
            raise CommandError(
                "Default storage is not MinioMediaStorage "
                f"(got {type(st).__name__}). Set MEDIA_STORAGE=minio in .env."
            )

        scheme = "https" if st.secure else "http"
        self.stdout.write(f"Endpoint : {scheme}://{st.endpoint}")
        self.stdout.write(f"Bucket   : {st.bucket_name}")
        self.stdout.write(f"Region   : {st.region_name}")
        self.stdout.write(f"Presign  : {st.querystring_auth} "
                          f"(expiry {st.url_expiry_seconds}s)")
        self.stdout.write("")

        client = st.client
        key = f"_diagnostics/check-{uuid.uuid4().hex}.txt"
        payload = b"tdx minio diagnostics"

        ok_bucket, res = self._step(
            "bucket_exists (needs s3:ListBucket or admin)",
            lambda: client.bucket_exists(st.bucket_name),
        )
        if ok_bucket and res is False:
            self.stdout.write(self.style.WARNING(
                f"        bucket '{st.bucket_name}' does not exist — create it "
                "or set MINIO_AUTO_CREATE_BUCKET=True"
            ))

        # HEAD on a missing object: NoSuchKey = healthy; AccessDenied = the
        # key lacks s3:ListBucket (exists() falls back, suffixing disabled).
        def head_missing():
            try:
                client.stat_object(st.bucket_name, key)
            except S3Error as exc:
                if exc.code in ("NoSuchKey", "NoSuchObject"):
                    return "clean-404"
                raise
            return "unexpected-200"

        ok_head, res = self._step(
            "stat missing object (needs s3:ListBucket for a clean 404)",
            head_missing,
        )
        if not ok_head and getattr(res, "code", "") == "AccessDenied":
            self.stdout.write(self.style.WARNING(
                "        -> uploads still work, but duplicate filenames may "
                "overwrite. Grant s3:ListBucket on the bucket to fix."
            ))

        ok_put, _ = self._step(
            "put_object (needs s3:PutObject)",
            lambda: client.put_object(
                st.bucket_name, key, io.BytesIO(payload), len(payload),
                content_type="text/plain",
            ),
        )
        if not ok_put:
            self.stdout.write(self.style.ERROR(
                "\nUploads are broken at PutObject — this is a server-side "
                "policy problem. Attach a readwrite policy for this bucket "
                "to the access key (see command docs/README)."
            ))
            return

        def get_back():
            resp = client.get_object(st.bucket_name, key)
            try:
                assert resp.read() == payload
            finally:
                resp.close()
                resp.release_conn()

        self._step("get_object (needs s3:GetObject)", get_back)
        self._step("stat existing object", lambda: client.stat_object(st.bucket_name, key))
        self._step("presigned URL", lambda: st.url(key))
        self._step("remove_object (needs s3:DeleteObject)",
                   lambda: client.remove_object(st.bucket_name, key))

        self.stdout.write("")
        self.stdout.write("Done. If any step failed with AccessDenied, attach this "
                          "policy to the access key in MinIO:")
        self.stdout.write(f"""
{{
  "Version": "2012-10-17",
  "Statement": [
    {{"Effect": "Allow",
      "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
      "Resource": ["arn:aws:s3:::{st.bucket_name}"]}},
    {{"Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": ["arn:aws:s3:::{st.bucket_name}/*"]}}
  ]
}}""")
