"""Compiles a tailored resume to PDF via Typst and uploads it to Cloudflare
R2. Never raises to its caller — any failure is logged and reported back as
a None url, so a PDF problem never fails a /tailor request."""

import asyncio
import logging
import tempfile
import uuid
from pathlib import Path

import boto3
import typst

from app.core.config import settings
from app.schemas.resume import ResumeTailorOutput
from app.services.resume_pdf_template import build_resume_typst

logger = logging.getLogger(__name__)

_R2_KEY_TEMPLATE = "resumes/{user_id}/{resume_id}.pdf"


async def generate_and_upload_pdf(
    user_id: uuid.UUID,
    resume_id: uuid.UUID,
    tailored: ResumeTailorOutput,
    contact: dict,
    education: list[dict],
    certifications: list[dict],
) -> str | None:
    try:
        pdf_bytes = await asyncio.to_thread(_render_pdf, tailored, contact, education, certifications)
        return await asyncio.to_thread(_upload_to_r2, user_id, resume_id, pdf_bytes)
    except Exception:
        logger.exception("PDF generation/upload failed for resume_id=%s", resume_id)
        return None


def _render_pdf(
    tailored: ResumeTailorOutput, contact: dict, education: list[dict], certifications: list[dict]
) -> bytes:
    source = build_resume_typst(tailored, contact, education, certifications)
    with tempfile.TemporaryDirectory() as tmpdir:
        typ_path = Path(tmpdir) / "resume.typ"
        typ_path.write_text(source, encoding="utf-8")
        return typst.compile(str(typ_path))


def _r2_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
    )


def _upload_to_r2(user_id: uuid.UUID, resume_id: uuid.UUID, pdf_bytes: bytes) -> str:
    key = _R2_KEY_TEMPLATE.format(user_id=user_id, resume_id=resume_id)
    _r2_client().put_object(
        Bucket=settings.r2_bucket_name, Key=key, Body=pdf_bytes, ContentType="application/pdf"
    )
    return f"{settings.r2_public_url_base.rstrip('/')}/{key}"
