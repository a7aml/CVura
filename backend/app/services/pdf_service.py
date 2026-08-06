"""Compiles a tailored resume to PDF via Typst and uploads it to Cloudflare
R2. Never raises to its caller — any failure is logged and reported back as
a None key, so a PDF problem never fails a /tailor request.

The bucket is private: this module never hands out a permanent public URL.
It returns the R2 object key, which callers persist, and a separate
presigned-URL step (generate_presigned_url) turns that key into a
short-lived, time-limited download link on demand."""

import asyncio
import logging
import tempfile
import uuid
from pathlib import Path

import boto3
import typst
from botocore.config import Config

from app.core.config import settings
from app.schemas.resume import ResumeTailorOutput
from app.services.resume_pdf_template import build_resume_typst

logger = logging.getLogger(__name__)

_R2_KEY_TEMPLATE = "resumes/{user_id}/{resume_id}.pdf"

# How long a generated download link stays valid. Short-lived enough that a
# leaked link (referrer header, shared screenshot, browser history) isn't a
# standing exposure, long enough to cover a slow download right after tailoring.
PRESIGNED_URL_EXPIRY_SECONDS = 3600


async def generate_and_upload_pdf(
    user_id: uuid.UUID,
    resume_id: uuid.UUID,
    tailored: ResumeTailorOutput,
    contact: dict,
    education: list[dict],
    certifications: list[dict],
) -> str | None:
    """Returns the uploaded PDF's R2 object key (not a URL) on success, or
    None if generation/upload failed."""
    try:
        pdf_bytes = await asyncio.to_thread(_render_pdf, tailored, contact, education, certifications)
        return await asyncio.to_thread(_upload_to_r2, user_id, resume_id, pdf_bytes)
    except Exception:
        logger.exception("PDF generation/upload failed for resume_id=%s", resume_id)
        return None


def generate_presigned_url(key: str, expires_in: int = PRESIGNED_URL_EXPIRY_SECONDS) -> str:
    return _r2_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.r2_bucket_name, "Key": key},
        ExpiresIn=expires_in,
    )


def _render_pdf(
    tailored: ResumeTailorOutput, contact: dict, education: list[dict], certifications: list[dict]
) -> bytes:
    source = build_resume_typst(tailored, contact, education, certifications)
    with tempfile.TemporaryDirectory() as tmpdir:
        typ_path = Path(tmpdir) / "resume.typ"
        typ_path.write_text(source, encoding="utf-8")
        return typst.compile(str(typ_path))


def _r2_client():
    # boto3 defaults to SigV2 query params (AWSAccessKeyId=...&Signature=...)
    # for a custom endpoint_url unless told otherwise — R2 rejects those
    # outright ("SigV2 authorization is not supported"). Confirmed via a real
    # presigned URL returning that exact error when actually fetched: the
    # /tailor request itself succeeded (upload + DB write are fine), but
    # every download of the resulting link failed. R2 requires SigV4.
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        config=Config(signature_version="s3v4"),
    )


def _upload_to_r2(user_id: uuid.UUID, resume_id: uuid.UUID, pdf_bytes: bytes) -> str:
    key = _R2_KEY_TEMPLATE.format(user_id=user_id, resume_id=resume_id)
    _r2_client().put_object(
        Bucket=settings.r2_bucket_name, Key=key, Body=pdf_bytes, ContentType="application/pdf"
    )
    return key
